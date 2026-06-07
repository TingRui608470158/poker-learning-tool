import type { TableView } from "../../types/game";
import { seatPositionPercent } from "../../utils/seatLayout";
import { SeatNode } from "./SeatNode";
import { TableCenter } from "./TableCenter";

interface OvalPokerTableProps {
  view: TableView;
  heroSeat: number;
}

export function OvalPokerTable({ view, heroSeat }: OvalPokerTableProps) {
  const compact = view.num_players > 6;

  return (
    <section className="mx-auto w-full max-w-4xl">
      <div
        className="relative mx-auto aspect-[16/10] w-full min-h-[320px] sm:min-h-[380px] md:min-h-[420px]"
        style={{ maxHeight: "520px" }}
      >
        {/* 木色邊軌 */}
        <div
          className="absolute inset-[2%] rounded-[50%] border-[6px] border-[#5c3d2e] shadow-2xl sm:border-8"
          style={{
            background:
              "radial-gradient(ellipse 70% 60% at 50% 45%, #2d6a4f 0%, #1a4d3e 55%, #143528 100%)",
          }}
        />

        <TableCenter
          pot={view.pot}
          communityCards={view.community_cards}
          stage={view.stage}
        />

        {view.seats.map((seat) => {
          const pos = seatPositionPercent(seat.seat, heroSeat, view.num_players);
          return (
            <div
              key={seat.seat}
              className="absolute z-20 -translate-x-1/2 -translate-y-1/2"
              style={{ left: pos.left, top: pos.top }}
            >
              <SeatNode
                seat={seat}
                isActor={view.current_actor === seat.seat && !view.is_over}
                compact={compact}
              />
            </div>
          );
        })}
      </div>

      {view.is_over && view.result_message && (
        <div className="mt-4 rounded-xl border border-emerald-500/30 bg-emerald-950/40 px-4 py-3 text-center text-sm text-emerald-100">
          {view.result_message}
        </div>
      )}
    </section>
  );
}
