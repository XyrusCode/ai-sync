/**
 * UI inspector. Logs in, walks a list of routes, and dumps the selectors you
 * need to author scripts. This is the step that prevents the most common
 * failure in the whole pipeline: writing a script against remembered selectors
 * instead of observed ones.
 *
 * Usage:
 *   npx ts-node src/inspect.ts --routes "/,/students,/settings" --out output/ui-inspection.json
 *   npx ts-node src/inspect.ts --discover          # expand nav, list all routes
 *
 * NOTE: uses $$eval / locator APIs rather than page.evaluate closures. Bundlers
 * that inject a `__name` helper (tsx/esbuild) break arrow functions passed to
 * page.evaluate, because the serialized function has no access to the helper.
 */
import 'dotenv/config'
import * as fs from 'fs'
import * as path from 'path'
import { chromium } from 'playwright'
import { audienceFor, loadConfig, viewerFor } from './config'

interface PageData {
  url: string
  title: string
  headings: unknown[]
  buttons: unknown[]
  inputs: unknown[]
  links: unknown[]
  tabs: unknown[]
  comboboxes: unknown[]
  dialogs: unknown[]
  emptyStates: unknown[]
  textSample: string
  error?: string
}

async function loginIfNeeded(page: any, audienceKey: string): Promise<void> {
  const audience = audienceFor(audienceKey)
  if (audience.auth.mode === 'none') return
  const login = audience.auth.uiLogin
  if (!login) throw new Error('inspect requires a uiLogin block (used to establish the session)')

  const base = audience.appBaseUrl.replace(/\/$/, '')
  await page.goto(`${base}${login.loginPath}`, { waitUntil: 'commit', timeout: 90000 })
  await page.waitForTimeout(800)
  await page.waitForSelector(login.identifierSelector, { timeout: 60000 })
  await page.locator(login.identifierSelector).first().fill(process.env.LOGIN_ID ?? '')
  await page.locator(login.passwordSelector).first().fill(process.env.LOGIN_PASSWORD ?? '')
  await page.locator(login.submitSelector).first().click()
  await page.waitForURL((u: any) => !u.pathname.includes('/login'), { timeout: 120000, waitUntil: 'commit' })
  await page.waitForTimeout(2000)
  console.log('[inspect] logged in')
}

async function inspectPage(page: any, url: string, fullUrl: string): Promise<PageData> {
  const data: PageData = { url: fullUrl, title: '', headings: [], buttons: [], inputs: [], links: [], tabs: [], comboboxes: [], dialogs: [], emptyStates: [], textSample: '' }
  try {
    await page.goto(fullUrl, { waitUntil: 'commit', timeout: 60000 })
    await page.waitForTimeout(2500)

    data.url = page.url()
    data.title = await page.title()
    data.textSample = ((await page.evaluate('document.body ? document.body.innerText : ""')) as string)
      .replace(/\s+/g, ' ')
      .slice(0, 500)

    data.headings = await page.$$eval('h1, h2, h3, h4', (els: Element[]) =>
      els.map((el) => ({ tag: el.tagName, text: (el as HTMLElement).innerText?.trim().slice(0, 120) })),
    )
    data.buttons = await page.$$eval('button, [role="button"], a[role="button"]', (els: Element[]) =>
      els.slice(0, 40).map((el) => ({
        tag: el.tagName,
        text: (el as HTMLElement).innerText?.trim().slice(0, 80),
        id: el.id || undefined,
        testid: el.getAttribute('data-testid') || undefined,
        ariaLabel: el.getAttribute('aria-label') || undefined,
        type: el.getAttribute('type') || undefined,
        cls: String((el as HTMLElement).className || '').slice(0, 60),
      })),
    )
    data.inputs = await page.$$eval('input, select, textarea', (els: Element[]) =>
      els.map((el) => ({
        tag: el.tagName,
        type: el.getAttribute('type') || undefined,
        name: el.getAttribute('name') || undefined,
        placeholder: el.getAttribute('placeholder') || undefined,
        id: el.id || undefined,
        testid: el.getAttribute('data-testid') || undefined,
        ariaLabel: el.getAttribute('aria-label') || undefined,
      })),
    )
    data.links = await page.$$eval('a[href]', (els: Element[]) =>
      els.slice(0, 60).map((el) => ({ text: (el as HTMLElement).innerText?.trim().slice(0, 60), href: el.getAttribute('href') })),
    )
    data.tabs = await page.$$eval('[role="tab"], [class*="tab" i][role], nav a', (els: Element[]) =>
      els.slice(0, 30).map((el) => ({ text: (el as HTMLElement).innerText?.trim().slice(0, 60), testid: el.getAttribute('data-testid') || undefined })),
    )
    data.comboboxes = await page.$$eval('[role="combobox"], select, [class*="select" i]', (els: Element[]) =>
      els.slice(0, 30).map((el) => ({
        cls: String((el as HTMLElement).className || '').slice(0, 60),
        ariaLabel: el.getAttribute('aria-label') || undefined,
        testid: el.getAttribute('data-testid') || undefined,
      })),
    )
    data.dialogs = await page.$$eval('[role="dialog"], [class*="modal" i], [class*="drawer" i]', (els: Element[]) =>
      els.slice(0, 10).map((el) => ({ cls: String((el as HTMLElement).className || '').slice(0, 60), ariaLabel: el.getAttribute('aria-label') || undefined })),
    )
    data.emptyStates = await page.$$eval('[class*="empty" i]', (els: Element[]) =>
      els.slice(0, 10).map((el) => ({ text: (el as HTMLElement).innerText?.trim().slice(0, 120) })),
    )
  } catch (err: any) {
    data.error = err.message.split('\n')[0]
  }
  return data
}

