import { useEffect, useRef } from "react";
import { ActionBar } from "./components/ActionBar";
import { ActionTimeline } from "./components/ActionTimeline";
import { RightSidebar } from "./components/RightSidebar";
import { GameStatusBar } from "./components/GameStatusBar";
import { TurnBanner } from "./components/TurnBanner";
import { SettingsSidebar } from "./components/SettingsSidebar";
import { OvalPokerTable } from "./components/table/OvalPokerTable";
import { useSession } from "./hooks/useSession";

export default function App() {
  const {
    settings,
    setSettings,
    sessionId,
    state,
    health,
    busy,
    initLoading,
    loadError,
    coachLoading,
    coachError,
    newSession,
    handleAction,
    handleNewHand,
    requestReview,
  } = useSession();

  const bootstrapped = useRef(false);

  useEffect(() => {
    if (bootstrapped.current || sessionId || initLoading) return;
    bootstrapped.current = true;
    void newSession();
  }, [sessionId, initLoading, newSession]);

  return (
    <div className="flex min-h-screen flex-col bg-[#0a1612]">
      <header className="shrink-0 border-b border-white/10 bg-black/25">
        <div className="flex w-full items-center justify-between px-4 py-3 lg:px-6">
          <div>
            <h1 className="text-lg font-bold text-[#fefae0]">Poker Learning</h1>
            <p className="text-xs text-white/40">真實牌桌 · 翻前位置 · 小六視角</p>
          </div>
          {state && (
            <p className="text-right text-xs tabular-nums text-white/35">
              {state.view.num_players} 人桌
            </p>
          )}
        </div>
      </header>

      <main className="min-h-0 flex-1 w-full px-3 py-4 sm:px-4 lg:px-6 lg:py-5">
        {!state ? (
          <div className="mx-auto max-w-md rounded-2xl border border-white/10 bg-white/[0.03] p-8 text-center">
            {loadError ? (
              <>
                <p className="font-medium text-red-300">無法載入牌局</p>
                <p className="mt-3 text-left text-sm text-red-200/80">{loadError}</p>
                <button
                  type="button"
                  onClick={() => {
                    bootstrapped.current = false;
                    void newSession();
                  }}
                  className="mt-4 rounded-xl bg-accent px-6 py-2 text-sm font-bold text-felt-dark"
                >
                  重試
                </button>
              </>
            ) : (
              <p className="text-white/60">
                {initLoading ? "正在建立牌局…" : "載入中…"}
              </p>
            )}
          </div>
        ) : (
          <div className="grid h-full grid-cols-1 gap-4 xl:grid-cols-[minmax(220px,260px)_minmax(0,1fr)_minmax(300px,380px)] xl:items-stretch">
            <aside className="order-1 xl:sticky xl:top-4 xl:self-start">
              <SettingsSidebar
                values={settings}
                health={health}
                busy={busy}
                onChange={setSettings}
                onNewSession={() => void newSession()}
              />
            </aside>

            <div className="order-2 min-w-0 space-y-4">
              <GameStatusBar
                stage={state.view.stage}
                phase={state.phase}
                view={state.view}
              />

              <OvalPokerTable view={state.view} heroSeat={state.hero_seat} />

              <TurnBanner
                phase={state.phase}
                view={state.view}
                heroSeat={state.hero_seat}
              />

              <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <ActionBar
                  phase={state.phase}
                  learningMode={state.learning_mode}
                  legalActions={state.view.legal_actions}
                  preflopStrategy={state.preflop_strategy}
                  busy={busy}
                  coachLoading={coachLoading}
                  hasAnalysis={Boolean(state.review?.sections.length)}
                  onAction={handleAction}
                  onNewHand={handleNewHand}
                  onRequestReview={() => void requestReview()}
                />
              </div>

              <ActionTimeline lines={state.view.action_log ?? []} />
            </div>

            <aside className="order-3 min-h-[360px] xl:sticky xl:top-4 xl:min-h-0 xl:self-stretch">
              <RightSidebar
                learningMode={state.learning_mode}
                phase={state.phase}
                review={state.review}
                handEventCount={state.hand_event_count}
                coachLoading={coachLoading}
                coachError={coachError}
                preflopStrategy={state.preflop_strategy}
                numPlayers={state.view.num_players}
              />
            </aside>
          </div>
        )}
      </main>
    </div>
  );
}
