/**
 * App configuration loader.
 *
 * Everything app-specific lives in `config/app.config.json`: base URLs, how to
 * authenticate, which selectors mean "the app shell is up". The pipeline reads
 * it and stays ignorant of the product it is filming.
 *
 * Secrets stay in `.env`. Any string in the JSON may reference them with
 * `${ENV:VAR_NAME}` so tokens never land in a committed file.
 */
import 'dotenv/config'
import * as fs from 'fs'
import * as path from 'path'

export type AuthMode = 'localStorage-token' | 'ui-login' | 'none'

export interface UiLoginConfig {
  loginPath: string
  identifierSelector: string
  passwordSelector: string
  submitSelector: string
  /**
   * Request field name the login form submits. Backends disagree: many read
   * `email`, some read `identifier` (email OR phone) or `username`.
   * Only matters for token minting; UI login is unaffected.
   */
  identifierField: string
}

export interface TokenApiConfig {
  url: string
  /** Body template; `${ENV:VAR}` placeholders are substituted at load time. */
  body: Record<string, string>
  headers?: Record<string, string>
  /**
   * Dotted path to the token in the JSON response. Empty string = the response
   * body IS the token. Common shapes: `data`, `token`, `access_token`, `data.token`.
   */
  tokenPath?: string
  /** Prepended to the extracted value when the app stores "Bearer <token>". */
  tokenPrefix?: string
}

export interface AuthConfig {
  mode: AuthMode
  /**
   * localStorage seeding. `scope` is interpolated into the key templates, so a
   * React/Redux app that namespaces under `@<scope>.token` is a two-line change.
   */
  localStorage?: {
    scope: string
    tokenKey?: string
    institutionKey?: string
    /** Extra localStorage keys to seed, e.g. product-tour completion flags. */
    seed?: Record<string, string>
  }
  uiLogin?: UiLoginConfig
  tokenApi?: TokenApiConfig
  /** Key under which the minted token is cached in output/tokens.json. */
  cacheKey?: string
}

export interface ShellConfig {
  /** Root element that only exists once the authenticated app has mounted. */
  readyRootSelector: string
  /** Any of these being visible means "still loading". */
  spinnerSelectors: string[]
  /** Where to land after login, so segment 1 opens on a warm page. */
  defaultPath: string
  /** Click these to expand collapsed nav, then harvest links. Inspector only. */
  navExpandSelectors?: string[]
  /** Where the inspector harvests nav links from. */
  navLinkSelector?: string
}

export interface AudienceConfig {
  label: string
  appBaseUrl: string
  auth: AuthConfig
  shell: ShellConfig
}

export interface ViewerConfig {
  width: number
  height: number
  /** How long to wait for readySelector before logging a gate failure. */
  readyTimeoutMs: number
  /** How long to wait for the app shell / spinners to clear. */
  shellTimeoutMs: number
  /** Total wall-clock budget for one script. Batches must stay under this. */
  scriptTimeoutMs: number
}

export interface AppConfig {
  name: string
  audiences: Record<string, AudienceConfig>
  viewer: ViewerConfig
  tts: {
    voice: string
    rate: string
    volume: string
  }
  upload?: {
    privacy: 'unlisted' | 'private' | 'public'
    playlistId?: string
  }
}

const CONFIG_PATH = process.env.SCREENCAST_CONFIG ?? path.join(process.cwd(), 'config', 'app.config.json')

/** Replace `${ENV:NAME}` with the process env value (empty string when unset). */
function interpolate(value: unknown): unknown {
  if (typeof value === 'string') {
    return value.replace(/\$\{ENV:([A-Z0-9_]+)\}/gi, (_m, name: string) => process.env[name] ?? '')
  }
  if (Array.isArray(value)) return value.map(interpolate)
  if (value && typeof value === 'object') {
    const out: Record<string, unknown> = {}
    for (const [k, v] of Object.entries(value as Record<string, unknown>)) out[k] = interpolate(v)
    return out
  }
  return value
}

function loadRaw(): AppConfig {
  if (!fs.existsSync(CONFIG_PATH)) {
    throw new Error(
      `No app config at ${CONFIG_PATH}\n` +
        `Create it from config/app.config.example.json, or set SCREENCAST_CONFIG to its path.`,
    )
  }
  const raw = interpolate(JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf-8'))) as AppConfig

  // Keys starting with `_` are annotations, not audiences, so a config can be
  // commented in place without the loader trying to authenticate as "_comment".
  if (raw.audiences) {
    raw.audiences = Object.fromEntries(Object.entries(raw.audiences).filter(([k]) => !k.startsWith('_')))
    if (Object.keys(raw.audiences).length === 0) {
      throw new Error(`No audiences defined in ${CONFIG_PATH} (keys starting with "_" are ignored)`)
    }
  }
  return raw
}

let cached: AppConfig | null = null

export function loadConfig(): AppConfig {
  if (!cached) cached = loadRaw()
  return cached
}

/**
 * Resolve the audience a script targets. Falls back to the first configured
 * audience so single-app setups need no `audience` field at all.
 */
export function audienceFor(name: string | undefined): AudienceConfig {
  const cfg = loadConfig()
  const key = name ?? Object.keys(cfg.audiences)[0]
  const audience = cfg.audiences[key]
  if (!audience) {
    throw new Error(
      `Unknown audience "${key}". Configured: ${Object.keys(cfg.audiences).join(', ') || '(none)'}`,
    )
  }
  return audience
}

export function viewerFor(): ViewerConfig {
  return loadConfig().viewer
}

export function ttsFor() {
  return loadConfig().tts
}
