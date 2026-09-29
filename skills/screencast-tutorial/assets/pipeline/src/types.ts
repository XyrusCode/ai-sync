/**
 * Script/action schema for the screencast tutorial pipeline.
 *
 * A *script* is one video: an ordered list of segments. A *segment* is one
 * narration beat plus the actions that put the described UI on screen.
 *
 * Nothing here is app-specific. App facts live in `config/app.config.json`.
 */

/** Every primitive the recorder can drive in the browser. */
export type Action =
  | { type: 'navigate'; url: string }
  | { type: 'click'; selector: string; description?: string }
  | { type: 'fill'; selector: string; value: string; label?: string }
  | { type: 'select'; selector: string; value: string }
  | { type: 'wait'; ms: number }
  | { type: 'scroll'; direction: 'up' | 'down'; amount?: number }
  | { type: 'hover'; selector: string }
  | { type: 'press'; key: string }
  | { type: 'waitForSelector'; selector: string; timeout?: number; state?: 'attached' | 'detached' | 'visible' | 'hidden' }
  /** Annotation only: records a step in the log that has no browser effect (API call, background job). */
  | { type: 'note'; description: string }

export interface Segment {
  /** Stable slug. Also the audio/segment filename, so never rename after recording. */
  id: string
  /** Spoken narration. Drives the segment length; 15-25s reads well. */
  narrator: string
  actions: Action[]
  /**
   * REQUIRED. Selector identifying the UI this segment narrates. Narration
   * only starts once it is visible, so the speaker describes the settled screen
   * instead of racing ahead of the click.
   */
  readySelector: string
  /** Extra ms held after narration (breathing room before the next cut). */
  holdAfterMs?: number
}

export interface TutorialScript {
  id: string
  title: string
  /** Key into `audiences` in app.config.json. Decides baseUrl + auth strategy. */
  audience: string
  /** Overrides the audience's appBaseUrl. Rarely needed. */
  baseUrl?: string
  segments: Segment[]
  /** true for videos that intentionally show logged-out state (login walkthroughs). */
  skipAuth?: boolean
  /** YouTube description, used by --upload. */
  description?: string
  /** Set by the loader; not authored by hand. */
  __file?: string
}

export interface SegmentTiming {
  segmentId: string
  /** Start of the on-camera action phase. */
  startMs: number
  /** Instant the described UI settled; narration begins here. */
  narrationStartMs: number
  endMs: number
}

export interface RecordResult {
  videoPath: string
  timings: SegmentTiming[]
}

export interface AudioResult {
  segmentId: string
  audioPath: string
  durationMs: number
}

export interface ValidationResult {
  scriptId: string
  ok: boolean
  failures: string[]
}
