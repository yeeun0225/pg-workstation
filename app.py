import streamlit as st
from utils.auth import COMMON_CSS, USERS

st.set_page_config(
    page_title="PG 가맹점 AI 워크스테이션",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(COMMON_CSS, unsafe_allow_html=True)

# ── 로그인 ─────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.update({"logged_in": False, "role": None, "messages": []})

if not st.session_state.logged_in:
    _, col, _ = st.columns([1.5, 2, 1.5])
    with col:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("# ⚡ PG 가맹점\nAI 워크스테이션")
        st.markdown("---")
        role = st.selectbox("소속 팀", list(USERS.keys()))
        pw = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
        if st.button("로그인", use_container_width=True, type="primary"):
            if pw == USERS.get(role, ""):
                st.session_state.update({"logged_in": True, "role": role, "messages": []})
                st.rerun()
            else:
                st.error("비밀번호가 올바르지 않습니다.")
    st.stop()

# ── 페이지 네비게이션 ───────────────────────────────────
pg = st.navigation([
    st.Page("home.py",    title="홈",    icon="🏠", default=True),
    st.Page("chatbot.py", title="챗봇",  icon="💬"),
    st.Page("issues.py",  title="이슈",  icon="📋"),
])
pg.run()
