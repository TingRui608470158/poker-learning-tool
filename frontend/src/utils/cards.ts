export interface CardDisplay {
  rank: string;
  suit: string;
  color: string;
}

const SUIT_SYMBOLS: Record<string, string> = {
  S: "♠",
  H: "♥",
  D: "♦",
  C: "♣",
};

const SUIT_COLORS: Record<string, string> = {
  S: "#1a1a1a",
  H: "#c0392b",
  D: "#2980b9",
  C: "#27ae60",
};

export function parseCard(cardIndex: string): CardDisplay {
  if (!cardIndex) {
    return { rank: "?", suit: "", color: "#666666" };
  }
  const suit = cardIndex[0];
  let rank = cardIndex.slice(1);
  if (rank === "T") rank = "10";
  return {
    rank,
    suit: SUIT_SYMBOLS[suit] ?? suit,
    color: SUIT_COLORS[suit] ?? "#1a1a1a",
  };
}
