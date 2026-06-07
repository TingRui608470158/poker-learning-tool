import type { HandReview, Phase } from "../types/game";

interface CoachPanelProps {
  phase: Phase;
  review: HandReview | null;
  handEventCount: number;
  loading: boolean;
  error: string | null;
}

export function CoachPanel({
  phase,
  review,
  handEventCount,
  loading,
  error,
}: CoachPanelProps) {
  const inProgress = phase !== "hand_over";
  const hasReview = Boolean(review?.sections.length);

  return (
    <div className="flex h-full min-h-[420px] flex-col rounded-2xl border border-white/10 bg-white/[0.03] xl:min-h-0">
      <div className="shrink-0 border-b border-white/10 px-4 py-3">
        <h2 className="text-sm font-semibold text-accent">專家點評</h2>
        {handEventCount > 0 && (
          <p className="mt-0.5 text-[10px] text-white/35">
            已記錄 {handEventCount} 步行動
          </p>
        )}
      </div>

      <div className="min-h-0 flex-1 space-y-4 overflow-y-auto px-4 py-4">
        {loading && (
          <div className="flex items-center gap-2 text-sm text-muted">
            <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-accent border-t-transparent" />
            正在生成分街點評…
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-950/30 px-3 py-2 text-sm text-red-200">
            {error}
            <p className="mt-1 text-xs opacity-70">
              請確認 Ollama 已在 127.0.0.1:11434 運行
            </p>
          </div>
        )}

        {!loading && !error && hasReview && review && (
          <div className="space-y-4">
            {review.sections.map((section) => (
              <section
                key={section.street}
                className="rounded-xl border border-white/10 bg-black/20 px-3 py-3"
              >
                <h3 className="border-b border-accent/30 pb-2 text-sm font-bold text-accent">
                  {section.title}
                </h3>
                <p className="mt-2 whitespace-pre-wrap break-words text-sm leading-relaxed text-[#dcefe3]">
                  {section.content}
                </p>
              </section>
            ))}
          </div>
        )}

        {!loading && !error && !hasReview && inProgress && (
          <p className="text-sm leading-relaxed text-white/40">
            本局進行中，結束後可請小六分街點評（翻前／翻牌／轉牌／河牌）。
          </p>
        )}

        {!loading && !error && !hasReview && !inProgress && (
          <p className="text-sm leading-relaxed text-white/40">
            本局已結束，按下方「取得小六點評」。
          </p>
        )}
      </div>
    </div>
  );
}
