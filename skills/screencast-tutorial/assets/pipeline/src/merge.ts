/**
 * Merge. Turns one continuous recording + per-segment narration into a final
 * MP4, without ever time-stretching the video.
 *
 *   cut window  = [narrationStart - lead .. narrationStart + narration + tail]
 *   lead        = min(narrationStart - start, MAX_LEAD_MS)   // silent lead-in
 *
 * Because the recorder holds for narration + tail, the cut is always
 * lead + narration long and the video plays at native speed. If a clip came up
 * short (crash, aborted hold), the last frame is freeze-padded with `tpad`
 * rather than slowing footage down: visible jank beats slow-motion desync.
 *
 * Cuts are re-encoded, not stream-copied. VFR webm + `-c:v copy` drifts, so
 * segment boundaries would land off the wall-clock timings.
 */
import * as fs from 'fs'
import * as path from 'path'
import { execSync } from 'child_process'
import type { AudioResult, RecordResult, TutorialScript } from './types'

const SEGMENTS_DIR = path.join(process.cwd(), 'output', 'segments')
const FINAL_DIR = path.join(process.cwd(), 'output', 'final')

/** Cap the un-narrated action phase so a slow spinner does not eat the clip. */
const MAX_LEAD_MS = Number(process.env.MAX_LEAD_MS ?? 2500)
const TAIL_MS = 1200

function ffmpeg(cmd: string, quiet = true): void {
  execSync(`ffmpeg -y ${cmd}`, { stdio: quiet ? 'pipe' : 'inherit' })
}

/** ms -> seconds string for ffmpeg. */
const s = (ms: number): string => (ms / 1000).toFixed(3)

export function mergeScript(script: TutorialScript, record: RecordResult, audio: AudioResult[]): string {
  fs.mkdirSync(SEGMENTS_DIR, { recursive: true })
  fs.mkdirSync(FINAL_DIR, { recursive: true })

  const audioBy = new Map(audio.map((a) => [a.segmentId, a]))
  const timingBy = new Map(record.timings.map((t) => [t.segmentId, t]))
  const files: string[] = []

  for (const segment of script.segments) {
    const timing = timingBy.get(segment.id)
    const clip = audioBy.get(segment.id)

    if (!timing) {
      console.warn(`   [skip] no timing for ${segment.id}`)
      continue
    }
    if (!clip?.audioPath || clip.durationMs <= 0) {
      console.warn(`   [skip] no narration audio for ${segment.id}`)
      continue
    }

    const rawCut = path.join(SEGMENTS_DIR, `${script.id}__${segment.id}__raw.mp4`)
    const outSeg = path.join(SEGMENTS_DIR, `${script.id}__${segment.id}.mp4`)

    // Narration trails the action by `lead` seconds of silence, not the reverse.
    const rawLead = Math.max(0, timing.narrationStartMs - timing.startMs)
    const leadMs = Math.min(rawLead, MAX_LEAD_MS)

    const startSec = timing.narrationStartMs - leadMs
    const endSec = Math.min(timing.endMs, timing.narrationStartMs + clip.durationMs + TAIL_MS)
    const cutSec = endSec - startSec
    const targetSec = leadMs + clip.durationMs + TAIL_MS
    if (cutSec <= 0) {
      console.warn(`   [skip] zero-duration cut for ${segment.id}`)
      continue
    }

    const padMs = Math.max(0, Math.round(targetSec - cutSec))
    if (padMs > 0) {
      console.warn(
        `   [pad] ${segment.id}: cut ${cutSec.toFixed(2)}s < needed ${targetSec.toFixed(2)}s — freeze last frame ${padMs}ms`,
      )
    }

    console.log(
      `   -> ${segment.id}: cut=${targetSec.toFixed(2)}s lead=${s(leadMs)}s narration=${s(clip.durationMs)}s`,
    )

    ffmpeg(
      `-ss ${s(startSec)} -to ${s(endSec)} -i "${record.videoPath}" ` +
        `-i "${clip.audioPath}" ` +
        `-filter_complex ` +
        `"[0:v]tpad=stop_mode=clone:stop_duration=${s(padMs)},fps=30,format=yuv420p[v];` +
        `[1:a]adelay=${leadMs}:all=1,apad,loudnorm=I=-16:TP=-1.5:LRA=11[a]" ` +
        `-map "[v]" -map "[a]" -t ${s(targetSec)} ` +
        `-c:v libx264 -preset fast -crf 23 -c:a aac -b:a 128k -ar 44100 "${rawCut}"`,
    )
    fs.renameSync(rawCut, outSeg)
    files.push(outSeg)
  }

  if (!files.length) throw new Error('No segments merged — nothing to concatenate')

  const finalPath = path.join(FINAL_DIR, `${script.id}.mp4`)
  const listPath = path.join(SEGMENTS_DIR, `${script.id}__filelist.txt`)
  fs.writeFileSync(
    listPath,
    files.map((f) => `file '${f.replace(/'/g, "'\\''")}'`).join('\n'),
    'utf-8',
  )

  console.log(`\n[concat] ${files.length} segments -> ${finalPath}`)
  ffmpeg(
    `-f concat -safe 0 -i "${listPath}" -c:v libx264 -preset fast -crf 22 -c:a aac -b:a 128k "${finalPath}"`,
    false,
  )
  fs.unlinkSync(listPath)
  console.log(`[done] ${finalPath}`)
  return finalPath
}
