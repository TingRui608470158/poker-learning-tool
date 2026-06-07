import type { HealthResponse, LearningMode } from "../types/game";
import { GTO_DEPTH_OPTIONS, LEARNING_MODE_LABELS } from "../types/game";

export interface SettingsValues {
  numPlayers: number;
  learningMode: LearningMode;
  gtoStackBb: number;
}

interface SettingsSidebarProps {
  values: SettingsValues;
  health: HealthResponse | null;
  busy: boolean;
  onChange: (values: SettingsValues) => void;
  onNewSession: () => void;
}

const MODES: LearningMode[] = ["full", "preflop_gto", "coach_review"];

export function SettingsSidebar({
  values,
  health,
  busy,
  onChange,
  onNewSession,
}: SettingsSidebarProps) {
  const isPreflopGto = values.learningMode === "preflop_gto";

  return (
    <div className="flex h-full flex-col rounded-2xl border border-white/10 bg-white/[0.03]">
      <div className="border-b border-white/10 px-4 py-3">
        <h2 className="text-sm font-semibold text-white/80">牌局設定</h2>
      </div>

      <div className="space-y-4 px-4 py-4 text-sm">
        <fieldset className="space-y-2">
          <legend className="text-white/45">學習模式</legend>
          {MODES.map((mode) => (
            <label
              key={mode}
              className="flex cursor-pointer items-center gap-2 text-xs text-white/70"
            >
              <input
                type="radio"
                name="learningMode"
                value={mode}
                checked={values.learningMode === mode}
                disabled={busy}
                onChange={() =>
                  onChange({
                    ...values,
                    learningMode: mode,
                    numPlayers: mode === "preflop_gto" ? 2 : values.numPlayers,
                  })
                }
                className="accent-accent"
              />
              {LEARNING_MODE_LABELS[mode]}
            </label>
          ))}
        </fieldset>

        <label className="block">
          <span className="text-white/45">打牌人數 · {values.numPlayers}</span>
          <input
            type="range"
            min={2}
            max={9}
            step={1}
            value={values.numPlayers}
            disabled={busy || isPreflopGto}
            onChange={(e) =>
              onChange({ ...values, numPlayers: Number(e.target.value) })
            }
            className="mt-1 w-full accent-accent disabled:opacity-40"
          />
          <div className="mt-1 flex justify-between text-[10px] text-white/30">
            <span>2</span>
            <span>6</span>
            <span>9</span>
          </div>
          {isPreflopGto && (
            <p className="mt-1 text-[10px] text-white/35">翻前策略模式固定 2 人桌</p>
          )}
        </label>

        {isPreflopGto && (
          <label className="block">
            <span className="text-white/45">GTO 練習深度 · {values.gtoStackBb}bb</span>
            <select
              value={values.gtoStackBb}
              disabled={busy}
              onChange={(e) =>
                onChange({ ...values, gtoStackBb: Number(e.target.value) })
              }
              className="mt-1 w-full rounded-lg border border-white/15 bg-black/30 px-2 py-2 text-sm text-[#fefae0]"
            >
              {GTO_DEPTH_OPTIONS.map((d) => (
                <option key={d} value={d}>
                  {d} bb
                </option>
              ))}
            </select>
          </label>
        )}

        <p className="text-xs text-white/35">你固定坐在畫面下方，其餘座位為 RL 對手</p>

        <p className="text-xs leading-relaxed text-white/35">
          {isPreflopGto
            ? "翻前策略模式：固定籌碼深度，右側顯示 GTO 表與 EV。"
            : "每手重新發牌並分配籌碼；各座位獨立 1～100bb，與上一手無關"}
        </p>

        <button
          type="button"
          disabled={busy}
          onClick={onNewSession}
          className="w-full rounded-xl border border-accent/40 py-2 text-sm font-semibold text-accent transition hover:bg-accent/10 disabled:opacity-50"
        >
          套用並新一局
        </button>

        {health && (
          <p className="text-xs text-white/35">
            Ollama {health.ollama_reachable ? "✓" : "✗"}
          </p>
        )}
      </div>
    </div>
  );
}
