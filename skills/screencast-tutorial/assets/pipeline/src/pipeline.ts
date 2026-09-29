/**
 * Pipeline CLI. Three stages, always in this order:
 *
 *   1. audio   synthesise narration  (cheap, cached, no browser)
 *   2. record  capture the browser  (expensive, gated)
 *   3. merge   cut + mix + concat    (cheap, ffmpeg only)
 *
 * Audio comes first on purpose: the recorder needs exact narration durations to
 * size each hold, which is what keeps the merge from time-stretching.
 *
 *   npx ts-node src/pipeline.ts --list
 *   npx ts-node src/pipeline.ts --script my-tutorial
 *   npx ts-node src/pipeline.ts --all
 *   npx ts-node src/pipeline.ts --validate [--script X]
 *   npx ts-node src/pipeline.ts --audio-only | --record-only | --merge-only
 *   npx ts-node src/pipeline.ts --upload [--script X] [--privacy unlisted]
 */
import 'dotenv/config'
import * as fs from 'fs'
import * as path from 'path'
import { execSync } from 'child_process'
import type { AudioResult, TutorialScript } from './types'
import { audioPathFor, ensureAudio, getAudioDurationMs } from './audio'
import { recordScript, validateScript } from './record'
import { mergeScript } from './merge'
const ROOT = process.cwd()
const SCRIPTS_DIR = path.join(ROOT, 'scripts')

function ffprobeMs(file: string): number {
  try {
    return getAudioDurationMs(file)
  } catch {
    return 0
  }
}

/** Load every script JSON under scripts/, sorted by filename for a stable order. */
export function loadAllScripts(): TutorialScript[] {
  if (!fs.existsSync(SCRIPTS_DIR)) return []
  const out: TutorialScript[] = []
  const walk = (dir: string) => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
      const p = path.join(dir, entry.name)
      if (entry.isDirectory()) walk(p)
      else if (entry.name.endsWith('.json')) {
        const script = JSON.parse(fs.readFileSync(p, 'utf-8')) as TutorialScript
        script.__file = p
        out.push(script)
      }
    }
  }
  walk(SCRIPTS_DIR)
  return out
}

export function loadScript(id: string): TutorialScript {
  const match = loadAllScripts().find((s) => s.id === id)
  if (!match) {
    throw new Error(`No script with id "${id}". Available:\n  ${loadAllScripts().map((s) => s.id).join('\n  ')}`)
  }
  return match
}

/** Re-collect narration results from disk so merge can run standalone. */
function audioFromDisk(script: TutorialScript): AudioResult[] {
  return script.segments.map((seg) => {
    const p = audioPathFor(script.id, seg.id)
    return { segmentId: seg.id, audioPath: fs.existsSync(p) ? p : '', durationMs: fs.existsSync(p) ? ffprobeMs(p) : 0 }
  })
}

/** Merge an existing capture. Picks the newest webm that has timings. */
function mergeExisting(script: TutorialScript): string {
  const rawDir = path.join(ROOT, 'output', 'raw', script.id)
  if (!fs.existsSync(rawDir)) throw new Error(`No recording for ${script.id} — run --record-only first`)
  const webms = fs
    .readdirSync(rawDir)
    .filter((f) => f.endsWith('.webm') && fs.existsSync(path.join(rawDir, f.replace('.webm', '-timings.json'))))
    .map((f) => ({ f, mtime: fs.statSync(path.join(rawDir, f)).mtimeMs }))
    .sort((a, b) => b.mtime - a.mtime)
  if (!webms.length) throw new Error(`No webm with timings in ${rawDir}`)
  const videoPath = path.join(rawDir, webms[0].f)
  const timings = JSON.parse(fs.readFileSync(videoPath.replace('.webm', '-timings.json'), 'utf-8'))
  return mergeScript(script, { videoPath, timings }, audioFromDisk(script))
}

async function runFull(script: TutorialScript): Promise<string> {
  console.log(`\n=== ${script.id} — ${script.title} ===`)
  console.log('[1/3] narration')
  await ensureAudio(script)
  console.log('[2/3] record')
  const recorded = await recordScript(script)
  console.log('[3/3] merge')
  return mergeScript(script, recorded, audioFromDisk(script))
}

const HELP = `
screencast-tutorial pipeline

  --list                list discovered scripts
  --script <id>         run one script end-to-end (audio -> record -> merge)
  --all                 run every script in scripts/
  --validate            dry-run selectors against the live app, no recording
  --audio-only          synthesise narration only
  --record-only         record only (narration must already exist)
  --merge-only          re-merge existing captures (no browser)
  --upload              publish output/final to YouTube
  --auth-youtube        one-time OAuth for uploads
  --privacy <status>    unlisted | private | public
  --force               re-upload even if already published

Env:
  STRICT_GATES=true     abort a take when a settle gate fails (default: log and continue)
  PLAYWRIGHT_HEADLESS=false   watch the recording live
`

async function main(): Promise<void> {
  const args = process.argv.slice(2)
  const has = (f: string) => args.includes(f)
  const val = (f: string) => {
    const i = args.indexOf(f)
    return i !== -1 ? args[i + 1] : undefined
  }

  const target = val('--script')
  const scripts = target ? [loadScript(target)] : loadAllScripts()

  if (has('--list')) {
    for (const s of scripts) console.log(`  ${s.id.padEnd(28)} ${s.title}`)
    return
  }
  if (has('--auth-youtube')) {
    const { authorize } = await import('./upload')
    await authorize()
    return
  }
  if (has('--upload')) {
    const { uploadAll } = await import('./upload')
    await uploadAll({ targetScript: target, force: has('--force'), privacy: val('--privacy') })
    return
  }

  if (has('--validate')) {
    const results = []
    for (const s of scripts) results.push(await validateScript(s))
    const failed = results.filter((r) => !r.ok)
    console.log(`\n[validate] ${results.length - failed.length}/${results.length} PASS`)
    for (const f of failed) {
      console.log(`\n  FAIL ${f.scriptId}`)
      for (const m of f.failures) console.log(`    - ${m}`)
    }
    if (failed.length) process.exitCode = 1
    return
  }

  if (has('--audio-only')) {
    for (const s of scripts) await ensureAudio(s)
    return
  }
  if (has('--record-only')) {
    for (const s of scripts) await recordScript(s)
    return
  }
  if (has('--merge-only')) {
    for (const s of scripts) {
      try {
        mergeExisting(s)
      } catch (err) {
        console.error(`  [fail] ${s.id}: ${(err as Error).message}`)
      }
    }
    return
  }

  if (target || has('--all')) {
    if (!scripts.length) {
      console.error('No scripts found. Put JSON files in scripts/ (see references/script-schema.md).')
      process.exitCode = 1
      return
    }
    const produced: string[] = []
    for (const s of scripts) {
      try {
        produced.push(await runFull(s))
      } catch (err) {
        console.error(`\n  [fail] ${s.id}: ${(err as Error).message.split('\n')[0]}`)
      }
    }
    console.log(`\n[done] ${produced.length}/${scripts.length} produced`)
    for (const p of produced) console.log(`  ${p}`)
    return
  }

  console.log(HELP)
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
