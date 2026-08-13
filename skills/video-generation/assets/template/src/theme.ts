/**
 * Central design tokens. This is the FIRST thing to customize per subject.
 * Swap these values to rebrand the whole video — every scene reads from here.
 *
 * Tip: pick one dark background + 2-3 vivid accents that pop against it.
 * For a real brand, use its actual hex colors.
 */
export const COLORS = {
  bg: '#07070f', // near-black base
  bgDeep: '#03030a', // darker edge for radial vignettes
  accent1: '#00e5ff', // primary accent  (TODO: subject)
  accent2: '#ff2e9a', // secondary accent (TODO: subject)
  accent3: '#b8ff2e', // tertiary accent  (TODO: subject)
  white: '#ffffff',
  dim: 'rgba(255,255,255,0.55)',
};

// A heavy display face for headlines + a light face for supporting copy.
// Swap for a brand font (load via @remotion/google-fonts or a local file) when needed.
export const FONT_STACK = `'Arial Black', 'Segoe UI Black', 'Arial', sans-serif`;
export const FONT_LIGHT = `'Segoe UI', 'Arial', sans-serif`;
