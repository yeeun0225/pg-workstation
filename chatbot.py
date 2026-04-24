import streamlit as st
import anthropic
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from utils.auth import ROLE_ICON

load_dotenv(Path(__file__).parent / ".env", override=True)

DATA      = Path(__file__).parent / "data"
FILES_DIR = DATA / "files"

FAQ_QUICK = [
    "가맹점 정산주기는 어떻게 확인하나요?",
    "가맹점 수수료율은 어떻게 확인하나요?",
    "매핑SET의 카드사별 가맹점번호는 어떻게 확인하나요?",
    "고객 무이자 미적용 민원 이유가 뭘까요?",
    "카드사 업종 무이자 정책은 어떻게 확인하나요?",
    "신용카드 매출전표 표기명을 변경할 수 있나요?",
    "거래건 분담무이자 적용 거래건은 어디서 조회하나요?",
    "세금계산서 공급가액 및 세액은 어디서 확인하나요?",
    "PG정산 대금은 어디서 조회하나요?",
    "정산예정금액과 실제 입금금액이 다른 이유는?",
    "역환(이월)금액은 어떻게 없애나요?",
    "내부관리자 메뉴가 안보여요",
]

def load_faq():
    p = DATA / "faq.txt"
    return p.read_text(encoding="utf-8") if p.exists() else ""

def load_rar():
    p = DATA / "rar.json"
    if not p.exists(): return ""
    rows = json.loads(p.read_text(encoding="utf-8"))
    lines = ["[R&R 담당 부서 테이블]"]
    for r in rows:
        contact = f" ({r['연락처']})" if r.get("연락처") else ""
        lines.append(f"- {r['업무']}: {r['부서']} / {r.get('담당자','미지정')}{contact}")
    return "\n".join(lines)

def list_files():
    if not FILES_DIR.exists(): return []
    return [{"name": f.name, "path": f}
            for f in sorted(FILES_DIR.iterdir())
            if f.is_file() and not f.name.startswith(".")]

def build_system_prompt(role):
    faq = load_faq()
    rar = load_rar()
    files = list_files()
    file_names = "\n".join(f"- {f['name']}" for f in files) or "등록된 파일 없음"
    role_ctx = (
        "현재 사용자는 PG사업지원팀 소속입니다. 모든 정보에 접근 가능합니다."
        if role == "PG사업지원팀"
        else "현재 사용자는 영업팀 소속입니다. FAQ, R&R 안내, 파일 안내만 제공하세요."
    )
    return f"""당신은 PG사 가맹점 관리팀 전용 AI 워크스테이션 챗봇입니다.
{role_ctx}

■ 답변 원칙
- 아래 FAQ에 등록된 답변 내용을 절대 요약하거나 생략하지 마세요. FAQ의 A: 내용을 빠짐없이 전부 출력하세요.
- FAQ에 없는 내용을 임의로 추가하거나 지어내지 마세요. 등록된 내용만 답변하세요.
- 등록된 정보에 없는 내용은 "해당 내용은 등록된 정보에 없습니다. 담당 부서에 직접 문의해 주세요."라고만 안내하세요.
- 답변 형식은 읽기 좋게 구조화하되(줄바꿈, bullet 등), 내용은 FAQ 원문 그대로 유지하세요.
- 제목/소제목은 **굵게** 처리하고 h1·h2 등 큰 헤더는 사용하지 마세요.

{'='*60}
{faq if faq else '※ FAQ 문서가 아직 등록되지 않았습니다.'}
{'='*60}
{rar if rar else '※ R&R 테이블이 아직 등록되지 않았습니다.'}
{'='*60}
[다운로드 가능한 파일 목록]
{file_names}
{'='*60}"""

def ask_claude(history, role):
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key or api_key == "your-api-key-here":
        return "⚠️ ANTHROPIC_API_KEY가 설정되지 않았습니다."
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=build_system_prompt(role),
        messages=history,
    )
    return response.content[0].text

# ── 사이드바 ───────────────────────────────────────────
with st.sidebar:
    st.markdown("---")
    icon = ROLE_ICON.get(st.session_state.get("role", ""), "")
    st.markdown(f"**{icon} {st.session_state.get('role','')}** 접속 중")

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
            st.download_button(
                label=f["name"], data=f["path"].read_bytes(),
                file_name=f["name"], key=f"dl_{f['name']}",
                use_container_width=True,
            )

    st.markdown("---")
    if st.button("대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    if st.button("로그아웃", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

# ── 챗봇 UI ────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] textarea::placeholder {
    font-family: 'Noto Sans KR', sans-serif !important;
    font-size: 13px !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("## 💬 챗봇")
st.caption("FAQ · R&R · 파일 안내 | 질문을 입력하거나 왼쪽 버튼을 클릭하세요.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    avatar = "❓" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

triggered_q = st.session_state.pop("faq_trigger", None) if "faq_trigger" in st.session_state else None
user_input  = st.chat_input("질문을 입력하세요...") or triggered_q

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="❓"):
        st.markdown(user_input)
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("답변 생성 중..."):
            answer = ask_claude(
                [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                st.session_state.get("role", "PG사업지원팀"),
            )
        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()
