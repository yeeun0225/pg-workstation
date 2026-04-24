import streamlit as st
import json
from datetime import datetime
from pathlib import Path
from utils.auth import ROLE_ICON

DATA_FILE = Path(__file__).parent / "data" / "issues.json"

CATEGORIES = ["정산오류", "설정오류", "연동장애", "민원", "기타"]
SALES_TEAMS = ["전체", "PG사업부", "법인PG영업팀", "이커머스영업팀", "솔루션영업팀", "해외사업팀"]
STATUSES   = ["미해결", "처리중", "완료"]
STATUS_COLOR = {"미해결": "#EF4444", "처리중": "#D97706", "완료": "#16A34A"}

# ── 데이터 CRUD ────────────────────────────────────────
def load_issues() -> list:
    if not DATA_FILE.exists(): return []
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))

def save_issues(issues: list):
    DATA_FILE.write_text(json.dumps(issues, ensure_ascii=False, indent=2), encoding="utf-8")

def next_id(issues: list) -> str:
    if not issues: return "ISS-001"
    nums = [int(i["id"].split("-")[1]) for i in issues if "-" in i.get("id","")]
    return f"ISS-{max(nums)+1:03d}"

# ── 사이드바 ───────────────────────────────────────────
with st.sidebar:
    st.markdown("---")
    icon = ROLE_ICON.get(st.session_state.get("role",""), "")
    st.markdown(f"**{icon} {st.session_state.get('role','')}** 접속 중")
    if st.button("로그아웃", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

# ── 페이지 스타일 ──────────────────────────────────────
st.markdown("""
<style>
.issue-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 10px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.issue-id    { font-size: 11px !important; color: #94A3B8; font-weight:600; }
.issue-title { font-size: 15px !important; font-weight: 700; color: #1E293B; margin: 4px 0; }
.issue-meta  { font-size: 11px !important; color: #64748B; }
.badge {
    display: inline-block;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 11px !important;
    font-weight: 600;
    margin-right: 6px;
}
.issue-detail {
    background: #F8FAFC;
    border-top: 1px solid #E2E8F0;
    border-radius: 0 0 12px 12px;
    padding: 14px 20px;
    margin-top: -10px;
    margin-bottom: 10px;
}
/* 처리내용 버튼 */
button[data-testid^="stBaseButton"][key*="toggle_"] {
    background: #EFF6FF !important;
    border: 1px solid #BFDBFE !important;
    color: #2563EB !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    border-radius: 6px !important;
    padding: 4px 10px !important;
    width: 100% !important;
}
button[data-testid^="stBaseButton"][key*="toggle_"]:hover {
    background: #DBEAFE !important;
}
/* 삭제 버튼 */
button[data-testid^="stBaseButton"][key*="del_"] {
    background: transparent !important;
    border: none !important;
    color: #CBD5E1 !important;
    font-size: 16px !important;
    padding: 4px !important;
}
button[data-testid^="stBaseButton"][key*="del_"]:hover {
    color: #EF4444 !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("## 📋 이슈 관리")
st.caption("가맹점별 이슈를 등록하고 추적합니다.")
st.markdown("---")

issues = load_issues()

# ── 탭: 목록 / 등록 ────────────────────────────────────
tab_list, tab_new = st.tabs(["📋  이슈 목록", "✏️  새 이슈 등록"])

# ══════════════════════════════════════════════════════
# 탭 1 — 이슈 목록
# ══════════════════════════════════════════════════════
with tab_list:
    if not issues:
        st.info("등록된 이슈가 없습니다. '새 이슈 등록' 탭에서 추가해보세요.")
    else:
        # 필터
        col_s, col_c, col_t, col_q = st.columns([1.5, 1.5, 1.5, 3])
        with col_s:
            filter_status = st.selectbox("상태", ["전체"] + STATUSES, key="f_status")
        with col_c:
            filter_cat = st.selectbox("카테고리", ["전체"] + CATEGORIES, key="f_cat")
        with col_t:
            filter_team = st.selectbox("영업팀", SALES_TEAMS, key="f_team")
        with col_q:
            search_q = st.text_input("검색", placeholder="가맹점명·제목 검색", label_visibility="collapsed")

        st.markdown("<br>", unsafe_allow_html=True)

        # 필터 적용
        filtered = issues
        if filter_status != "전체":
            filtered = [i for i in filtered if i["status"] == filter_status]
        if filter_cat != "전체":
            filtered = [i for i in filtered if i["category"] == filter_cat]
        if filter_team != "전체":
            filtered = [i for i in filtered if i.get("sales_team") == filter_team]
        if search_q:
            q = search_q.lower()
            filtered = [i for i in filtered if q in i.get("merchant","").lower() or q in i.get("title","").lower()]

        # 요약 카운트
        c1, c2, c3, c4 = st.columns(4)
        for col, label, count, color in [
            (c1, "전체",   len(issues),                                "#2563EB"),
            (c2, "미해결", sum(1 for i in issues if i["status"]=="미해결"), "#EF4444"),
            (c3, "처리중", sum(1 for i in issues if i["status"]=="처리중"), "#D97706"),
            (c4, "완료",   sum(1 for i in issues if i["status"]=="완료"),   "#16A34A"),
        ]:
            with col:
                st.markdown(f"""
                <div style="background:#fff;border:1px solid #E2E8F0;border-radius:10px;
                            padding:12px 16px;text-align:center;box-shadow:0 1px 4px rgba(0,0,0,0.05)">
                    <div style="font-size:26px;font-weight:800;color:{color}">{count}</div>
                    <div style="font-size:11px;color:#64748B">{label}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.caption(f"총 {len(filtered)}건 표시 중")

        # 이슈 카드 목록
        for issue in reversed(filtered):
            s_color = STATUS_COLOR.get(issue["status"], "#94A3B8")
            iid = issue["id"]
            show_key = f"show_{iid}"
            if show_key not in st.session_state:
                st.session_state[show_key] = False

            with st.container():
                col_info, col_toggle, col_del = st.columns([8.5, 1.5, 0.5])
                with col_info:
                    st.markdown(f"""
                    <div class="issue-card">
                        <div class="issue-id">{iid} · {issue['created_at']}</div>
                        <div class="issue-title">{issue['title']}</div>
                        <div class="issue-meta">
                            <span class="badge" style="background:#EFF6FF;color:#2563EB">{issue['category']}</span>
                            <span class="badge" style="background:#F8FAFC;color:{s_color};border:1px solid {s_color}">{issue['status']}</span>
                            {f'<span class="badge" style="background:#F0FDF4;color:#16A34A">{issue["sales_team"]}</span>' if issue.get('sales_team') else ''}
                            🏢 {issue.get('merchant','미지정')} &nbsp;·&nbsp; 👤 {issue.get('assignee','미배정')}
                        </div>
                    </div>""", unsafe_allow_html=True)
                with col_toggle:
                    label = "처리내용 ▲" if st.session_state[show_key] else "처리내용 ▼"
                    if st.button(label, key=f"toggle_{iid}", use_container_width=True):
                        st.session_state[show_key] = not st.session_state[show_key]
                        st.rerun()
                with col_del:
                    if st.button("🗑️", key=f"del_{iid}", help="이슈 삭제"):
                        issues = [i for i in issues if i["id"] != iid]
                        save_issues(issues)
                        st.rerun()

                if st.session_state[show_key]:
                    st.markdown('<div class="issue-detail">', unsafe_allow_html=True)
                    if issue.get("content"):
                        st.markdown(f"**내용:** {issue['content']}")
                    if issue.get("note"):
                        st.markdown(f"**메모:** {issue['note']}")
                    col_st, col_note, col_save = st.columns([1.5, 3, 1])
                    with col_st:
                        new_status = st.selectbox(
                            "상태", STATUSES,
                            index=STATUSES.index(issue["status"]),
                            key=f"st_{iid}",
                        )
                    with col_note:
                        new_note = st.text_input(
                            "처리 메모", value=issue.get("note", ""),
                            placeholder="처리 메모 입력...",
                            key=f"note_{iid}",
                        )
                    with col_save:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("저장", key=f"save_{iid}", use_container_width=True, type="primary"):
                            for idx, iss in enumerate(issues):
                                if iss["id"] == iid:
                                    issues[idx]["status"] = new_status
                                    issues[idx]["note"]   = new_note
                                    issues[idx]["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                                    break
                            save_issues(issues)
                            st.success("저장됐습니다!")
                            st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# 탭 2 — 새 이슈 등록
# ══════════════════════════════════════════════════════
with tab_new:
    with st.form("issue_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            merchant   = st.text_input("가맹점명 *", placeholder="예) (주)테스트가맹점")
            category   = st.selectbox("카테고리 *", CATEGORIES)
        with col2:
            sales_team = st.selectbox("영업팀 구분", SALES_TEAMS[1:])
            assignee   = st.text_input("담당자", placeholder="예) 홍길동")
        with col3:
            status     = st.selectbox("초기 상태", STATUSES)

        title   = st.text_input("이슈 제목 *", placeholder="한 줄로 이슈를 요약하세요")
        content = st.text_area("이슈 내용", placeholder="상세 내용을 입력하세요", height=150)
        note    = st.text_input("메모", placeholder="추가 메모 (선택)")

        submitted = st.form_submit_button("등록", use_container_width=True, type="primary")

    if submitted:
        if not merchant or not title:
            st.error("가맹점명과 이슈 제목은 필수입니다.")
        else:
            new_issue = {
                "id":         next_id(issues),
                "merchant":   merchant,
                "category":   category,
                "sales_team": sales_team,
                "title":      title,
                "content":    content,
                "assignee":   assignee,
                "status":     status,
                "note":       note,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
            issues.append(new_issue)
            save_issues(issues)
            st.success(f"✅ 이슈 **{new_issue['id']}** 가 등록됐습니다!")
            st.rerun()
