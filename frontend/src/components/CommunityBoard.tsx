import { PlayingCard } from "./PlayingCard";

interface CommunityBoardProps {
  cards: string[];
}

export function CommunityBoard({ cards }: CommunityBoardProps) {
  const slots = Array.from({ length: 5 }, (_, i) => cards[i]);

  return (
    <div className="flex justify-center gap-2">
      {slots.map((card, index) => (
        <PlayingCard
          key={index}
          cardIndex={card}
          size="sm"
          variant={card ? "face-up" : "empty"}
        />
      ))}
    </div>
  );
}
