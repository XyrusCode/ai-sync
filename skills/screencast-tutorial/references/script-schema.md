# Script schema

One JSON file per video under `scripts/`. Files are discovered recursively and
sorted by filename, so `01-`, `02-` prefixes give you a deterministic order.

## Top level

```jsonc
{
  "id": "dashboard-tour",              // unique; also the output filename
  "title": "Dashboard Tour",           // shown in logs and as the video title
  "audience": "admin",                 // key into audiences in app.config.json
  "baseUrl": "https://...",            // optional; overrides the audience URL
  "skipAuth": false,                   // true for videos showing logged-out state
  "description": "...",                // YouTube description
  "segments": [ /* ... */ ]
}
```

`skipAuth: true` is for videos that deliberately film the logged-out experience,
typically a login walkthrough. Nothing is injected and the recorder starts on
the login route.

## Segment

```jsonc
{
  "id": "quick-actions",               // unique within the script; names the audio file
  "narrator": "The quick action tiles jump straight to...",
  "actions": [ /* ... */ ],
  "readySelector": "button:has-text('Reports')",
  "holdAfterMs": 500                   // optional extra hold
}
```

### `readySelector` is required

Validation fails the script without it, and it is the mechanism that keeps
narration on the settled screen. It should identify the specific content this
segment talks about, not something trivially true.

```jsonc
"readySelector": "#root"                        // too broad: always true
"readySelector": "h1:has-text('Reports')"       // right: names the described page
```

A loose selector is not a safe default. `#root` passes while the content panel
is still empty, which is exactly the desync this design removes.

### `id` stability

`id` names the cached narration file (`output/audio/<script>__<segment>.mp3`).
Renaming a segment after recording orphans the cache and re-synthesizes. Not
fatal, just a wasted TTS call.

## Actions

| Type | Fields | Notes |
|---|---|---|
| `navigate` | `url` | Relative to `baseUrl`, or absolute. |
| `click` | `selector`, `description?` | |
| `fill` | `selector`, `value`, `label?` | |
| `select` | `selector`, `value` | Native `<select>` only. |
| `wait` | `ms` | |
| `scroll` | `direction` (`up`/`down`), `amount?` | Pixels, default 400. |
| `hover` | `selector` | |
| `press` | `key` | e.g. `Enter`, `Tab`. |
| `waitForSelector` | `selector`, `timeout?`, `state?` | |
| `note` | `description` | Log only; no browser effect. Use to caption an API call or background job in the transcript. |

All selectors are Playwright selectors: CSS, `text=`, `:has-text()`,
`>>` chaining, and so on. See [Playwright selector docs](https://playwright.dev/docs/selectors).

## Ordering: pre-roll vs on-camera

Leading `navigate` and `wait` actions run **before** the clip starts for that
segment (pre-roll, off-camera). Everything from the first other action onward
runs on camera.

```jsonc
"actions": [
  { "type": "navigate", "url": "/reports" },   // pre-roll: not filmed
  { "type": "wait", "ms": 800 },              // pre-roll: not filmed
  { "type": "click", "selector": "#filter" }  // on camera
]
```

This matters. A cold load can take tens of seconds to fetch lazy chunks; if that
happens on camera, the segment opens on a blank screen and the narration is
already playing. Put navigation first so the merged clip opens on a painted page.

Actions that are only there to buy time (e.g. a `wait` after a slow animation)
belong *after* the visible action, so the wait does not pad the visible part of
the clip.

## Selector discipline

Preference order, most to least durable:

1. `#id` and `[data-testid="..."]`
2. `[aria-label="..."]`, `[role="..."]` combined with text
3. `[placeholder="..."]` on inputs
4. `text=` / `:has-text()` for human-visible labels
5. CSS class — last resort, and worth reporting upstream

Text and class selectors break the moment copy changes. If a page has no stable
hook, that is an app defect worth filing, not a reason to pin a script to
`.css-1x2y3z`.

Prefer a stable parent plus a discriminator over a positional selector.
`tbody tr:nth-child(3) td:nth-child(2)` breaks on re-sort; a row keyed by a
stable column is fine.

## Authoring rules that matter

**One idea per segment.** A segment that describes three things gets narrated
over one screen, and the last two thirds contradict what is on screen.

**15-25 seconds of narration.** Roughly 35-60 words. Long narration on a static
screen is a slideshow; short narration leaves the viewer with nothing to look at.

**Describe the settled screen, not the click.** The narrator speaks after
`readySelector` paints. "The reports table shows every invoice for the period,
with a running total in the footer" is right. "Now click Reports" is wrong,
because by the time it is spoken the click has already happened.

**Scroll for motion when nothing else changes.** A segment whose only action is
navigation gets a gentle auto-scroll across the hold, so the frame is not frozen.
When a segment does change something on screen, the recorder holds static, which
is what you want while the narrator explains the result.

**Keep segments independent.** A segment that depends on a prior segment's state
is fragile; a failed gate cascades. Re-establish the route in the segment that
needs it.

## Worked example

```jsonc
{
  "id": "enrollment-form",
  "title": "Enrolling a New Pupil",
  "audience": "admin",
  "segments": [
    {
      "id": "open-form",
      "narrator": "The Pupils workspace holds your learner register. Three tabs sit at the top: manage the roster, add a pupil one at a time, or bulk upload a spreadsheet.",
      "actions": [
        { "type": "navigate", "url": "/students" },
        { "type": "wait", "ms": 800 }
      ],
      "readySelector": "[role='tablist']"
    },
    {
      "id": "add-tab",
      "narrator": "Switching to the Add Pupil tab opens the enrollment form. Fields marked with an asterisk are required; everything else can be filled in later.",
      "actions": [
        { "type": "click", "selector": "[role='tab']:has-text('Add')" },
        { "type": "wait", "ms": 600 }
      ],
      "readySelector": "form:has(input[name='firstName'])"
    },
    {
      "id": "submit",
      "narrator": "Once the required fields are filled, the Save button becomes active. Submitting creates the pupil and generates a registration number automatically.",
      "actions": [
        { "type": "click", "selector": "button:has-text('Save')" },
        { "type": "wait", "ms": 800 }
      ],
      "readySelector": "[role='alert'], [role='status'], .toast"
    }
  ]
}
```

## Validation

```bash
npx ts-node src/pipeline.ts --validate --script enrollment-form
```

Reports every pre-roll failure, action failure, and settle-gate failure with the
selector that caused it. Fix all of them before recording; `--validate` is cheap
(a few minutes) compared with a failed take.
