// Timing for the whole piece, in frames. Edit these to change pacing.
// One "second" = FPS frames. Scene boundaries are cumulative frame counts.
export const FPS = 30;

// Scene end-frames (cumulative). A scene runs from the previous end to its own.
export const TITLE_END = 90; //   0 - 90   (3.0s)  title / logo build
export const CONTENT_END = 240; //  90 - 240  (5.0s)  main message / features
export const OUTRO_END = 330; // 240 - 330  (3.0s)  call-to-action / end card
export const DURATION_IN_FRAMES = OUTRO_END; // total length

// Landscape master; the vertical composition reuses the same content.
export const WIDTH = 1920;
export const HEIGHT = 1080;
export const VERTICAL_WIDTH = 1080;
export const VERTICAL_HEIGHT = 1920;
