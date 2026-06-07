/** 橢圓牌桌座位角度（Hero 固定於下方 90°） */
export function seatPositionPercent(
  seatIndex: number,
  heroSeat: number,
  total: number,
): { left: string; top: string } {
  const rel = (seatIndex - heroSeat + total) % total;
  const angleDeg = 90 + rel * (360 / total);
  const angleRad = (angleDeg * Math.PI) / 180;
  const rx = 42;
  const ry = 38;
  const left = 50 + rx * Math.cos(angleRad);
  const top = 50 + ry * Math.sin(angleRad);
  return { left: `${left}%`, top: `${top}%` };
}
