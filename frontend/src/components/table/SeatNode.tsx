import type { SeatView } from "../../types/game";
import { PlayingCard } from "../PlayingCard";
import { DealerButton } from "./DealerButton";
import { PositionBadge } from "./PositionBadge";

interface SeatNodeProps {
  seat: SeatView;
  isActor: boolean;
  compact?: boolean;
}

export function SeatNode({ seat, isActor, compact = false }: SeatNodeProps) {
  const cards =
    seat.hand_hidden || seat.hand.length === 0
      ? [undefined, undefined]
      : seat.hand;

  return (
    <div className="relative">
      {isActor && (
        <div
          className={`absolute -top-3 left-1/2 z-30 -translate-x-1/2 whitespace-nowrap rounded-full px-2.5 py-0.5 text-[11px] font-bold shadow-md sm:text-xs ${
            seat.is_hero
              ? "bg-accent text-felt-dark"
              : "border border-white/25 bg-white/90 text-[#1a1a1a]"
          }`}
        >
          {seat.is_hero ? "你的回合" : "對手"}
        </div>
      )}

      <div
        className={`relative flex min-w-[120px] max-w-[160px] flex-col items-center gap-1.5 rounded-xl border px-2 py-2 backdrop-blur-sm sm:min-w-[140px] sm:max-w-[180px] sm:px-3 sm:py-2.5 ${
          isActor
            ? "border-accent bg-black/55 shadow-[0_0_16px_rgba(255,209,102,0.35)] ring-2 ring-accent"
            : "border-white/15 bg-black/35"
        } ${seat.is_hero && !isActor ? "ring-1 ring-accent/35" : ""}`}
      >
        {seat.is_hero && !isActor && (
          <div className="absolute -left-1 -top-1 z-10 rounded bg-accent/80 px-1 py-px text-[9px] font-bold text-felt-dark">
            你
          </div>
        )}

        {seat.is_dealer && (
          <div className="absolute -right-1 -top-1 z-10">
            <DealerButton />
          </div>
        )}

        <PositionBadge
          en={seat.position_en}
          zh={seat.position_zh}
          compact={compact}
        />

        <div className="flex gap-1">
          {cards.map((card, i) => (
            <PlayingCard
              key={i}
              cardIndex={card}
              size="sm"
              variant={
                seat.hand_hidden ? "face-down" : card ? "face-up" : "empty"
              }
            />
          ))}
        </div>

        <div className="w-full text-center text-[10px] leading-snug text-white/65 sm:text-xs">
          <span className="text-white/45">起 </span>
          <span className="tabular-nums text-white/75">{seat.starting_bb}bb</span>
          <span className="text-white/35"> · </span>
          <span className="text-white/45">剩 </span>
          <span className="font-semibold tabular-nums text-white">
            {seat.stack_bb}bb
          </span>
          {seat.stakes > 0 && (
            <span className="text-accent/90">
              {" "}
              · 本輪 {seat.stakes}
            </span>
          )}
        </div>

        {seat.last_action_label && (
          <div
            className={`max-w-full truncate text-xs ${
              isActor ? "text-white/60" : "text-white/40"
            }`}
          >
            {seat.last_action_label}
          </div>
        )}
      </div>
    </div>
  );
}
