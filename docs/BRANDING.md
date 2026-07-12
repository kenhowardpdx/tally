# Branding

## Favicon

Source: `frontend/src/lib/assets/favicon.svg` (imported and linked in
`frontend/src/routes/+layout.svelte`).

A bold, uppercase "T" for Tally, drawn as a single stroked path so the left
side of the crossbar doubles as a checkmark tick — a nod to tracking bills
and staying on top of your balance. The vertical stem reads clearly as a
"T" leg, not a plus/cross, avoiding any unintended religious-symbol
association.

- Background: rounded square, `#2563eb` (blue-600)
- Glyph: white, round-capped stroke (`stroke-width="6.5"`) on a 48x48 canvas
  - Crossbar + check: `M8 16 L15 24 L24 10 L40 14` (short dip, longer rise,
    then the right arm of the T)
  - Stem: `M24 10 L24 40`
- Tested legible down to 16x16

To update the favicon, edit `frontend/src/lib/assets/favicon.svg` directly —
it's a plain SVG, no build step required.
