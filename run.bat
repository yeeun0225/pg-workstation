@echo off
chcp 65001 > nul
echo PG 가맹점 AI 워크스테이션 시작 중...
echo.
echo 브라우저에서 http://localhost:8501 로 접속하세요
echo 종료하려면 이 창에서 Ctrl+C 를 누르세요
echo.
set PATH=C:\Users\USER\.local\bin;%PATH%
uv run streamlit run app.py --server.port 8501 --browser.gatherUsageStats false
