/**
 * Recorder. Drives a real browser, performs each segment's actions, and
 * records the whole session as one continuous webm so cuts stay frame-accurate.
 *
 * The load-bearing idea: narration describes the SETTLED screen, so the recorder
 * measures two instants per segment, not one.
 *
 *   startMs          the clip starts here (on-camera action phase begins)
 *   narrationStartMs the described UI has painted; narration begins here
 *   endMs            clip ends
 *
 * The recorder holds the frame for narration + tail after narrationStartMs, so
 * the recorded window always covers lead-in + narration. That is what lets the
 * merge run at ratio 1.0 and never time-stretch (see merge.ts).
 */
import 'dotenv/config'
import * as fs from 'fs'
import * as path from 'path'
import { chromium, type Browser, type BrowserContext, type Page } from 'playwright'
import type { Action, RecordResult, SegmentTiming, TutorialScript, ValidationResult } from './types'
import { getAudioDurationMs, audioPathFor } from './audio'
import { prepareAuthenticatedContext, clearCachedToken } from './auth'
import { audienceFor, viewerFor } from './config'

const HEADLESS = process.env.PLAYWRIGHT_HEADLESS !== 'false'
const CHROMIUM_PATH = process.env.CHROMIUM_PATH || undefined
const RAW_DIR = path.join(process.cwd(), 'output', 'raw')

/** Tail held after narration ends, and the floor for any segment hold. */
const TAIL_MS = 1200
const MIN_HOLD_MS = 3500

export function baseUrlFor(script: TutorialScript): string {
  return (script.baseUrl ?? audienceFor(script.audience).appBaseUrl).replace(/\/$/, '')
}

function resolveUrl(url: string, baseUrl: string): string {
  if (url.startsWith('http://') || url.startsWith('https://')) return url
  return `${baseUrl}${url.startsWith('/') ? url : '/' + url}`
}

async function runAction(page: Page, action: Action, baseUrl: string): Promise<void> {
  const sel = 'selector' in action ? action.selector : ''
  switch (action.type) {
    case 'navigate':
      // 'commit' returns on first bytes. 'domcontentloaded' can hang when the
      // server is slow to finish JS chunks; content readiness is gated separately.
      await page.goto(resolveUrl(action.url, baseUrl), { waitUntil: 'commit' })
      await page.waitForTimeout(400)
      break
    case 'click':
      await page.locator(sel).first().click({ timeout: 20000 })
      break
    case 'fill':
      await page.locator(sel).first().fill(action.value, { timeout: 20000 })
      break
    case 'select':
      await page.locator(sel).first().selectOption(action.value, { timeout: 20000 })
      break
    case 'wait':
      await page.waitForTimeout(action.ms)
      break
    case 'scroll': {
      const delta = (action.amount ?? 400) * (action.direction === 'down' ? 1 : -1)
      await page.mouse.wheel(0, delta)
      break
    }
    case 'hover':
      await page.locator(sel).first().hover({ timeout: 10000 })
      break
    case 'press':
      await page.keyboard.press(action.key)
      break
    case 'waitForSelector':
      await page
        .locator(sel)
        .first()
        .waitFor({ state: action.state ?? 'visible', timeout: action.timeout ?? 15000 })
      break
    case 'note':
      console.log(`      [note] ${action.description}`)
      break
  }
}

/**
 * Block until the page has genuinely settled: app shell mounted, every
 * configured spinner gone, and (when given) the segment's readySelector
 * visible. Returns the list of gates that failed so callers can log loudly or
 * abort, rather than narrating over a loading screen.
 */
