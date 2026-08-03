---
name: daimon-widget-cards
description: Render Daimon display cards for assistant results. Use automatically when showing local files, images, videos, final generated products, completed deletion lists, existing tool resources, or a Canvas entry point in Daimon chat. Blueprint Widgets are shown with the Widget tool, not card fences.
---

# Daimon Widget Cards

Use this skill when the answer should include structured display cards in Daimon chat.

Most Daimon cards are display only. They are emitted as Markdown fenced code blocks that the
Daimon desktop client renders. Do not collect user input, create forms, or ask the user to choose
through a display card.

Interactive Widgets are Blueprint assets. Create them with the `Widget` tool and show them with
`Widget.show` or the `widgetView` returned by `Widget.create`. Do not emit legacy `daimon-instant-widget` cards.

## Supported Card Types

Use only these Daimon card fences:

- `daimon-file-list` - files found or listed for the user.
- `daimon-image-gallery` - image-only results.
- `daimon-video-card` - video-only results.
- `daimon-delete-list` - files that have already been deleted.
- `daimon-tool-call` - front-end display for an existing tool resource.
- `daimon-product` - final files created or modified by this task.
- `daimon-canvas` - a clickable entry point that opens an existing Canvas.

Do not invent other card names.

## File-Like Cards

For file, image, video, delete-list, and product cards, write one Markdown link per line:

```daimon-file-list
[Report.pdf](</Users/me/Desktop/Report.pdf>)
[Notes.md](</Users/me/Desktop/Notes.md>)
```

Rules:

1. Paths must be absolute local paths.
2. Use angle brackets around paths, especially when paths may contain spaces.
3. Only include files you know exist or were returned by a real tool/result.
4. Do not duplicate the same path across cards in the same answer.

## Final Products

When the task creates or modifies final files on disk, declare those files at the end of the answer
with `daimon-product`.

Use `daimon-product` for final deliverables instead of repeating them in `daimon-file-list`,
`daimon-image-gallery`, or `daimon-video-card`.

```daimon-product
[Data report.xlsx](</Users/me/Downloads/Data report.xlsx>)
```

## Media Cards

Use `daimon-image-gallery` only for image files:

```daimon-image-gallery
[cover.png](</Users/me/Pictures/cover.png>)
[diagram.jpg](</Users/me/Pictures/diagram.jpg>)
```

Use `daimon-video-card` only for video files:

```daimon-video-card
[demo.mp4](</Users/me/Movies/demo.mp4>)
```

If results contain mixed file types, use `daimon-file-list`.

## Completed Deletions

Use `daimon-delete-list` only after deletion has already completed:

```daimon-delete-list
[old.log](</Users/me/Desktop/old.log>)
```

Do not use this card to request deletion or ask for deletion confirmation.

## Tool Resource Cards

Use `daimon-tool-call` only for a supported tool-created resource that the Daimon client can
inspect by id:

```daimon-tool-call
kind: resource-kind
id: resource-id
agentId: main
```

`agentId` is optional. Include it when the tool result provides it.

Do not use `daimon-tool-call` for Blueprint Widget display. Use `Widget.show`.

## Canvas Entry Cards

Use `daimon-canvas` to give the user a clickable card that opens a Canvas in the side panel.
Emit it after you create a Canvas, place Widgets onto a Canvas, or whenever you direct the user
to look at a specific Canvas:

```daimon-canvas
canvasId: canvas-id-from-canvas-tool
title: Canvas title
```

Rules:

1. `canvasId` is required. Use the id returned by the `Canvas` tool (for example from
   `createCanvas` or `readCanvas`). Never invent or guess a canvas id.
2. `title` is optional but recommended; use the Canvas title so the card is recognizable.
3. The card only opens an existing Canvas. It does not create one and does not display Canvas
   content inline.

## Output Placement

- Put a short natural-language summary before cards when helpful.
- Keep card count low; use the most specific card type.
- Put `daimon-product` at the end of the response when final deliverables exist.
- Do not expose internal ids in natural language when they are only needed inside a card.
