import type { Phase, TableView } from "../types/game";
import { positionDisplay } from "../types/game";

interface TurnBannerProps {
  phase: Phase;
  view: TableView;
  heroSeat: number;
}

export function TurnBanner({ phase, view, heroSeat }: TurnBannerProps) {
  if (view.is_over || phase === "hand_over") {
    return null;
  }

  const actor = view.seats[view.current_actor];
  const actorPos = actor
    ? positionDisplay(actor.position_en, actor.position_zh)
    : `座位 ${view.current_actor}`;
  const isHeroTurn =
    phase === "awaiting_human_action" || view.current_actor === heroSeat;

  if (isHeroTurn) {
    return (
      <div className="rounded-xl border border-accent/40 bg-accent/15 px-4 py-3 text-center">
        <p className="text-base font-bold text-accent">輪到你</p>
        <p className="mt-0.5 text-sm text-white/70">
          {actorPos} · 請選擇下方動作
        </p>
      </div>
    );
  }

  return null;
}