async function waitForSettled(
  page: Page,
  readySelector: string | undefined,
  audienceKey: string,
): Promise<string[]> {
  const failed: string[] = []
  const viewer = viewerFor()
  // Must be the SCRIPT's audience: a second role can have a different shell
  // (different root element, different spinner classes) on a different host.
  const shell = audienceFor(audienceKey).shell

  try {
    await page.waitForSelector(shell.readyRootSelector, { state: 'attached', timeout: viewer.shellTimeoutMs })
  } catch {
    failed.push(`shell root ${shell.readyRootSelector} never mounted`)
  }

  if (shell.spinnerSelectors.length) {
    try {
      // waitForFunction with a DOM snapshot: visible = offsetParent != null.
      await page.waitForFunction(
        ({ selectors }) => {
          for (const s of selectors) {
            for (const el of Array.from(document.querySelectorAll(s))) {
              const box = el as HTMLElement
              if (box.offsetParent !== null || getComputedStyle(box).position === 'fixed') return false
            }
          }
          return true
        },
        { selectors: shell.spinnerSelectors },
        { timeout: viewer.shellTimeoutMs },
      )
    } catch {
      failed.push(`spinner still visible after ${viewer.shellTimeoutMs / 1000}s (${shell.spinnerSelectors.join(', ')})`)
    }
  }

  if (readySelector) {
    try {
      await page.waitForSelector(readySelector, { state: 'visible', timeout: viewer.readyTimeoutMs })
    } catch {
      failed.push(`readySelector not visible after ${viewer.readyTimeoutMs / 1000}s: ${readySelector}`)
    }
  } else {
    // No readySelector: fall back to text-stability inside the shell root, so a
    // fast-rendering sidebar cannot satisfy the gate while content is still blank.
    try {
      await page.waitForFunction(
        ({ root }) => {
          const w = window as unknown as { __screencastLen?: number }
          const main = (root ? document.querySelector(root) : document.body) as HTMLElement | null
          const len = (main ?? document.body)?.innerText?.trim().length ?? 0
          const prev = w.__screencastLen ?? -1
          w.__screencastLen = len
          return len > 120 && len === prev
        },
        { root: shell.readyRootSelector },
        { timeout: viewer.readyTimeoutMs, polling: 800 },
      )
    } catch {
      failed.push('shell text never stabilised (sparse page or still loading)')
    }
  }

  return failed
}

async function attemptUiLogin(page: Page, script: TutorialScript): Promise<void> {
  const audience = audienceFor(script.audience)
  const login = audience.auth.uiLogin
  if (!login) throw new Error(`audience "${script.audience}" has no uiLogin block`)

  const baseUrl = baseUrlFor(script)
  await page.goto(`${baseUrl}${login.loginPath}`, { waitUntil: 'commit', timeout: 90000 })
  await page.waitForTimeout(500)

  await page.waitForSelector(login.identifierSelector, { timeout: 60000 })
  await page.locator(login.identifierSelector).first().fill(process.env.LOGIN_ID ?? '')
  await page.locator(login.passwordSelector).first().fill(process.env.LOGIN_PASSWORD ?? '')
  await page.locator(login.submitSelector).first().click()
}

/**
 * Log in via the UI with retries, and ASSERT success. A silently-failed login
 * used to produce a confident video of the login page. Success is "URL left
 * /login"; anything else retries, then throws so the caller can skip rather
 * than ship garbage.
 */
async function loginWithRetry(page: Page, script: TutorialScript, maxAttempts = 3): Promise<void> {
  const audience = audienceFor(script.audience)
  if (audience.auth.mode === 'none') return
  const loginPath = audience.auth.uiLogin?.loginPath ?? '/login'
  const urlTimeout = 150000

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      await attemptUiLogin(page, script)
      await page.waitForURL((u) => !u.pathname.includes(loginPath.split('?')[0]), {
        timeout: urlTimeout,
        waitUntil: 'commit',
      })
      console.log(`   [auth] UI login ok (attempt ${attempt})`)
      await page.waitForTimeout(1500)
      return
    } catch (err) {
      console.warn(
        `   [auth] UI login attempt ${attempt}/${maxAttempts} failed: ${(err as Error).message.split('\n')[0]}`,
      )
      if (attempt === maxAttempts) {
        throw new Error(`UI login failed for ${script.id} after ${maxAttempts} attempts — skipping rather than recording garbage`)
      }
      await page.waitForTimeout(2000)
    }
  }
}

interface Session {
  browser: Browser
  context: BrowserContext
  page: Page
  /** Wall-clock instant the page (and video capture) was created. ALL segment
   *  timings are measured from here so cuts line up with the webm timeline. */
  startEpoch: number
}

async function launchBrowser(record: boolean, script: TutorialScript): Promise<{ browser: Browser; context: BrowserContext; rawDir: string }> {
  const viewer = viewerFor()
  const browser = await chromium.launch({
    headless: HEADLESS,
    slowMo: Number(process.env.PLAYWRIGHT_SLOWMO ?? 0),
    executablePath: CHROMIUM_PATH,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-ipv6', '--disable-http2', '--autoplay-policy=no-user-gesture-required'],
  })

  let rawDir = ''
  if (record) {
    rawDir = path.join(RAW_DIR, script.id)
    fs.mkdirSync(rawDir, { recursive: true })
  }

  const context = await browser.newContext({
    viewport: { width: viewer.width, height: viewer.height },
    ...(record
      ? { recordVideo: { dir: rawDir, size: { width: viewer.width, height: viewer.height } } }
      : {}),
  })
  return { browser, context, rawDir }
}

