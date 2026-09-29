/**
 * Authentication for the recorder.
 *
 * Two strategies, chosen per audience in app.config.json:
 *
 *  1. `localStorage-token` (preferred). Mint ONE bearer token through the app's
 *     own API, cache it, and seed localStorage before the SPA boots. A batch of
 *     16 videos costs one login instead of sixteen. This also sidesteps login
 *     throttles (many backends cap ~5 attempts / 15 min per credential+IP) that
 *     a re-record loop trips immediately.
 *
 *  2. `ui-login` (fallback). Drive the real login form. Needed for videos that
 *     show the login page itself, and whenever the API contract is unknown.
 *
 * Strategy 1 auto-degrades to 2: if a seeded token yields no app shell, the
 * cached token is dropped and the UI form is driven instead.
 */
import 'dotenv/config'
import * as fs from 'fs'
import * as path from 'path'
import axios from 'axios'
import type { BrowserContext } from 'playwright'
import type { TutorialScript } from './types'
import { audienceFor } from './config'

const TOKENS_CACHE = path.join(process.cwd(), 'output', 'tokens.json')

interface CacheEntry {
  accessToken: string
  tokenPrefix?: string
  fetchedAt: number
}

function readCache(): Record<string, CacheEntry> {
  try {
    return JSON.parse(fs.readFileSync(TOKENS_CACHE, 'utf-8'))
  } catch {
    return {}
  }
}

function writeCache(cache: Record<string, CacheEntry>): void {
  fs.mkdirSync(path.dirname(TOKENS_CACHE), { recursive: true })
  fs.writeFileSync(TOKENS_CACHE, JSON.stringify(cache, null, 2), 'utf-8')
}

function extract(obj: unknown, dotted: string): string | undefined {
  if (!dotted) return typeof obj === 'string' ? obj : undefined
  let cur: unknown = obj
  for (const part of dotted.split('.')) {
    if (cur && typeof cur === 'object' && part in (cur as Record<string, unknown>)) {
      cur = (cur as Record<string, unknown>)[part]
    } else {
      return undefined
    }
  }
  return typeof cur === 'string' ? cur : undefined
}

async function mintToken(audienceKey: string): Promise<CacheEntry> {
  const audience = audienceFor(audienceKey)
  const tokenApi = audience.auth.tokenApi
  if (!tokenApi) throw new Error(`audience "${audienceKey}" uses token auth but has no tokenApi block`)

  const missing = Object.values(tokenApi.body).filter((v) => v === '')
  if (missing.length) {
    throw new Error(`tokenApi body has unresolved \${ENV:...} placeholders: ${JSON.stringify(tokenApi.body)}`)
  }

  const res = await axios.post(tokenApi.url, tokenApi.body, {
    headers: { Accept: 'application/json', 'Content-Type': 'application/json', ...(tokenApi.headers ?? {}) },
    timeout: 60_000,
  })

  const token = extract(res.data, tokenApi.tokenPath ?? 'data') ?? extract(res.data, 'token')
  if (!token || token.length < 16) {
    throw new Error(
      `Unexpected login response from ${tokenApi.url}: ${JSON.stringify(res.data).slice(0, 200)}\n` +
        `Adjust tokenPath in app.config.json (tried "tokenPath" then "token").`,
    )
  }
  return { accessToken: token, tokenPrefix: tokenApi.tokenPrefix, fetchedAt: Date.now() }
}

export function clearCachedToken(audienceKey: string): void {
  const cache = readCache()
  delete cache[audienceKey]
  writeCache(cache)
}

/** Cached token for an audience, minting one when absent or stale. */
export async function getAuthToken(audienceKey: string, forceRefresh = false): Promise<CacheEntry> {
  const cache = readCache()
  const entry = cache[audienceKey]
  const maxAgeMs = 12 * 60 * 60 * 1000
  if (!forceRefresh && entry?.accessToken && Date.now() - entry.fetchedAt < maxAgeMs) {
    return entry
  }
  console.log(`   [auth] minting ${audienceKey} token via API`)
  const fresh = await mintToken(audienceKey)
  cache[audienceKey] = fresh
  writeCache(cache)
  return fresh
}

/**
 * Seed localStorage so the SPA boots authenticated. Keys are configurable
 * because storage layout is app-specific; the values themselves are not.
 */
export async function prepareAuthenticatedContext(
  context: BrowserContext,
  script: TutorialScript,
): Promise<boolean> {
  if (script.skipAuth) return false
  const audience = audienceFor(script.audience)
  if (audience.auth.mode !== 'localStorage-token') return false

  let token: CacheEntry
  try {
    token = await getAuthToken(script.audience)
  } catch (err) {
    console.warn(`   [auth] token mint failed (${(err as Error).message.split('\n')[0]}) — will use UI login`)
    return false
  }

  const ls = audience.auth.localStorage
  if (!ls) throw new Error(`audience "${script.audience}" uses token auth but has no localStorage block`)

  const value = token.tokenPrefix ? `${token.tokenPrefix} ${token.accessToken}` : token.accessToken
  const tokenKey = ls.tokenKey ?? `@${ls.scope}.token`

  await context.addInitScript(
    ({ tokenKey, institutionKey, value, seed }) => {
      // Common shape: { accessToken, createdAt }. Apps that expect a bare
      // string, or a different field name, only need this one function edited.
      window.localStorage.setItem(tokenKey, JSON.stringify({ accessToken: value, createdAt: Date.now().toString() }))
      if (!seed) return
      if (institutionKey) {
        // Tenant/workspace metadata the SPA needs before its first API call.
        window.localStorage.setItem(institutionKey, JSON.stringify(seed))
        return
      }
      for (const [k, v] of Object.entries(seed)) {
        window.localStorage.setItem(k, v)
      }
    },
    { tokenKey, institutionKey: ls.institutionKey ?? null, value, seed: ls.seed ?? null },
  )
  return true
}
