# Configuration

`config/app.config.json` holds every app-specific fact. The pipeline reads it and
stays ignorant of the product it films. That split is the reason one copy of the
code serves many apps and many user roles.

## Shape

```jsonc
{
  "name": "my-app",
  "audiences": {
    "<key>": {
      "label": "Admin console",          // human label, logs only
      "appBaseUrl": "https://admin.example.com",
      "auth": { /* see below */ },
      "shell": { /* see below */ }
    }
  },
  "viewer": { "width": 1280, "height": 720, "readyTimeoutMs": 30000,
              "shellTimeoutMs": 60000, "scriptTimeoutMs": 900000 },
  "tts": { "voice": "en-US-AriaNeural", "rate": "+0%", "volume": "+0%" },
  "upload": { "privacy": "unlisted", "playlistId": "" }
}
```

A script picks its audience by name. When there is only one, the `audience`
field can be omitted.

Keys starting with `_` are treated as annotations and ignored, so the config can
be commented in place without the loader trying to authenticate as `_comment`.

## Secret interpolation

Any string may reference the environment as `${ENV:VAR_NAME}`, resolved at load
time. This keeps tokens and passwords in `.env` while the committed config stays
shareable.

```jsonc
"body": { "email": "${ENV:LOGIN_ID}", "password": "${ENV:LOGIN_PASSWORD}" }
```

## `auth`

```jsonc
"auth": {
  "mode": "localStorage-token" | "ui-login" | "none",
  "cacheKey": "admin",
  "tokenApi": { /* when mode = localStorage-token */ },
  "localStorage": { /* when mode = localStorage-token */ },
  "uiLogin": { /* needed for inspect, and as the fallback path */ }
}
```

`uiLogin` should be filled in even when `mode` is `localStorage-token`: the
recorder falls back to driving the form when a cached token yields no app shell,
and `inspect.ts` needs it to establish a session.

### `tokenApi`

```jsonc
"tokenApi": {
  "url": "https://api.example.com/auth/login",
  "body": { "email": "${ENV:LOGIN_ID}", "password": "${ENV:LOGIN_PASSWORD}" },
  "headers": { "X-Tenant-ID": "acme" },
  "tokenPath": "data.token",
  "tokenPrefix": "Bearer"
}
```

- **`tokenPath`** — dotted path to the token in the JSON response. Empty string
  means the response body *is* the token. The pipeline tries `tokenPath`, then
  `token`, then `data`. Common shapes: `data`, `token`, `access_token`,
  `data.token`.
- **`tokenPrefix`** — set only when the app stores `"Bearer <token>"` in storage.

**The identifier field name varies by backend.** Some read `email`, others read
`identifier` (email *or* phone) or `username`. This is the most common cause of
a 401 on a token mint that looks correct. Confirm against the login controller;
do not guess.

### `localStorage`

```jsonc
"localStorage": {
  "scope": "admin",
  "tokenKey": "@admin.token",
  "institutionKey": "@admin.tenant",
  "seed": { "@admin.tourCompleted": "{\"home\":true}" }
}
```

- `tokenKey` — where the SPA reads the token from. Defaults to `@<scope>.token`.
- `institutionKey` — optional. When set, the whole `seed` object is written to
  this key as JSON (useful for tenant/workspace metadata the SPA needs before its
  first API call).
- `seed` — any other localStorage keys to plant. A product-tour flag is the
  common one: an auto-opening overlay dims the page and blocks clicks on early
  segments, so it must be pre-suppressed.

The seeded value is `{ accessToken, createdAt }` by default. If the app stores a
bare string or a different field name, that is the single function to edit in
`src/auth.ts`.

## `shell`

```jsonc
"shell": {
  "readyRootSelector": "#root",
  "spinnerSelectors": [".spinner", "[aria-busy='true']", ".ant-spin-spinning"],
  "defaultPath": "/",
  "navExpandSelectors": ["nav button[aria-expanded='false']"],
  "navLinkSelector": "nav a[href]"
}
```

- **`readyRootSelector`** — an element that only exists once the authenticated
  app has mounted. Pick the app's root container, not `body`.
- **`spinnerSelectors`** — anything visible here means "still loading". Getting
  this right is what stops narration from playing over a spinner. Include both
  full-screen and inline loaders. Ant Design adds `.ant-spin-spinning`; most
  others have a project-specific class.
- **`defaultPath`** — where to land after login, so segment 1 opens on a warm
  page rather than a cold load.
- `navExpandSelectors`, `navLinkSelector` — used by `inspect.ts --discover` to
  expand collapsed navigation and harvest routes.

## `viewer`

| Field | Meaning |
|---|---|
| `width` / `height` | Capture size. 1280x720 is the safe default; check the app renders correctly (some collapse to a mobile layout). |
| `readyTimeoutMs` | How long to wait for a `readySelector`. Raise for slow apps. |
| `shellTimeoutMs` | How long to wait for the shell and spinners. |
| `scriptTimeoutMs` | Budget for one script, used to size CI/session timeouts. |

## `tts`

Free Microsoft Edge neural voices, no API key. `rate` and `volume` are SSML-ish
strings (`+10%`, `-5%`). Keep narration pace near `+0%`; faster reads sound
synthetic. Nigerian English voices (`en-NG-EzinneNeural`, `en-NG-AbeoNeural`) are
available when that is the audience.

## Adding a user role

Duplicate an `audiences` entry. Change the URL, auth block, and shell selectors.
No code changes. A role that logs in through a different form, against a
different subdomain, needing a different localStorage namespace is a
configuration difference, not a code difference. That is the point.

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `LOGIN_ID` / `LOGIN_PASSWORD` | — | Credentials for the login form and token mint. |
| `SCREENCAST_CONFIG` | `config/app.config.json` | Config path override. |
| `STRICT_GATES` | `false` | `true` aborts a take when a settle gate fails. Use in CI. |
| `PLAYWRIGHT_HEADLESS` | `true` | `false` to watch a take live. |
| `PLAYWRIGHT_SLOWMO` | `0` | Per-action delay in ms. ~300 for heavily animated apps. |
| `CHROMIUM_PATH` | Playwright default | Pin a system Chromium. |
| `TTS_MAX_RETRIES` | `4` | Retries for dropped TTS websockets. |
| `MAX_LEAD_MS` | `2500` | Cap on silent lead-in before narration. |
