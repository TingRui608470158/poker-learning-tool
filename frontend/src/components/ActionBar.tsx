import type { ReactNode } from "react";
import type { LearningMode, Phase, PreflopStrategy } from "../types/game";

interface ActionBarProps {
  phase: Phase;
  learningMode: LearningMode;
  legalActions: string[];
  preflopStrategy: PreflopStrategy | null;
  busy: boolean;
  coachLoading: boolean;
  hasAnalysis: boolean;
  onAction: (index: number) => void;
  onNewHand: () => void;
  onRequestReview: () => void;
}

function ActionHint({ children }: { children: ReactNode }) {
  return (
    <p className="mb-3 text-center text-sm font-semibold text-accent">
      {children}
    </p>
  );
}

function formatEv(ev: number | null): string | null {
  if (ev === null) return null;
  const sign = ev >= 0 ? "+" : "";
  return `EV ${sign}${ev.toFixed(2)}bb`;
}

function formatGto(pct: number | null): string | null {
  if (pct === null) return null;
  return `GTO ${(pct * 100).toFixed(0)}%`;
}

export function ActionBar({
  phase,
  learningMode,
  legalActions,
  preflopStrategy,
  busy,
  coachLoading,
  hasAnalysis,
  onAction,
  onNewHand,
  onRequestReview,
}: ActionBarProps) {
  const showGtoHints =
    learningMode !== "coach_review" &&
    preflopStrategy !== null &&
    preflopStrategy.actions.length > 0;

  if (phase === "hand_over") {
    const showReview =
      learningMode !== "preflop_gto" && !hasAnalysis;

    return (
      <div className="flex flex-wrap gap-2 lg:flex-nowrap">
        {showReview && (
          <button
            type="button"
            disabled={busy || coachLoading}
            onClick={onRequestReview}
            className="rounded-xl bg-accent px-6 py-3 text-sm font-bold text-felt-dark transition hover:brightness-110 disabled:opacity-50"
          >
            {coachLoading ? "點評生成中…" : "取得小六點評"}
          </button>
        )}
        <button
          type="button"
          disabled={busy || coachLoading}
          onClick={onNewHand}
          className="rounded-xl border border-white/20 bg-white/10 px-6 py-3 text-sm font-semibold transition hover:bg-white/15 disabled:opacity-50"
        >
          再玩一局
        </button>
      </div>
    );
  }

  if (phase === "awaiting_human_action") {
    return (
      <div>
        <ActionHint>請選擇你的動作</ActionHint>
        <div className="flex flex-wrap gap-2 lg:flex-nowrap">
          {legalActions.map((label, index) => {
            const advice = preflopStrategy?.actions.find(
              (a) => a.action_index === index,
            );
            const evText = showGtoHints ? formatEv(advice?.ev_bb ?? null) : null;
            const gtoText = showGtoHints ? formatGto(advice?.gto_pct ?? null) : null;

            return (
              <button
                key={index}
                type="button"
                disabled={busy}
                onClick={() => onAction(index)}
                className="flex shrink-0 flex-col items-center rounded-xl border border-accent/30 bg-accent/10 px-4 py-2.5 text-sm font-medium whitespace-nowrap text-[#fefae0] transition hover:bg-accent/20 disabled:opacity-50"
              >
                <span>{label}</span>
                {(evText || gtoText) && (
                  <span className="mt-0.5 text-[10px] font-normal text-white/50">
                    {[evText, gtoText].filter(Boolean).join(" · ")}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <div className="py-2 text-center text-sm text-white/50">
      {busy ? "對手行動中…" : "等待對手行動…"}
    </div>
  );
}
