import streamlit as st
import anthropic
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from utils.auth import require_login, sidebar_common, COMMON_CSS

load_dotenv()

# ── 페이지 설정 ────────────────────────────────────────
st.set_page_config(
    page_title="챗봇 — PG 워크스테이션",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(COMMON_CSS, unsafe_allow_html=True)

require_login()
sidebar_common()

# ── 경로 ──────────────────────────────────────────────
DATA = Path(__file__).parent.parent / "data"
FILES_DIR = DATA / "files"

# ── 원클릭 FAQ 버튼 ────────────────────────────────────
FAQ_QUICK = [
    "정산 주기가 어떻게 되나요?",
    "가맹점 수수료율은 어떻게 확인하나요?",
    "연동 오류 발생 시 어떻게 처리하나요?",
    "신규 가맹점 등록 절차가 어떻게 되나요?",
    "담당자 변경은 어디에 요청하나요?",
    "정산 지연 시 처리 방법은?",
    "민원 처리 절차는 어떻게 되나요?",
    "API 문서는 어디서 받을 수 있나요?",
]

# ── 데이터 로더 ────────────────────────────────────────
def load_faq() -> str:
    path = DATA / "faq.txt"
    return path.read_text(encoding="utf-8") if path.exists() else ""

def load_rar() -> str:
    path = DATA / "rar.json"
    if not path.exists():
        return ""
    rows = json.loads(path.read_text(encoding="utf-8"))
    lines = ["[R&R 담당 부서 테이블]"]
    for r in rows:
        contact = f" ({r['연락처']})" if r.get("연락처") else ""
        lines.append(f"- {r['업무']}: {r['부서']} / {r.get('담당자','미지정')}{contact}")
    return "\n".join(lines)

def list_files() -> list[dict]:
    if not FILES_DIR.exists():
        return []
    return [
        {"name": f.name, "path": f}
        for f in sorted(FILES_DIR.iterdir())
        if f.is_file() and not f.name.startswith(".")
    ]

# ── 시스템 프롬프트 ────────────────────────────────────
def build_system_prompt(role: str) -> str:
    faq = load_faq()
    rar = load_rar()
    files = list_files()
    file_names = "\n".join(f"- {f['name']}" for f in files) or "등록된 파일 없음"

    role_ctx = (
        "현재 사용자는 가맹점 관리팀 소속입니다. 모든 정보에 접근 가능합니다."
        if role == "관리팀"
        else "현재 사용자는 영업팀 소속입니다. FAQ, R&R 안내, 파일 안내만 제공하세요. 내부 운영 데이터는 공유하지 마세요."
    )

    return f"""당신은 PG사 가맹점 관리팀 전용 AI 워크스테이션 챗봇입니다.
{role_ctx}

■ 답변 원칙
- 아래 제공된 FAQ, R&R, 파일 목록에 있는 정보만으로 답변하세요.
- 등록된 정보에 없는 내용은 "해당 내용은 등록된 정보에 없습니다. 담당 부서에 직접 문의해 주세요."라고 안내하세요.
- 답변은 간결하고 실용적으로 작성하세요. 불필요한 서론은 생략하세요.
- 담당자/부서 안내 시 R&R 테이블을 우선 참조하세요.

{'='*60}
{faq if faq else '※ FAQ 문서가 아직 등록되지 않았습니다.'}

{'='*60}
{rar if rar else '※ R&R 테이블이 아직 등록되지 않았습니다.'}

{'='*60}
[다운로드 가능한 파일 목록]
{file_names}
{'='*60}

파일 요청 시: 정확한 파일명을 안내해 주세요. 실제 다운로드는 사이드바에서 가능합니다."""

# ── Claude API ─────────────────────────────────────────
def ask_claude(history: list[dict], role: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key or api_key == "your-api-key-here":
        return "⚠️ ANTHROPIC_API_KEY가 설정되지 않았습니다. `.env` 파일에 API 키를 입력해 주세요."
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=build_system_prompt(role),
        messages=history,
    )
    return response.content[0].text

# ── 사이드바 — FAQ 버튼 + 파일 다운로드 ──────────────────
with st.sidebar:
    st.markdown("**💡 자주 묻는 질문**")
    for q in FAQ_QUICK:
        if st.button(q, key=f"faq_{q}"):
            st.session_state.faq_trigger = q
            st.rerun()

    files = list_files()
    if files:
        st.markdown("---")
        st.markdown("**📁 파일 다운로드**")
        for f in files:
            data = f["path"].read_bytes()
            st.download_button(
                label=f["name"],
                data=data,
                file_name=f["name"],
                key=f"dl_{f['name']}",
                use_container_width=True,
            )

    st.markdown("---")
    if st.button("대화 초기화", use_container_width=True, key="clear_chat"):
        st.session_state.messages = []
        st.rerun()

# ── 챗봇 메인 ──────────────────────────────────────────
st.markdown("## 💬 챗봇")
st.caption("FAQ · R&R · 파일 안내 | 질문을 입력하거나 왼쪽 버튼을 클릭하세요.")

if "messages" not in st.session_state:
    st.session_state.messages = []

# 대화 이력
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# FAQ 버튼 트리거
triggered_q = st.session_state.pop("faq_trigger", None) if "faq_trigger" in st.session_state else None

user_input = st.chat_input("질문을 입력하세요...") or triggered_q

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("답변 생성 중..."):
            history = [{"role": m["role"], "content": m["content"]}
                       for m in st.session_state.messages]
            answer = ask_claude(history, st.session_state.role)
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()
