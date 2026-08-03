#!/bin/bash
# Normalize all SVGs: replace black fills with currentColor for theming support

for f in /Users/moonshot/kimi-design-skill/assets/icons/*.svg; do
  # Replace fill="black" fill-opacity="0.9" with fill="currentColor"
  sed -i '' 's/fill="black" fill-opacity="0\.9"/fill="currentColor"/g' "$f"
  # Also catch any remaining fill="black" without opacity
  sed -i '' 's/fill="black"/fill="currentColor"/g' "$f"
  # And fill="#000000"
  sed -i '' 's/fill="#000000"/fill="currentColor"/g' "$f"
  # Remove xmlns if not needed (optional cleanup)
done

echo "Normalized $(ls /Users/moonshot/kimi-design-skill/assets/icons/*.svg | wc -l) SVG files."
