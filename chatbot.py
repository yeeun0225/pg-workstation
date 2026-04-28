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

CAT_ICON = {"계약정보": "📄", "내부셋팅": "⚙️", "결제": "💳", "정산": "💰"}

# ── 데이터 로드 ─────────────────────────────────────────
def load_faq_structured():
    p = DATA / "faq.txt"
    if not p.exists(): return {}
    text = p.read_text(encoding="utf-8")
    result = {}
    current_cat, current_q, current_a_lines, in_answer = None, None, [], False

    def save_qa():
        nonlocal current_q, current_a_lines, in_answer
        if current_q and current_cat is not None:
            result.setdefault(current_cat, []).append({
                "q": current_q, "a": "\n".join(current_a_lines).strip()
            })
            current_q = None; current_a_lines = []; in_answer = False

    for line in text.splitlines():
        s = line.strip()
        if s.startswith('[') and s.endswith(']') and '=' not in s:
            save_qa(); current_cat = s[1:-1]
        elif s.startswith('Q: '):
            save_qa(); current_q = s[3:]; in_answer = False
        elif s.startswith('A: '):
            in_answer = True; current_a_lines = [s[3:]]
        elif in_answer and not s.startswith('==='):
            current_a_lines.append(line)
    save_qa()
    return result

def load_faq_raw():
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
    faq = load_faq_raw()
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
        st.session_state.chat_messages = []
        st.rerun()
    if st.button("로그아웃", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

# ── Session State ────────────────────────────────────────
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "expanded_qs" not in st.session_state:
    st.session_state.expanded_qs = set()

faq_data   = load_faq_structured()
categories = list(faq_data.keys())
if "selected_cat" not in st.session_state or st.session_state.selected_cat not in categories:
    st.session_state.selected_cat = categories[0] if categories else None

# ── 스타일 ──────────────────────────────────────────────
st.markdown("""
<style>
/* FAQ 질문 버튼 */
div[data-faq-btn] button {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 10px !important;
    padding: 14px 18px !important;
    text-align: left !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    color: #1E293B !important;
    width: 100% !important;
    margin-bottom: 2px !important;
    justify-content: flex-start !important;
}
div[data-faq-btn] button:hover {
    border-color: #2563EB !important;
    color: #2563EB !important;
    background: #F8FBFF !important;
}
/* FAQ 답변 박스 */
.faq-answer {
    background: #F8FAFC;
    border: 1px solid #DBEAFE;
    border-radius: 0 0 10px 10px;
    padding: 14px 20px;
    font-size: 13px;
    color: #334155;
    white-space: pre-line;
    line-height: 1.8;
    margin-top: -4px;
    margin-bottom: 8px;
}
/* 카테고리 버튼 */
div[data-cat-btn] button {
    background: transparent !important;
    border: none !important;
    color: #64748B !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    text-align: left !important;
    padding: 9px 14px !important;
    border-radius: 8px !important;
    width: 100% !important;
    justify-content: flex-start !important;
}
div[data-cat-btn] button:hover {
    background: #EFF6FF !important;
    color: #2563EB !important;
}
[data-testid="stChatInput"] textarea {
    font-size: 13px !important;
}
</style>
""", unsafe_allow_html=True)

# ── 탭 ──────────────────────────────────────────────────
st.markdown("## 💬 챗봇")
tab_chat, tab_faq = st.tabs(["💬  챗봇", "❓  자주 묻는 질문"])

# ════════════════════════════════════════════════════════
# 탭 1 — 챗봇
# ════════════════════════════════════════════════════════
with tab_chat:
    st.caption("질문을 입력하면 AI가 FAQ 기반으로 답변해드립니다.")

    for msg in st.session_state.chat_messages:
        avatar = "❓" if msg["role"] == "user" else "🤖"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    user_input = st.chat_input("질문을 입력하세요...")

    if user_input:
        st.session_state.chat_messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="❓"):
            st.markdown(user_input)
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("답변 생성 중..."):
                answer = ask_claude(
                    [{"role": m["role"], "content": m["content"]}
                     for m in st.session_state.chat_messages],
                    st.session_state.get("role", "PG사업지원팀"),
                )
            st.markdown(answer)
        st.session_state.chat_messages.append({"role": "assistant", "content": answer})
        st.rerun()

# ════════════════════════════════════════════════════════
# 탭 2 — FAQ
# ════════════════════════════════════════════════════════
with tab_faq:
    st.caption("카테고리를 선택하거나 검색어를 입력하세요.")

    search_q = st.text_input("", placeholder="🔍   무엇이든 찾아보세요", label_visibility="collapsed", key="faq_search")
    st.markdown("<br>", unsafe_allow_html=True)

    col_cat, col_main = st.columns([2, 8])

    with col_cat:
        st.markdown("**카테고리**")
        st.markdown("<br>", unsafe_allow_html=True)
        for cat in categories:
            ico = CAT_ICON.get(cat, "📌")
            is_active = st.session_state.selected_cat == cat
            label = f"**{ico} {cat}**" if is_active else f"{ico} {cat}"
            st.markdown('<div data-cat-btn="1">', unsafe_allow_html=True)
            if st.button(label, key=f"cat_{cat}", use_container_width=True):
                st.session_state.selected_cat = cat
                st.session_state.expanded_qs = set()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    with col_main:
        if search_q:
            items = []
            for cat, qa_list in faq_data.items():
                for i, qa in enumerate(qa_list):
                    if search_q.lower() in qa["q"].lower() or search_q.lower() in qa["a"].lower():
                        items.append((cat, i, qa))
            if not items:
                st.info("검색 결과가 없습니다.")
        else:
            selected = st.session_state.selected_cat
            items = [(selected, i, qa) for i, qa in enumerate(faq_data.get(selected, []))]

        for cat, i, qa in items:
            q_key = f"faq_{cat}_{i}"
            is_exp = q_key in st.session_state.expanded_qs
            arrow  = "▲" if is_exp else "▼"

            st.markdown('<div data-faq-btn="1">', unsafe_allow_html=True)
            if st.button(f"Q.  {qa['q']}　{arrow}", key=q_key, use_container_width=True):
                if is_exp:
                    st.session_state.expanded_qs.discard(q_key)
                else:
                    st.session_state.expanded_qs.add(q_key)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

            if is_exp:
                st.markdown(f'<div class="faq-answer">{qa["a"]}</div>', unsafe_allow_html=True)
