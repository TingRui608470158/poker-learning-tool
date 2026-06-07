export type PlayerKind = "human" | "random" | "dqn";

export type Phase = "awaiting_next" | "awaiting_human_action" | "hand_over";

export interface StepRecord {
  actor_seat: number;
  action_label: string;
  action_log_line: string;
}

export interface SeatView {
  seat: number;
  kind: PlayerKind;
  hand: string[];
  stakes: number;
  chips_in_pot: number;
  hand_hidden: boolean;
  stack_remaining: number;
  starting_bb: number;
  stack_bb: number;
  is_dealer: boolean;
  is_hero: boolean;
  last_action_label: string | null;
  position_en: string;
  position_zh: string;
  angle_index: number;
}

export interface TableView {
  stage: string;
  pot: number;
  community_cards: string[];
  seats: SeatView[];
  big_blind: number;
  small_blind: number;
  num_players: number;
  dealer_seat: number;
  current_actor: number;
  legal_actions: string[];
  is_over: boolean;
  payoffs: number[] | null;
  result_message: string | null;
  action_log: string[] | null;
}

export type StreetId = "preflop" | "flop" | "turn" | "river";

export interface ReviewSection {
  street: StreetId;
  title: string;
  content: string;
}

export interface HandReview {
  sections: ReviewSection[];
}

export type LearningMode = "full" | "preflop_gto" | "coach_review";

export interface HandCell {
  hand: string;
  fold: number;
  call: number;
  raise: number;
  ev_bb: number;
  primary_action: string;
}

export interface ActionAdvice {
  action_index: number;
  label: string;
  ev_bb: number | null;
  gto_pct: number | null;
}

export interface PreflopStrategy {
  spot_label: string;
  hero_hand: string;
  actual_depth_bb: number;
  chart_depth_bb: number;
  hero_cell: HandCell;
  actions: ActionAdvice[];
  matrix: (HandCell | null)[][];
  disclaimer: string;
}

export interface LearningUIState {
  phase: Phase;
  view: TableView;
  review: HandReview | null;
  analysis: string | null;
  hero_seat: number;
  last_step: StepRecord | null;
  hand_event_count: number;
  learning_mode: LearningMode;
  preflop_strategy: PreflopStrategy | null;
}

export interface SessionCreateRequest {
  num_players: number;
  hero_seat: number;
  learning_mode?: LearningMode;
  gto_stack_bb?: number | null;
}

export const LEARNING_MODE_LABELS: Record<LearningMode, string> = {
  full: "完整學習",
  preflop_gto: "翻前策略",
  coach_review: "職業點評",
};

export const GTO_DEPTH_OPTIONS = [10, 25, 40, 100] as const;

export interface SessionCreateResponse {
  session_id: string;
  state: LearningUIState;
}

export interface HealthResponse {
  status: string;
  ollama_reachable: boolean;
  dqn_available: boolean;
}

export const KIND_LABELS: Record<PlayerKind, string> = {
  human: "真人",
  random: "RL 隨機",
  dqn: "RL DQN",
};

export function positionDisplay(en: string, zh: string): string {
  return `${en}（${zh}）`;
}
