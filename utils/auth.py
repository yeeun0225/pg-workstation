import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

USERS = {
    "PG사업지원팀": os.getenv("ADMIN_PASSWORD", "admin123"),
    "영업팀": os.getenv("SALES_PASSWORD", "sales123"),
}

ROLE_ICON = {"PG사업지원팀": "🔵", "영업팀": "🟢"}

COMMON_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap');

* { font-family: 'Noto Sans KR', sans-serif !important; }
p, li, label { font-size: 13px !important; }
/* SVG title/desc 완전 숨기기 */
svg title, svg desc {
    display: none !important;
    visibility: hidden !important;
    position: absolute !important;
    width: 0 !important;
    height: 0 !important;
    overflow: hidden !important;
    clip: rect(0,0,0,0) !important;
    font-size: 0 !important;
    color: transparent !important;
}
/* expander 버튼 내 sr-only 텍스트 */
[data-testid="stExpanderToggleIcon"] span:not(:has(svg)),
details summary span:not(:has(svg)),
[data-testid="stExpander"] summary span:not(:has(svg)) {
    display: none !important;
    font-size: 0 !important;
}
/* 사이드바 접기/펼치기 버튼 sr-only 텍스트 숨기기 (SVG 포함 span은 제외) */
[data-testid="stSidebarCollapseButton"] span:not(:has(svg)),
[data-testid="stSidebarCollapsedControl"] span:not(:has(svg)),
[data-testid="stBaseButton-header"] span:not(:has(svg)),
[data-testid="stSidebarContent"] ~ * span:not(:has(svg)),
header [data-testid] span:not(:has(svg)) {
    display: none !important;
    font-size: 0 !important;
    width: 0 !important;
    height: 0 !important;
    overflow: hidden !important;
    position: absolute !important;
    clip: rect(0,0,0,0) !important;
}
[data-testid="stChatMessage"] p { font-size: 13px !important; }
/* 아바타 크기 보호 — div 전체 override 제거 */
[data-testid="stChatMessageAvatarUser"],
[data-testid="stChatMessageAvatarAssistant"] {
    font-size: 26px !important;
    min-width: 2rem !important;
    width: 2rem !important;
    height: 2rem !important;
}

/* ── 전체 배경 ── */
.stApp, .main, [data-testid="stAppViewContainer"] {
    background-color: #F8FAFC !important;
}
/* ── 사이드바 ── */
[data-testid="stSidebar"] {
    background-color: #1E40AF !important;
    border-right: none;
}
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] a {
    color: #DBEAFE !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #FFFFFF !important;
}
/* ── 본문 텍스트 ── */
h1 { color: #1E293B !important; font-size: 2.5rem !important; }
h2 { color: #1E293B !important; font-size: 2.0rem !important; }
h3 { color: #1E293B !important; font-size: 1.5rem !important; }
p, li { color: #334155; }
hr { border-color: #E2E8F0 !important; }
.stCaption { color: #94A3B8 !important; }
/* ── 채팅 메시지 ── */
[data-testid="stChatMessage"] {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    margin-bottom: 8px;
}
[data-testid="stChatInputTextArea"] {
    background: #FFFFFF !important;
    color: #1E293B !important;
    border: 1px solid #CBD5E1 !important;
}
/* ── 사이드바 버튼 ── */
[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.12) !important;
    border: 1px solid rgba(255,255,255,0.25) !important;
    color: #FFFFFF !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    width: 100%;
    white-space: normal !important;
    height: auto !important;
    text-align: left !important;
    padding: 7px 12px !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.25) !important;
    border-color: rgba(255,255,255,0.5) !important;
}
/* ── 메인 primary 버튼 ── */
.main .stButton > button[kind="primary"],
button[kind="primary"] {
    background: #2563EB !important;
    border: none !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
}
button[kind="primary"]:hover {
    background: #1D4ED8 !important;
}
/* ── 입력 필드 ── */
[data-testid="stSelectbox"] > div > div,
[data-testid="stTextInput"] > div > div > input {
    background: #FFFFFF !important;
    border-color: #CBD5E1 !important;
    color: #1E293B !important;
}
</style>
<script>
(function() {
    var KEYWORDS = ['arrow', 'keyboard', 'upload', 'file', 'double', 'right', 'left', 'collapse', 'expand'];
    function hideEl(el) {
        el.style.cssText += 'display:none!important;font-size:0!important;width:0!important;height:0!important;overflow:hidden!important;position:absolute!important;clip:rect(0,0,0,0)!important;';
    }
    function clean() {
        // SVG title 태그 전부 제거
        document.querySelectorAll('svg title, svg desc').forEach(function(el) { el.remove(); });
        // 사이드바 접기 버튼 내 span 직접 숨기기
        var selectors = [
            '[data-testid="stSidebarCollapseButton"] span',
            '[data-testid="stSidebarCollapsedControl"] span',
            '[data-testid="stBaseButton-header"] span',
            '[data-testid="collapsedControl"] span',
            'button[aria-label*="sidebar"] span',
            'section[data-testid="stSidebarUserContent"] ~ * span'
        ];
        selectors.forEach(function(sel) {
            document.querySelectorAll(sel).forEach(function(el) {
                // SVG를 포함한 span은 건드리지 않음
                if (!el.querySelector('svg') && !el.closest('svg')) { hideEl(el); }
            });
        });
        // 텍스트만 있는 노드 중 키워드 포함된 것 숨기기
        document.querySelectorAll('*').forEach(function(el) {
            if (el.childElementCount === 0) {
                var t = (el.textContent || '').trim().toLowerCase();
                if (t.length > 0 && t.length < 60 && KEYWORDS.some(function(k){ return t.indexOf(k) !== -1; })) {
                    hideEl(el);
                }
            }
        });
    }
    clean();
    [300, 800, 2000].forEach(function(d){ setTimeout(clean, d); });
    new MutationObserver(function(){ clean(); }).observe(document.documentElement, {childList:true, subtree:true});
})();
</script>
"""


def require_login():
    """모든 페이지 상단에서 호출. 미로그인이면 로그인 화면 표시 후 st.stop()."""
    if "logged_in" not in st.session_state:
        st.session_state.update({
            "logged_in": False,
            "role": None,
            "messages": [],
            "faq_trigger": None,
        })

    if not st.session_state.logged_in:
        st.markdown(COMMON_CSS, unsafe_allow_html=True)
        _, col, _ = st.columns([1.5, 2, 1.5])
        with col:
            st.markdown("<br><br><br>", unsafe_allow_html=True)
            st.markdown("# ⚡ PG 가맹점\nAI 워크스테이션")
            st.markdown("---")
            role = st.selectbox("소속 팀", list(USERS.keys()))
            pw = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
            if st.button("로그인", use_container_width=True, type="primary"):
                if pw == USERS.get(role, ""):
                    st.session_state.update({
                        "logged_in": True,
                        "role": role,
                        "messages": [],
                    })
                    st.rerun()
                else:
                    st.error("비밀번호가 올바르지 않습니다.")
        st.stop()


def sidebar_common():
    """공통 사이드바 — 로고, 유저 정보, 로그아웃."""
    with st.sidebar:
        st.markdown("### ⚡ AI 워크스테이션")
        icon = ROLE_ICON.get(st.session_state.role, "")
        st.markdown(f"**{icon} {st.session_state.role}** 접속 중")
        st.markdown("---")

        st.markdown("🏠 **홈** · 💬 **챗봇** — 사이드바 상단 메뉴를 이용하세요")

        st.markdown("---")
        if st.button("로그아웃", use_container_width=True, key="sidebar_logout"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()
