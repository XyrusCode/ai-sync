/**
 * YouTube publishing. Uses the resumable upload path so a 3 MB tutorial or a
 * 2 GB screencast both survive a flaky connection.
 *
 * Setup: Google Cloud Console -> enable YouTube Data API v3 -> OAuth 2.0
 * "Desktop app" client -> put client id/secret in .env -> run --auth-youtube
 * once. Tokens land in output/youtube-token.json (git-ignored).
 */
import 'dotenv/config'
import * as fs from 'fs'
import * as path from 'path'
import { createInterface } from 'node:readline'
import { google, youtube_v3 } from 'googleapis'
import { loadAllScripts, loadScript } from './pipeline'
import { loadConfig } from './config'
import type { TutorialScript } from './types'

const TOKEN_PATH = path.join(process.cwd(), 'output', 'youtube-token.json')
const UPLOAD_LOG = path.join(process.cwd(), 'output', 'uploads.json')
const FINAL_DIR = path.join(process.cwd(), 'output', 'final')
const SCOPE = 'https://www.googleapis.com/auth/youtube.upload'

type Privacy = 'unlisted' | 'private' | 'public'

/**
 * googleapis ships types that lag the runtime API here: the resumable-upload
 * option and the playlistItems snippet shape are both accepted by the library
 * but missing from its .d.ts. These casts are the narrowest way to say so.
 */
type PlaylistSnippet = { playlistId: string; resourceId: string }

function oauthClient(): InstanceType<typeof google.auth.OAuth2> {
  const { YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_OAUTH_PORT } = process.env
  if (!YOUTUBE_CLIENT_ID || !YOUTUBE_CLIENT_SECRET) {
    throw new Error('Set YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET in .env, then run --auth-youtube')
  }
  return new google.auth.OAuth2(
    YOUTUBE_CLIENT_ID,
    YOUTUBE_CLIENT_SECRET,
    `http://localhost:${YOUTUBE_OAUTH_PORT ?? 4173}`,
  )
}

export async function authorize(): Promise<void> {
  const auth = oauthClient()
  const url = auth.generateAuthUrl({ access_type: 'offline', scope: [SCOPE] })
  console.log('Open this URL, approve access, then paste the code here:\n')
  console.log(url)

  const rl = createInterface({ input: process.stdin, output: process.stdout })
  const code = await new Promise<string>((resolve) => rl.question('code: ', resolve))
  rl.close()

  const { tokens } = await auth.getToken(code.trim())
  fs.mkdirSync(path.dirname(TOKEN_PATH), { recursive: true })
  fs.writeFileSync(TOKEN_PATH, JSON.stringify(tokens, null, 2), 'utf-8')
  console.log(`[youtube] authorized. Token -> ${TOKEN_PATH}`)
}

async function youtubeClient() {
  if (!fs.existsSync(TOKEN_PATH)) {
    throw new Error(`No YouTube token at ${TOKEN_PATH}. Run: npx ts-node src/pipeline.ts --auth-youtube`)
  }
  const auth = oauthClient()
  auth.setCredentials(JSON.parse(fs.readFileSync(TOKEN_PATH, 'utf-8')))
  return google.youtube({ version: 'v3', auth })
}

function readUploadLog(): Record<string, string> {
  try {
    return JSON.parse(fs.readFileSync(UPLOAD_LOG, 'utf-8'))
  } catch {
    return {}
  }
}

function descriptionFor(script: TutorialScript): string {
  return script.description ?? `${script.title}\n\nRecorded from the live app.`
}

export async function uploadAll(opts: {
  targetScript?: string
  force?: boolean
  privacy?: string
}): Promise<void> {
  const scripts = opts.targetScript ? [loadScript(opts.targetScript)] : loadAllScripts()
  const log = readUploadLog()
  const yt = await youtubeClient()
  const privacy = (opts.privacy ?? loadConfig().upload?.privacy ?? 'unlisted') as Privacy
  const playlistId = loadConfig().upload?.playlistId

  for (const script of scripts) {
    const file = path.join(FINAL_DIR, `${script.id}.mp4`)
    if (!fs.existsSync(file)) {
      console.warn(`[youtube] skip ${script.id}: no final video at ${file}`)
      continue
    }
    if (log[script.id] && !opts.force) {
      console.log(`[youtube] skip ${script.id}: already uploaded (${log[script.id]})`)
      continue
    }

    console.log(`[youtube] uploading ${script.id} (${privacy})`)
    const res = await yt.videos.insert(
      {
        part: ['snippet', 'status'],
        requestBody: {
          snippet: { title: script.title, description: descriptionFor(script) },
          status: { privacyStatus: privacy },
        },
        media: { body: fs.createReadStream(file), mimeType: 'video/mp4' },
      },
      {
        resumable: true,
        onUploadProgress: (e: { loaded?: number }) => process.stdout.write(`\r   ${e.loaded ?? 0} bytes`),
      } as never,
    )
    process.stdout.write('\n')

    const videoId = (res.data as youtube_v3.Schema$Video).id
    if (!videoId) throw new Error(`Upload returned no video id for ${script.id}`)
    log[script.id] = videoId
    console.log(`[youtube] ${script.id} -> https://youtu.be/${videoId}`)

    if (playlistId) {
      await yt.playlistItems.insert({
        part: ['snippet'],
        requestBody: { snippet: { playlistId, resourceId: videoId } as PlaylistSnippet } as never,
      })
    }
  }

  fs.mkdirSync(path.dirname(UPLOAD_LOG), { recursive: true })
  fs.writeFileSync(UPLOAD_LOG, JSON.stringify(log, null, 2), 'utf-8')
}
