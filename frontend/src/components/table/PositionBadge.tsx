interface PositionBadgeProps {
  en: string;
  zh: string;
  compact?: boolean;
}

export function PositionBadge({ en, zh, compact = false }: PositionBadgeProps) {
  if (compact) {
    return (
      <span className="rounded bg-black/40 px-1.5 py-0.5 text-[10px] font-bold text-accent">
        {en}
      </span>
    );
  }
  return (
    <div className="text-center leading-tight">
      <div className="text-xs font-bold tracking-wide text-accent">{en}</div>
      <div className="text-[10px] text-white/50">{zh}</div>
    </div>
  );
}
