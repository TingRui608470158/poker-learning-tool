import type { HandCell, PreflopStrategy } from "../types/game";

const RANKS = ["A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"] as const;

const ACTION_COLORS: Record<string, string> = {
  fold: "bg-white/10",
  call: "bg-blue-500/50",
  raise: "bg-accent/70",
};

function cellColor(cell: HandCell): string {
  return ACTION_COLORS[cell.primary_action] ?? "bg-white/15";
}

interface GtoPanelProps {
  strategy: PreflopStrategy | null;
  numPlayers: number;
}

export function GtoPanel({ strategy, numPlayers }: GtoPanelProps) {
  if (numPlayers !== 2) {
    return (
      <div className="flex h-full min-h-[420px] flex-col rounded-2xl border border-white/10 bg-white/[0.03] p-4 xl:min-h-0">
        <h2 className="text-sm font-semibold text-accent">GTO 翻前表</h2>
        <p className="mt-4 text-sm text-white/50">
          GTO 翻前表目前僅支援 2 人桌。請切換至翻前策略模式或將人數設為 2。
        </p>
      </div>
    );
  }

  if (!strategy) {
    return (
      <div className="flex h-full min-h-[420px] flex-col rounded-2xl border border-white/10 bg-white/[0.03] p-4 xl:min-h-0">
        <h2 className="text-sm font-semibold text-accent">GTO 翻前表</h2>
        <p className="mt-4 text-sm text-white/50">
          翻後街道不提供 GTO 翻前表；請在翻牌前輪到你時查看。
        </p>
      </div>
    );
  }

  const { hero_hand, hero_cell, matrix, spot_label, disclaimer } = strategy;

  return (
    <div className="flex h-full min-h-[420px] flex-col rounded-2xl border border-white/10 bg-white/[0.03] xl:min-h-0">
      <div className="shrink-0 border-b border-white/10 px-4 py-3">
        <h2 className="text-sm font-semibold text-accent">GTO 翻前表</h2>
        <p className="mt-0.5 text-[10px] text-white/40">{spot_label}</p>
        <p className="mt-1 text-xs text-white/60">
          你的手牌 <span className="font-bold text-[#fefae0]">{hero_hand}</span>
          {" · "}EV {hero_cell.ev_bb >= 0 ? "+" : ""}
          {hero_cell.ev_bb.toFixed(2)}bb
        </p>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-3 py-3">
        <div className="mb-2 flex gap-3 text-[10px] text-white/40">
          <span className="flex items-center gap-1">
            <span className="inline-block h-2 w-2 rounded-sm bg-white/10" /> 棄牌
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block h-2 w-2 rounded-sm bg-blue-500/50" /> 跟注
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block h-2 w-2 rounded-sm bg-accent/70" /> 加注
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="mx-auto border-collapse text-[9px]">
            <thead>
              <tr>
                <th className="w-4" />
                {RANKS.map((r) => (
                  <th key={r} className="w-5 px-0.5 text-white/30">
                    {r}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {matrix.map((row, ri) => (
                <tr key={RANKS[ri]}>
                  <td className="pr-1 text-right text-white/30">{RANKS[ri]}</td>
                  {row.map((cell, ci) => {
                    if (!cell) {
                      return <td key={ci} className="h-5 w-5 p-px" />;
                    }
                    const isHero = cell.hand === hero_hand;
                    return (
                      <td key={ci} className="h-5 w-5 p-px">
                        <div
                          title={`${cell.hand} F${(cell.fold * 100).toFixed(0)}% C${(cell.call * 100).toFixed(0)}% R${(cell.raise * 100).toFixed(0)}%`}
                          className={`flex h-full w-full items-center justify-center rounded-sm text-[7px] font-medium text-white/90 ${cellColor(cell)} ${isHero ? "ring-2 ring-yellow-400 ring-offset-1 ring-offset-[#0a1612]" : ""}`}
                        >
                          {cell.hand.length <= 3 ? cell.hand : ""}
                        </div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {disclaimer && (
          <p className="mt-3 text-[10px] leading-relaxed text-white/35">{disclaimer}</p>
        )}
      </div>
    </div>
  );
}
