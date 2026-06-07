interface ActionTimelineProps {
  lines: string[];
}

export function ActionTimeline({ lines }: ActionTimelineProps) {
  return (
    <details className="group rounded-2xl border border-white/10 bg-white/[0.03]">
      <summary className="cursor-pointer list-none px-4 py-3 text-sm font-medium text-white/70 marker:content-none [&::-webkit-details-marker]:hidden">
        <span className="flex items-center justify-between">
          行動紀錄
          <span className="text-xs text-white/35 group-open:rotate-180 transition-transform">
            ▼
          </span>
        </span>
      </summary>
      <div className="max-h-48 overflow-y-auto border-t border-white/10 px-4 py-3">
        {!lines.length ? (
          <p className="text-sm text-white/40">尚無紀錄</p>
        ) : (
          <ol className="space-y-1.5">
            {lines.map((line, index) => (
              <li
                key={`${index}-${line}`}
                className="flex gap-2 text-xs leading-relaxed text-white/55"
              >
                <span className="shrink-0 tabular-nums text-white/25">
                  {index + 1}.
                </span>
                <span>{line}</span>
              </li>
            ))}
          </ol>
        )}
      </div>
    </details>
  );
}
