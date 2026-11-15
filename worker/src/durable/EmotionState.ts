// EmotionState Durable Object: one per user, holding the dopamine/survival
// state and its history. Port of EmotionalStateManager plus the
// UserDopamineAndSurvival(UserDopamineAndSurvivalHistory) tables.

import { DurableObject } from "cloudflare:workers";
import { computeAdjustedDopamine, computeAdjustedSurvival } from "../emotionMath";
import type { Metrics, MetricsHistory } from "../prompts";

const DEFAULT_STATE: Metrics = {
  dopamine_user: 0.5,
  survival_user: 1.0,
  dopamine_ai: 0.5,
  survival_ai: 1.0,
};

interface StoredHistory extends MetricsHistory {}

export class EmotionState extends DurableObject {
  private async current(): Promise<Metrics> {
    const stored = await this.ctx.storage.get<Metrics>("current");
    if (stored) return stored;
    const initial = { ...DEFAULT_STATE, timestamp: new Date().toISOString() };
    await this.ctx.storage.put("current", initial);
    await this.appendHistory(initial);
    return initial;
  }

  private async appendHistory(m: Metrics): Promise<void> {
    const history = (await this.ctx.storage.get<StoredHistory>("history")) ?? {
      dopamine_user: [],
      survival_user: [],
      dopamine_ai: [],
      survival_ai: [],
      timestamps: [],
    };
    history.dopamine_user.push(m.dopamine_user);
    history.survival_user.push(m.survival_user);
    history.dopamine_ai.push(m.dopamine_ai);
    history.survival_ai.push(m.survival_ai);
    history.timestamps!.push(m.timestamp ?? new Date().toISOString());
    await this.ctx.storage.put("history", history);
  }

  async getCurrent(): Promise<Metrics> {
    return this.current();
  }

  async getHistory(): Promise<MetricsHistory> {
    await this.current();
    return (await this.ctx.storage.get<StoredHistory>("history"))!;
  }

  async recalculate(
    stimuliUser: Record<string, number>,
    stimuliAi: Record<string, number>
  ): Promise<Metrics> {
    const current = await this.current();
    const lastUpdated = current.timestamp ?? new Date().toISOString();
    const next: Metrics = {
      dopamine_user: computeAdjustedDopamine(current.dopamine_user, stimuliUser, lastUpdated),
      survival_user: computeAdjustedSurvival(current.survival_user, stimuliUser, lastUpdated),
      dopamine_ai: computeAdjustedDopamine(current.dopamine_ai, stimuliAi, lastUpdated),
      survival_ai: computeAdjustedSurvival(current.survival_ai, stimuliAi, lastUpdated),
      timestamp: new Date().toISOString(),
    };
    await this.ctx.storage.put("current", next);
    await this.appendHistory(next);
    return next;
  }
}
