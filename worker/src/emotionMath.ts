// Port of emotional_state.py compute_adjusted_dopamine / compute_adjusted_survival.
// Same constants, same math; time is measured from ISO timestamps.

import { STIMULI_WEIGHTS } from "./stimuliTags";

const DECAY_RATE = 0.003;
const ALPHA = 0.3;

function minutesBetween(lastUpdated: string, now: Date): number {
  return (now.getTime() - new Date(lastUpdated).getTime()) / 60000;
}

export function computeAdjustedDopamine(
  current: number,
  stimuliTags: Record<string, number>,
  lastUpdated: string,
  now = new Date()
): number {
  let delta = 0;
  for (const [stimuli, score] of Object.entries(stimuliTags)) {
    delta += score * (STIMULI_WEIGHTS[stimuli]?.dopamine ?? 0);
  }
  const decayed = current * Math.exp(-DECAY_RATE * minutesBetween(lastUpdated, now));
  const updated = decayed + delta;
  const stabilized = (1 - ALPHA) * updated + ALPHA * decayed;
  return Math.max(0, Math.min(1, stabilized));
}

export function computeAdjustedSurvival(
  current: number,
  stimuliTags: Record<string, number>,
  lastUpdated: string,
  now = new Date()
): number {
  let delta = 0;
  for (const [stimuli, score] of Object.entries(stimuliTags)) {
    delta += score * (STIMULI_WEIGHTS[stimuli]?.survival ?? 0);
  }
  const decayed = current * Math.exp(-DECAY_RATE * minutesBetween(lastUpdated, now));
  const updated = decayed + delta;
  const stabilized = (1 - ALPHA) * updated + ALPHA * decayed;
  return Math.max(0, Math.min(1, stabilized));
}
