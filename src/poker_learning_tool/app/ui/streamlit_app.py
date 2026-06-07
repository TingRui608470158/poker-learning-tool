"""Streamlit 可視化學習界面。"""

from __future__ import annotations

import streamlit as st

from poker_learning_tool.app.learning_session import LearningSession
from poker_learning_tool.env import SeatConfig, build_seats, card_label, model_available
from poker_learning_tool.env.players import PlayerKind
from poker_learning_tool.perspective import XiaoLiuSkill

TABLE_CSS = """
<style>
.poker-table {
    background: linear-gradient(145deg, #1b4332 0%, #2d6a4f 50%, #1b4332 100%);
    border: 3px solid #40916c;
    border-radius: 16px;
    padding: 24px 16px;
    margin: 8px 0 16px 0;
}
.seat-label {
    font-size: 1.05rem;
    font-weight: 700;
    margin-bottom: 8px;
    color: #d8f3dc;
}
.stage-badge {
    display: inline-block;
    background: #ffd166;
    color: #1b4332;
    font-weight: 700;
    padding: 4px 14px;
    border-radius: 20px;
    margin-bottom: 8px;
}
.pot-display {
    color: #fefae0;
    font-size: 1.3rem;
    font-weight: 700;
    margin: 8px 0 12px 0;
}
.card-row {
    display: flex;
    gap: 8px;
    justify-content: center;
    flex-wrap: wrap;
    min-height: 90px;
    align-items: center;
}
.card {
    width: 56px;
    height: 80px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.4rem;
    font-weight: 700;
    box-shadow: 0 2px 6px rgba(0,0,0,0.35);
}
.card.face-up {
    background: #fefefe;
    border: 2px solid #333;
}
.card.face-down {
    background: #1d3557;
    border: 2px solid #457b9d;
    color: #a8dadc;
    font-size: 1.6rem;
}
.card.empty {
    background: rgba(255,255,255,0.08);
    border: 2px dashed rgba(255,255,255,0.25);
    color: transparent;
}
.actor-badge {
    color: #ffd166;
    font-size: 0.9rem;
    margin-top: 4px;
}
</style>
"""

KIND_LABELS = {
    "human": "真人",
    "random": "RL 隨機",
    "dqn": "RL DQN",
}


def _render_card_html(
    card_index: str | None, *, face_down: bool = False, empty: bool = False
) -> str:
    if face_down:
        return '<div class="card face-down">🂠</div>'
    if empty or not card_index:
        return '<div class="card empty">?</div>'
    text, color = card_label(card_index)
    return f'<div class="card face-up" style="color:{color}">{text}</div>'


def _render_card_row(
    cards: list[str], *, count: int = 2, face_down: bool = False
) -> str:
    if face_down:
        items = [_render_card_html(None, face_down=True) for _ in range(count)]
    elif cards:
        items = [_render_card_html(c) for c in cards]
    else:
        items = [_render_card_html(None, empty=True) for _ in range(count)]
    return f'<div class="card-row">{"".join(items)}</div>'


def _render_table(view) -> None:
    parts = [TABLE_CSS, '<div class="poker-table">']
    for seat in view.seats:
        actor = (
            '<div class="actor-badge">▶ 輪到行動</div>'
            if seat.seat == view.current_actor and not view.is_over
            else ""
        )
        pos = f"{seat.position_en}（{seat.position_zh}）" if seat.position_en else ""
        parts.append(f'<div class="seat-label">座位 {seat.seat} · {pos}</div>')
        parts.append(_render_card_row(seat.hand, face_down=seat.hand_hidden))
        parts.append(
            f'<div style="color:#b7e4c7;font-size:0.95rem;">剩 {seat.stack_remaining} · 本輪已押 {seat.stakes}</div>'
        )
        parts.append(actor)
    parts.append('<div style="text-align:center;margin:20px 0;">')
    parts.append(f'<span class="stage-badge">{view.stage}</span>')
    parts.append(f'<div class="pot-display">底池：{view.pot}</div>')
    parts.append(_render_card_row(view.community_cards, count=5))
    parts.append("</div></div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def _seat_kind_select(label: str, key: str) -> PlayerKind:
    options: list[PlayerKind] = ["human", "random"]
    if model_available():
        options.append("dqn")
    labels = {k: KIND_LABELS[k] for k in options}
    choice = st.selectbox(
        label,
        options=options,
        format_func=lambda x: labels[x],
        key=key,
    )
    return choice


def _build_session(settings: dict) -> LearningSession:
    return LearningSession(
        coach=XiaoLiuSkill(),
        seats=build_seats(2, settings["hero_seat"]),
        hero_seat=settings["hero_seat"],
    )


def main() -> None:
    st.set_page_config(
        page_title="Poker Learning Tool",
        page_icon="🃏",
        layout="wide",
    )

    defaults = {
        "learning": None,
        "settings": {
            "seat0": "human",
            "seat1": "random",
            "hero_seat": 0,
        },
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    st.sidebar.header("牌局設定")
    st.sidebar.caption("每局各座位獨立隨機 1～100bb")
    seat0 = _seat_kind_select("座位 0", "seat0_kind")
    seat1 = _seat_kind_select("座位 1", "seat1_kind")
    hero_seat = st.sidebar.radio("小六分析視角", [0, 1], format_func=lambda x: f"座位 {x}")

    if st.sidebar.button("新一局", type="primary", use_container_width=True):
        st.session_state.settings = {
            "seat0": seat0,
            "seat1": seat1,
            "hero_seat": hero_seat,
        }
        session = _build_session(st.session_state.settings)
        session.start_hand()
        st.session_state.learning = session
        st.rerun()

    if st.session_state.learning is None:
        st.session_state.settings.update(
            {
                "seat0": seat0,
                "seat1": seat1,
                "hero_seat": hero_seat,
            }
        )
        session = _build_session(st.session_state.settings)
        session.start_hand()
        st.session_state.learning = session

    learning: LearningSession = st.session_state.learning
    state = learning.get_state()

    st.title("Poker Learning Tool")
    st.caption("步進學習 · 小六分析 · 雙座位 Human / RL")

    _render_table(state.view)

    if state.phase == "hand_over":
        if state.view.result_message:
            st.success(state.view.result_message)
    elif state.phase == "awaiting_human_action":
        st.warning(f"輪到你（座位 {state.view.current_actor}）— 請選擇 action")

    st.subheader("小六點評")
    if state.phase == "hand_over" and state.review is None:
        if st.button("取得小六點評", type="secondary", use_container_width=True):
            with st.spinner("分街點評生成中..."):
                try:
                    learning.request_hand_review(hero_seat=hero_seat)
                    st.rerun()
                except RuntimeError as exc:
                    st.error(f"無法取得小六點評：{exc}")
    elif state.phase != "hand_over":
        st.caption("本局進行中，結束後可請小六分街點評。")
    if state.review:
        for section in state.review.sections:
            st.markdown(f"**【{section.title}】**")
            st.markdown(section.content)
            st.divider()

    st.subheader("操作")
    if state.phase == "awaiting_human_action":
        actions = state.view.legal_actions
        if actions:
            cols = st.columns(len(actions))
            for index, label in enumerate(actions):
                with cols[index]:
                    if st.button(label, key=f"act_{index}", use_container_width=True):
                        learning.submit_action(index)
                        st.rerun()
    elif state.phase == "hand_over":
        if st.button("再玩一局", type="primary", use_container_width=True):
            learning.start_hand()
            st.rerun()

    st.subheader("行動紀錄")
    log = state.view.action_log or []
    st.code("\n".join(log) or "（尚無紀錄）")


if __name__ == "__main__":
    main()