async function main(): Promise<void> {
  const args = process.argv.slice(2)
  const flag = (name: string, fallback?: string) => {
    const i = args.indexOf(name)
    return i !== -1 ? args[i + 1] : fallback
  }

  const explicit = flag('--audience')
  const audienceKey = explicit ?? Object.keys(loadConfig().audiences)[0]
  const audience = audienceFor(audienceKey)
  const routesArg = flag('--routes', '/')
  const out = flag('--out', 'output/ui-inspection.json')
  const discover = args.includes('--discover')

  const browser = await chromium.launch({
    headless: process.env.PLAYWRIGHT_HEADLESS !== 'false',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-http2'],
  })
  const viewer = viewerFor()
  const context = await browser.newContext({ viewport: { width: viewer.width, height: viewer.height } })
  const page = await context.newPage()

  console.log(`[inspect] base: ${audience.appBaseUrl}`)
  await loginIfNeeded(page, audienceKey)

  const all: Record<string, unknown> = {}

  if (discover) {
    // Expand collapsed nav, then harvest every route it reveals.
    for (const sel of audience.shell.navExpandSelectors ?? []) {
      const nodes = await page.$$(sel)
      for (const n of nodes) {
        try {
          await n.click()
          await page.waitForTimeout(400)
        } catch {
          /* not clickable, skip */
        }
      }
    }
    const navSel = audience.shell.navLinkSelector ?? 'nav a[href], aside a[href]'
    all.__nav = await page.$$eval(navSel, (els: Element[]) =>
      els.map((el) => ({ text: (el as HTMLElement).innerText?.trim(), href: el.getAttribute('href') })),
    )
    console.log('[inspect] discovered nav routes:', JSON.stringify(all.__nav, null, 2))
  }

  for (const route of routesArg.split(',').map((r) => r.trim()).filter(Boolean)) {
    const full = `${audience.appBaseUrl.replace(/\/$/, '')}${route.startsWith('/') ? route : '/' + route}`
    const name = route === '/' ? 'root' : route.replace(/^\//, '').replace(/[/?=&]/g, '-')
    console.log(`[inspect] ${route}`)
    all[name] = await inspectPage(page, route, full)
  }

  fs.mkdirSync(path.dirname(out), { recursive: true })
  fs.writeFileSync(out, JSON.stringify(all, null, 2), 'utf-8')
  console.log(`[inspect] wrote ${out}`)
  await context.close()
  await browser.close()
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
