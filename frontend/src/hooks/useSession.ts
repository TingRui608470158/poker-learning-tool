import { useCallback, useEffect, useState } from "react";
import * as api from "../api/client";
import type { HealthResponse, LearningUIState } from "../types/game";
import type { SettingsValues } from "../components/SettingsSidebar";

const DEFAULT_SETTINGS: SettingsValues = {
  numPlayers: 2,
  learningMode: "full",
  gtoStackBb: 25,
};

const HERO_SEAT = 0;

export function useSession() {
  const [settings, setSettings] = useState<SettingsValues>(DEFAULT_SETTINGS);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [state, setState] = useState<LearningUIState | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [initLoading, setInitLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [coachLoading, setCoachLoading] = useState(false);
  const [coachError, setCoachError] = useState<string | null>(null);

  useEffect(() => {
    api.fetchHealth().then(setHealth).catch(() => {
      setHealth({ status: "error", ollama_reachable: false, dqn_available: false });
    });
  }, []);

  const run = useCallback(async (fn: () => Promise<LearningUIState>) => {
    setBusy(true);
    try {
      const next = await fn();
      setState(next);
      return next;
    } finally {
      setBusy(false);
    }
  }, []);

  const newSession = useCallback(async () => {
    setCoachError(null);
    setCoachLoading(false);
    setLoadError(null);
    setInitLoading(true);
    try {
      const resp = await api.createSession({
        num_players: settings.numPlayers,
        hero_seat: HERO_SEAT,
        learning_mode: settings.learningMode,
        gto_stack_bb:
          settings.learningMode === "preflop_gto" ? settings.gtoStackBb : null,
      });
      setSessionId(resp.session_id);
      setState(resp.state);
      return resp.state;
    } catch (err) {
      const message = err instanceof Error ? err.message : "建立牌局失敗";
      setLoadError(message);
      setSessionId(null);
      setState(null);
      return null;
    } finally {
      setInitLoading(false);
    }
  }, [settings]);

  const requestReview = useCallback(async () => {
    if (!sessionId || !state || state.phase !== "hand_over") return;
    setCoachLoading(true);
    setCoachError(null);
    try {
      const next = await api.analyze(sessionId);
      setState(next);
      return next;
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "無法取得小六點評";
      setCoachError(message);
      return null;
    } finally {
      setCoachLoading(false);
    }
  }, [sessionId, state]);

  const handleAction = useCallback(
    async (index: number) => {
      if (!sessionId) return;
      await run(() => api.submitAction(sessionId, index));
    },
    [sessionId, run],
  );

  const handleNewHand = useCallback(async () => {
    if (!sessionId) {
      await newSession();
      return;
    }
    setCoachError(null);
    await run(() => api.startHand(sessionId));
  }, [sessionId, newSession, run]);

  return {
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
  };
}