/** Shared session setup: launch -> context -> page -> auth -> warm-up. */
async function createSession(script: TutorialScript, record: boolean): Promise<Session> {
  const { browser, context } = await launchBrowser(record, script)
  const page = await context.newPage()
  page.setDefaultNavigationTimeout(90000)

  // Video capture for this page starts now; every timing is relative to it.
  const startEpoch = Date.now()

  let injected = false
  if (!script.skipAuth) {
    injected = await prepareAuthenticatedContext(context, script)
    if (!injected) await loginWithRetry(page, script)
  }

  // Warm-up: a cold load fetches lazy chunks before content paints, so without
  // this the first segment opens on a blank screen. Land on the default route
  // and wait for real content.
  if (!script.skipAuth) {
    const audience = audienceFor(script.audience)
    try {
      await page.goto(`${baseUrlFor(script)}${audience.shell.defaultPath}`, { waitUntil: 'commit', timeout: 90000 })
    } catch {
      /* commit can time out on slow hosts; the settle gate below still runs */
    }
    const warmGates = await waitForSettled(page, undefined, script.audience)
    if (injected && warmGates.length) {
      // An injected token that never yields a shell is stale or mis-scoped.
      console.warn('   [auth] injected token produced no app shell — retrying with UI login')
      await context.close()
      await browser.close()
      return createSessionWithoutToken(script, record)
    }
    await page.waitForTimeout(1500)
  }

  return { browser, context, page, startEpoch }
}

/** Session with UI login only. Used when a cached token proves invalid. */
async function createSessionWithoutToken(script: TutorialScript, record: boolean): Promise<Session> {
  clearCachedToken(script.audience)
  const { browser, context } = await launchBrowser(record, script)
  const page = await context.newPage()
  page.setDefaultNavigationTimeout(90000)
  const startEpoch = Date.now()

  if (!script.skipAuth) await loginWithRetry(page, script)
  if (!script.skipAuth) {
    const audience = audienceFor(script.audience)
    try {
      await page.goto(`${baseUrlFor(script)}${audience.shell.defaultPath}`, { waitUntil: 'commit', timeout: 90000 })
    } catch {
      /* settle below */
    }
    await waitForSettled(page, undefined, script.audience)
    await page.waitForTimeout(1500)
  }
  return { browser, context, page, startEpoch }
}

