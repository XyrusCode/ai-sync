/**
 * Narration synthesis. Free Microsoft Edge neural voices via `msedge-tts`
 * (pure Node, no Python, no API key). The pipeline is audio-first: this runs
 * BEFORE recording so exact narration durations are known when holds are sized.
 *
 * Stage order is the whole point. See references/architecture.md.
 */
import * as fs from 'fs'
import * as path from 'path'
import { execSync } from 'child_process'
import { Readable } from 'stream'
import { MsEdgeTTS, OUTPUT_FORMAT } from 'msedge-tts'
import type { TutorialScript, AudioResult } from './types'
import { ttsFor } from './config'

const OUTPUT_DIR = path.join(process.cwd(), 'output', 'audio')

export function getAudioDurationMs(filePath: string): number {
  try {
    const out = execSync(
      `ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "${filePath}"`,
      { encoding: 'utf-8' },
    ).trim()
    return Math.round(parseFloat(out) * 1000)
  } catch {
    return 0
  }
}

export function audioPathFor(scriptId: string, segmentId: string): string {
  return path.join(OUTPUT_DIR, `${scriptId}__${segmentId}.mp3`)
}

/** One shared WebSocket per process; setMetadata is idempotent. */
let sharedClient: MsEdgeTTS | null = null

async function getClient(): Promise<MsEdgeTTS> {
  if (!sharedClient) {
    sharedClient = new MsEdgeTTS({ enableLogger: false })
    // setMetadata(voice, format) — prosody is applied per-utterance, not here.
    await sharedClient.setMetadata(ttsFor().voice, OUTPUT_FORMAT.AUDIO_24KHZ_48KBITRATE_MONO_MP3)
  }
  return sharedClient
}

const MAX_RETRIES = Number(process.env.TTS_MAX_RETRIES ?? 4)
const RETRY_DELAY_MS = Number(process.env.TTS_RETRY_DELAY_MS ?? 2000)

async function resetClient(): Promise<void> {
  try {
    await sharedClient?.close()
  } catch {
    /* ignore */
  }
  sharedClient = null
}

/**
 * The Edge TTS websocket drops mid-stream fairly often, especially on bursts.
 * Retry with a fresh client and linear backoff; treat a tiny buffer as a
 * dropped stream too, since it otherwise writes a corrupt mp3 that later reads
 * as "cached" forever.
 */
export async function synthesizeToFile(text: string, outPath: string): Promise<void> {
  for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    try {
      const client = await getClient()
      const result = client.toStream(text)
      const chunks: Buffer[] = []
      for await (const chunk of result.audioStream as Readable) {
        chunks.push(chunk as Buffer)
      }
      const buf = Buffer.concat(chunks)
      if (buf.length < 512) throw new Error(`TTS produced suspiciously small audio (${buf.length} bytes)`)
      fs.writeFileSync(outPath, buf)
      return
    } catch (err) {
      const msg = (err as Error).message
      const retryable = /stream closed|websocket|econnreset|socket hang up|small audio|timeout/i.test(msg)
      if (attempt < MAX_RETRIES && retryable) {
        process.stdout.write(`   [tts retry ${attempt}/${MAX_RETRIES}] `)
        await resetClient()
        await new Promise((r) => setTimeout(r, RETRY_DELAY_MS * attempt))
        continue
      }
      throw err
    }
  }
}

/**
 * Ensure every segment has narration. Cached mp3s are reused (a cache hit only
 * counts when ffprobe reports a real duration), so re-recording a script is
 * fast and narration cost is paid once. Delete the mp3 to re-synthesize.
 */
export async function ensureAudio(script: TutorialScript): Promise<AudioResult[]> {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true })
  const results: AudioResult[] = []

  for (const segment of script.segments) {
    if (!segment.narrator.trim()) {
      results.push({ segmentId: segment.id, audioPath: '', durationMs: 0 })
      continue
    }

    const audioPath = audioPathFor(script.id, segment.id)

    if (fs.existsSync(audioPath)) {
      const durationMs = getAudioDurationMs(audioPath)
      if (durationMs > 0) {
        console.log(`   [cached] ${segment.id}: ${durationMs}ms`)
        results.push({ segmentId: segment.id, audioPath, durationMs })
        continue
      }
      fs.unlinkSync(audioPath) // corrupt cache entry, regenerate
    }

    process.stdout.write(`   [tts] ${segment.id}: `)
    await synthesizeToFile(segment.narrator, audioPath)
    console.log(`${getAudioDurationMs(audioPath)}ms`)
    results.push({ segmentId: segment.id, audioPath, durationMs: getAudioDurationMs(audioPath) })
  }

  return results
}
