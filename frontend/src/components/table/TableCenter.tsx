import { CommunityBoard } from "../CommunityBoard";

interface TableCenterProps {
  pot: number;
  communityCards: string[];
  stage: string;
}

export function TableCenter({ pot, communityCards, stage }: TableCenterProps) {
  return (
    <div className="pointer-events-none absolute left-1/2 top-1/2 z-10 w-[min(90%,280px)] -translate-x-1/2 -translate-y-1/2 text-center">
      <span className="inline-block rounded-full bg-black/35 px-3 py-0.5 text-[11px] text-white/70">
        {stage}
      </span>
      <div className="mt-3 flex justify-center">
        <CommunityBoard cards={communityCards} />
      </div>
      <p className="mt-3 text-[11px] uppercase tracking-wider text-white/45">
        Pot
      </p>
      <p className="text-2xl font-bold tabular-nums text-[#fefae0]">{pot}</p>
    </div>
  );
}
