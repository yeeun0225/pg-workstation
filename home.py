import streamlit as st
import json
import os
import anthropic
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from utils.auth import ROLE_ICON

load_dotenv(Path(__file__).parent / ".env", override=True)

DATA = Path(__file__).parent / "data"

# ── 사이드바 로그아웃 ───────────────────────────────────
with st.sidebar:
    st.markdown("---")
    icon = ROLE_ICON.get(st.session_state.role, "")
    st.markdown(f"**{icon} {st.session_state.role}** 접속 중")
    if st.button("로그아웃", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

# ── 홈 전용 스타일 ──────────────────────────────────────
st.markdown("""
<style>
.stat-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 20px 24px;
    text-align: center;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.stat-num   { font-size: 40px; font-weight: 800; line-height: 1.1; }
.stat-label { font-size: 13px; color: #64748B; margin-top: 4px; }
.menu-card  {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    min-height: 130px;
}
.menu-icon  { font-size: 32px; }
.menu-title { font-size: 16px; font-weight: 700; color: #1E293B; margin: 10px 0 4px; }
.menu-desc  { font-size: 12px; color: #64748B; line-height: 1.5; }
.badge-mvp  {
    display: inline-block; background: #2563EB; color: #FFFFFF;
    font-size: 10px; font-weight: 700; border-radius: 4px;
    padding: 2px 7px; margin-left: 6px; vertical-align: middle;
}
.badge-soon {
    display: inline-block; background: #F1F5F9; color: #94A3B8;
    font-size: 10px; font-weight: 700; border-radius: 4px;
    padding: 2px 7px; margin-left: 6px; vertical-align: middle;
}
.notice-card {
    background: #FFFFFF;
    border-left: 3px solid #2563EB;
    border-radius: 0 10px 10px 0;
    padding: 14px 18px; margin-bottom: 10px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.notice-title { font-size: 13px; color: #1E293B; font-weight: 600; }
.notice-meta  { font-size: 11px; color: #94A3B8; margin-top: 3px; }
</style>
""", unsafe_allow_html=True)

# ── 인사 헤더 ───────────────────────────────────────────
now = datetime.now()
hour = now.hour
greeting = "좋은 아침이에요" if hour < 12 else ("좋은 오후에요" if hour < 18 else "수고 많으셨어요")
days = {"Mon":"월","Tue":"화","Wed":"수","Thu":"목","Fri":"금","Sat":"토","Sun":"일"}
date_str = now.strftime("%Y년 %m월 %d일") + f" ({days[now.strftime('%a')]})"

st.markdown("## ⚡ PG 가맹점 AI 워크스테이션")
st.markdown(f"**{greeting}!** 오늘도 힘차게 시작해볼까요 — {date_str}")
st.markdown("---")

# ── 통계 카드 ───────────────────────────────────────────
def safe_count(fname, pred):
    p = DATA / fname
    if not p.exists(): return 0
    try: return sum(1 for i in json.loads(p.read_text(encoding="utf-8")) if pred(i))
    except: return 0

open_issues = safe_count("issues.json", lambda i: i.get("status") != "완료")
open_todos  = safe_count("todos.json",  lambda i: not i.get("done"))
total_merch = safe_count("merchants.json", lambda _: True)

c1, c2, c3, c4 = st.columns(4)
for col, num, label, color in [
    (c1, open_issues,  "미해결 이슈",  "#EF4444" if open_issues > 0 else "#16A34A"),
    (c2, open_todos,   "미완료 투두",  "#D97706" if open_todos  > 0 else "#16A34A"),
    (c3, total_merch,  "등록 가맹점",  "#2563EB"),
    (c4, now.strftime("%H:%M"), "현재 시각", "#94A3B8"),
]:
    with col:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-num" style="color:{color}">{num}</div>
            <div class="stat-label">{label}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── 기능 메뉴 ───────────────────────────────────────────
st.markdown("### 기능 메뉴")
st.caption("챗봇은 왼쪽 사이드바 상단 메뉴에서 이동할 수 있습니다.")

menus = [
    ("💬", "챗봇",     "FAQ · R&R · 파일 안내\n영업팀 질문 즉시 응답",  "mvp"),
    ("📋", "이슈 관리", "가맹점별 이슈 등록 · 추적\n유사 이슈 자동 매칭", "soon"),
    ("✅", "투두",     "담당 가맹점별 할일 관리\n이슈 연동 자동 생성",   "soon"),
    ("⚙️", "검증 엔진", "코드 유형별 설정 자동 검증\n배치 업로드 · 수정 가이드", "soon"),
    ("📊", "월간 리포트","가맹점 매출 · 이슈 통계\n자동 리포트 생성",    "soon"),
    ("🔔", "알림 센터", "반복 이슈 경고 · 미해결 알림\n주간 체크리스트", "soon"),
]

cols = st.columns(3)
for i, (icon, title, desc, badge) in enumerate(menus):
    with cols[i % 3]:
        badge_html = '<span class="badge-mvp">MVP</span>' if badge == "mvp" else '<span class="badge-soon">준비 중</span>'
        st.markdown(f"""
        <div class="menu-card">
            <div class="menu-icon">{icon}</div>
            <div class="menu-title">{title}{badge_html}</div>
            <div class="menu-desc">{desc.replace(chr(10), "<br>")}</div>
        </div>""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

# ── 공지 + 로드맵 ───────────────────────────────────────
st.markdown("---")
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### 📌 공지사항")
    for title, meta in [
        ("챗봇 MVP 오픈",                       "2026-04-21 · 시스템"),
        ("FAQ 문서는 data/faq.txt에서 편집",    "2026-04-21 · 가이드"),
        ("R&R 테이블은 data/rar.json에서 수정", "2026-04-21 · 가이드"),
    ]:
        st.markdown(f"""
        <div class="notice-card">
            <div class="notice-title">{title}</div>
            <div class="notice-meta">{meta}</div>
        </div>""", unsafe_allow_html=True)

with col_right:
    st.markdown("### 🗺️ 개발 로드맵")
    for icon, name, stage, color in [
        ("✅", "챗봇 MVP",    "완료",    "#16A34A"),
        ("🔄", "이슈 관리",  "다음 단계","#2563EB"),
        ("⏳", "투두 시스템","단기",    "#D97706"),
        ("⏳", "검증 엔진",  "중기",    "#D97706"),
        ("⏳", "월간 리포트","장기",    "#94A3B8"),
    ]:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid #E2E8F0">'
            f'<span style="font-size:16px">{icon}</span>'
            f'<span style="color:#334155;font-size:13px;flex:1">{name}</span>'
            f'<span style="font-size:11px;color:{color};font-weight:600">{stage}</span>'
            f'</div>', unsafe_allow_html=True)

# ── 팝업 챗봇 ──────────────────────────────────────────
if "popup_open" not in st.session_state:
    st.session_state.popup_open = False
if "popup_messages" not in st.session_state:
    st.session_state.popup_messages = []

# FAB 버튼 스타일
st.markdown("""
<style>
div[data-testid="stButton"].fab-btn > button {
    position: fixed !important;
    bottom: 32px !important;
    right: 32px !important;
    width: 64px !important;
    height: 64px !important;
    border-radius: 50% !important;
    background: linear-gradient(135deg,#2563EB,#1D4ED8) !important;
    border: none !important;
    font-size: 28px !important;
    box-shadow: 0 6px 20px rgba(37,99,235,0.5) !important;
    z-index: 9999 !important;
    padding: 0 !important;
    cursor: pointer !important;
}
</style>
""", unsafe_allow_html=True)

# 팝업 채팅창
if st.session_state.popup_open:
    st.markdown("""
    <style>
    .popup-box {
        position: fixed;
        bottom: 110px;
        right: 24px;
        width: 360px;
        height: 480px;
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        box-shadow: 0 12px 40px rgba(0,0,0,0.18);
        z-index: 9998;
        display: flex;
        flex-direction: column;
        overflow: hidden;
    }
    .popup-header {
        background: linear-gradient(135deg,#2563EB,#1D4ED8);
        color: white;
        padding: 14px 18px;
        font-weight: 700;
        font-size: 14px !important;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .popup-messages {
        flex: 1;
        overflow-y: auto;
        padding: 12px;
    }
    .popup-msg-user {
        background: #EFF6FF;
        border-radius: 12px 12px 2px 12px;
        padding: 8px 12px;
        margin: 6px 0 6px 40px;
        font-size: 12px !important;
        color: #1E293B;
    }
    .popup-msg-bot {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px 12px 12px 2px;
        padding: 8px 12px;
        margin: 6px 40px 6px 0;
        font-size: 12px !important;
        color: #1E293B;
    }
    </style>
    """, unsafe_allow_html=True)

    # 팝업 헤더
    st.markdown('<div class="popup-box"><div class="popup-header">🤖 AI 챗봇 &nbsp;·&nbsp; 빠른 질문</div></div>', unsafe_allow_html=True)

    # 대화 이력
    msgs_html = '<div class="popup-messages">'
    for m in st.session_state.popup_messages:
        if m["role"] == "user":
            msgs_html += f'<div class="popup-msg-user">❓ {m["content"]}</div>'
        else:
            msgs_html += f'<div class="popup-msg-bot">🤖 {m["content"]}</div>'
    msgs_html += '</div>'

    # 팝업 채팅창 표시
    with st.container():
        col_close, _ = st.columns([1, 8])
        with col_close:
            if st.button("✕", key="popup_close"):
                st.session_state.popup_open = False
                st.rerun()

        for m in st.session_state.popup_messages:
            avatar = "❓" if m["role"] == "user" else "🤖"
            with st.chat_message(m["role"], avatar=avatar):
                st.markdown(m["content"])

        popup_input = st.chat_input("빠른 질문...", key="popup_chat_input")
        if popup_input:
            st.session_state.popup_messages.append({"role": "user", "content": popup_input})
            with st.chat_message("user", avatar="❓"):
                st.markdown(popup_input)

            api_key = os.getenv("ANTHROPIC_API_KEY", "")
            faq_path = DATA / "faq.txt"
            faq = faq_path.read_text(encoding="utf-8") if faq_path.exists() else ""
            system = f"""당신은 PG사 가맹점 관리팀 전용 AI 챗봇입니다. 아래 FAQ를 참고해서 간결하게 답변하세요.
FAQ에 없는 내용은 "담당 부서에 문의해 주세요."라고 안내하세요.
===
{faq}
==="""
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("..."):
                    client = anthropic.Anthropic(api_key=api_key)
                    resp = client.messages.create(
                        model="claude-haiku-4-5-20251001", max_tokens=512,
                        system=system,
                        messages=[{"role": m["role"], "content": m["content"]}
                                  for m in st.session_state.popup_messages],
                    )
                    answer = resp.content[0].text
                st.markdown(answer)
            st.session_state.popup_messages.append({"role": "assistant", "content": answer})
            st.rerun()

# FAB 버튼 (항상 고정)
label = "✕" if st.session_state.popup_open else "🤖"
if st.button(label, key="fab_toggle"):
    st.session_state.popup_open = not st.session_state.popup_open
    st.rerun()