export async function recordScript(script: TutorialScript): Promise<RecordResult> {
  fs.mkdirSync(RAW_DIR, { recursive: true })
  console.log(`\n[record] ${script.title}`)

  const { browser, context, page, startEpoch } = await createSession(script, true)
  const baseUrl = baseUrlFor(script)
  const timings: SegmentTiming[] = []
  const failures: string[] = []
  const STRICT = process.env.STRICT_GATES === 'true'

  for (const segment of script.segments) {
    console.log(`   -> ${segment.id}`)

    // Pre-roll (off-camera): run LEADING navigate/wait actions and settle before
    // the clip starts, so the merged segment opens on an already-painted page.
    let i = 0
    while (i < segment.actions.length) {
      const a = segment.actions[i]
      if (a.type === 'navigate' || a.type === 'wait') {
        try {
          await runAction(page, a, baseUrl)
        } catch (err) {
          console.warn(`      [pre-roll] ${a.type} failed: ${(err as Error).message.split('\n')[0]}`)
        }
        i++
      } else break
    }
    await waitForSettled(page, undefined, script.audience)

    // Action phase: the clip starts here.
    const startMs = Date.now() - startEpoch

    // AUDIO-FIRST invariant: narration must already exist, and its duration
    // sizes the hold. Enforce it loudly rather than guessing.
    const audioFile = audioPathFor(script.id, segment.id)
    const audioDurationMs = getAudioDurationMs(audioFile)
    if (audioDurationMs <= 0) {
      throw new Error(
        `No narration audio for ${script.id}/${segment.id} — run the audio stage first. ` +
          `The pipeline does this automatically; if you are calling record directly, run ensureAudio().`,
      )
    }
    const holdMs = Math.max(audioDurationMs + TAIL_MS + (segment.holdAfterMs ?? 0), MIN_HOLD_MS)

    // Does this segment show a visible UI change after the clip starts?
    const hasVisibleActions = segment.actions
      .slice(i)
      .some((a) => !['navigate', 'wait', 'note'].includes(a.type))

    for (; i < segment.actions.length; i++) {
      const a = segment.actions[i]
      try {
        await runAction(page, a, baseUrl)
        if (a.type === 'navigate' || a.type === 'click') await waitForSettled(page, undefined, script.audience)
      } catch (err) {
        console.warn(`      [action] ${a.type} failed: ${(err as Error).message.split('\n')[0]}`)
        failures.push(`${segment.id}: action failed (${a.type}${'selector' in a ? ` on ${a.selector}` : ''})`)
      }
    }

    // Final settle on the described content; this instant starts the narration.
    for (const f of await waitForSettled(page, segment.readySelector, script.audience)) {
      console.warn(`      [gate] ${f}`)
      failures.push(`${segment.id}: ${f}`)
    }
    const narrationStartMs = Date.now() - startEpoch

    if (hasVisibleActions) {
      // Hold static on the settled result for the narration.
      await page.waitForTimeout(holdMs)
    } else {
      // Narration-only segment: gentle scroll for visual motion. Use a wall-clock
      // deadline, not a step count — slowMo inflates each wheel event.
      const deadline = Date.now() + holdMs
      const stepMs = 600
      let direction = 1
      let n = 0
      while (Date.now() < deadline) {
        try {
          await page.mouse.wheel(0, direction * 200)
          await page.waitForTimeout(stepMs)
        } catch {
          break // page gone (redirect/crash) — stop cleanly
        }
        if (++n % 5 === 0) direction *= -1 // reverse so we never run off-screen
      }
    }

    timings.push({ segmentId: segment.id, startMs, narrationStartMs, endMs: Date.now() - startEpoch })
  }

  if (failures.length) {
    console.warn(`\n   ${failures.length} gate/action failure(s):`)
    for (const f of failures) console.warn(`     - ${f}`)
    if (STRICT) {
      await context.close()
      await browser.close()
      throw new Error(`STRICT_GATES=true — aborting ${script.id} (${failures.length} failures)`)
    }
  } else {
    console.log('   [ok] all settle gates passed')
  }

  await page.waitForTimeout(1200) // hold last frame briefly
  await context.close() // flushes the webm
  await browser.close()

  // Playwright names the file with a random UUID; take the newest.
  const rawDir = path.join(RAW_DIR, script.id)
  const files = fs
    .readdirSync(rawDir)
    .filter((f) => f.endsWith('.webm'))
    .map((f) => ({ name: f, mtime: fs.statSync(path.join(rawDir, f)).mtimeMs }))
    .sort((a, b) => b.mtime - a.mtime)
  if (!files.length) throw new Error(`No video produced in ${rawDir}`)
  const videoPath = path.join(rawDir, files[0].name)

  const timingsPath = videoPath.replace('.webm', '-timings.json')
  fs.writeFileSync(timingsPath, JSON.stringify(timings, null, 2), 'utf-8')
  console.log(`   [ok] video: ${videoPath}`)
  return { videoPath, timings }
}

/**
 * Dry-run a script against the live environment with no recording. Walks the
 * same pre-roll/actions/settle path as recordScript and reports anything that
 * fails. Run before a take: a green validate means the recording will not stall
 * mid-segment.
 */
export async function validateScript(script: TutorialScript): Promise<ValidationResult> {
  console.log(`\n[validate] ${script.title}`)
  const failures: string[] = []
  const { browser, context, page } = await createSession(script, false)
  const baseUrl = baseUrlFor(script)

  for (const segment of script.segments) {
    if (!segment.readySelector) {
      failures.push(`${segment.id}: missing readySelector (required)`)
      continue
    }

    let i = 0
    while (i < segment.actions.length) {
      const a = segment.actions[i]
      if (a.type === 'navigate' || a.type === 'wait') {
        try {
          await runAction(page, a, baseUrl)
        } catch (err) {
          failures.push(`${segment.id}: pre-roll ${a.type} failed — ${(err as Error).message.split('\n')[0]}`)
        }
        i++
      } else break
    }

    const gate1 = await waitForSettled(page, undefined, script.audience)
    for (; i < segment.actions.length; i++) {
      const a = segment.actions[i]
      try {
        await runAction(page, a, baseUrl)
        if (a.type === 'navigate' || a.type === 'click') await waitForSettled(page, undefined, script.audience)
      } catch (err) {
        failures.push(
          `${segment.id}: action ${a.type}${'selector' in a ? ` "${a.selector}"` : ''} failed — ${
            (err as Error).message.split('\n')[0]
          }`,
        )
      }
    }

    const gate2 = await waitForSettled(page, segment.readySelector, script.audience)
    const all = [...gate1, ...gate2].map((g) => `${segment.id}: ${g}`)
    failures.push(...all)
    console.log(`   ${all.length ? 'x' : 'ok'} ${segment.id}`)
  }

  await context.close()
  await browser.close()

  const ok = failures.length === 0
  console.log(ok ? `[validate] ${script.id}: PASS` : `[validate] ${script.id}: FAIL (${failures.length})`)
  return { scriptId: script.id, ok, failures }
}
