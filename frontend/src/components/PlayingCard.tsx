import { parseCard } from "../utils/cards";

type CardVariant = "face-up" | "face-down" | "empty";
type CardSize = "sm" | "md";

const SIZE = {
  sm: "h-16 w-11 text-base",
  md: "h-[4.5rem] w-10 text-lg",
};

interface PlayingCardProps {
  cardIndex?: string;
  variant?: CardVariant;
  size?: CardSize;
  className?: string;
}

export function PlayingCard({
  cardIndex,
  variant = "face-up",
  size = "md",
  className = "",
}: PlayingCardProps) {
  const dim = SIZE[size];

  if (variant === "face-down") {
    return (
      <div
        className={`flex shrink-0 items-center justify-center rounded-md border border-[#457b9d]/80 bg-card-back text-[#a8dadc] shadow ${dim} ${className}`}
      >
        🂠
      </div>
    );
  }

  if (variant === "empty" || !cardIndex) {
    return (
      <div
        className={`shrink-0 rounded-md border border-dashed border-white/15 bg-black/10 ${dim} ${className}`}
      />
    );
  }

  const { rank, suit, color } = parseCard(cardIndex);

  return (
    <div
      className={`flex shrink-0 flex-col items-center justify-center rounded-md border border-neutral-600 bg-card-face shadow ${dim} ${className}`}
    >
      <span className="font-bold leading-none" style={{ color }}>
        {rank}
      </span>
      <span className="text-sm leading-none" style={{ color }}>
        {suit}
      </span>
    </div>
  );
}
