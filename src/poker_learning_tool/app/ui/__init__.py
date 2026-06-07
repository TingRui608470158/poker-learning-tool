"""Streamlit UI 入口。"""

from poker_learning_tool.app.ui.streamlit_app import main as run_streamlit_main


def run_learning_ui() -> None:
    """啟動 Streamlit 學習界面（需以 streamlit run 執行）。"""
    run_streamlit_main()
