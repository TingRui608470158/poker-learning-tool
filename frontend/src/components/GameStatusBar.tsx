import type { Phase, TableView } from "../types/game";

interface GameStatusBarProps {
  stage: string;
  phase: Phase;
  view: TableView;
}

const PHASE_HINT: Record<Phase, string> = {
  awaiting_next: "對手回合",
  awaiting_human_action: "輪到你",
  hand_over: "本局結束",
};

export function GameStatusBar({ stage, phase, view }: GameStatusBarProps) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3">
      <div className="flex flex-wrap items-center gap-2">
        <span className="rounded-full bg-accent px-3 py-1 text-xs font-bold text-felt-dark">
          {stage}
        </span>
        <span className="text-xs text-white/45">
          {view.num_players} 人桌 · 盲注 {view.small_blind}/{view.big_blind} ·
          各座位 1～100bb
        </span>
      </div>
      <p
        className={`text-sm font-medium ${
          phase === "awaiting_human_action" ? "text-accent" : "text-muted"
        }`}
      >
        {PHASE_HINT[phase]}
      </p>
    </div>
  );
}
