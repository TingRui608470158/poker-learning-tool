import { useState } from "react";
import type { HandReview, LearningMode, Phase, PreflopStrategy } from "../types/game";
import { CoachPanel } from "./CoachPanel";
import { GtoPanel } from "./GtoPanel";

interface RightSidebarProps {
  learningMode: LearningMode;
  phase: Phase;
  review: HandReview | null;
  handEventCount: number;
  coachLoading: boolean;
  coachError: string | null;
  preflopStrategy: PreflopStrategy | null;
  numPlayers: number;
}

export function RightSidebar({
  learningMode,
  phase,
  review,
  handEventCount,
  coachLoading,
  coachError,
  preflopStrategy,
  numPlayers,
}: RightSidebarProps) {
  const [tab, setTab] = useState<"gto" | "coach">("gto");

  if (learningMode === "preflop_gto") {
    return <GtoPanel strategy={preflopStrategy} numPlayers={numPlayers} />;
  }

  if (learningMode === "coach_review") {
    return (
      <CoachPanel
        phase={phase}
        review={review}
        handEventCount={handEventCount}
        loading={coachLoading}
        error={coachError}
      />
    );
  }

  return (
    <div className="flex h-full min-h-[420px] flex-col xl:min-h-0">
      <div className="mb-2 flex shrink-0 gap-1 rounded-xl border border-white/10 bg-black/20 p-1">
        <button
          type="button"
          onClick={() => setTab("gto")}
          className={`flex-1 rounded-lg py-2 text-xs font-semibold transition ${tab === "gto" ? "bg-accent/20 text-accent" : "text-white/45 hover:text-white/70"}`}
        >
          GTO 翻前
        </button>
        <button
          type="button"
          onClick={() => setTab("coach")}
          className={`flex-1 rounded-lg py-2 text-xs font-semibold transition ${tab === "coach" ? "bg-accent/20 text-accent" : "text-white/45 hover:text-white/70"}`}
        >
          專家點評
        </button>
      </div>
      <div className="min-h-0 flex-1">
        {tab === "gto" ? (
          <GtoPanel strategy={preflopStrategy} numPlayers={numPlayers} />
        ) : (
          <CoachPanel
            phase={phase}
            review={review}
            handEventCount={handEventCount}
            loading={coachLoading}
            error={coachError}
          />
        )}
      </div>
    </div>
  );
}
