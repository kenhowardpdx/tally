# Branding

## Favicon

Source: `frontend/src/lib/assets/favicon.svg` (imported and linked in
`frontend/src/routes/+layout.svelte`).

A bold, uppercase "T" for Tally, built from two overlapping bars of equal
thickness so the crossbar and stem read like a plus sign — a nod to adding up
bills and balances. The short stub above the crossbar keeps the glyph
legible as a "T" rather than a full "+" at small sizes.

- Background: rounded square, `#2563eb` (blue-600)
- Glyph: white, two rounded bars (`rx="2"`) on a 48x48 canvas
- Tested legible down to 16x16

To update the favicon, edit `frontend/src/lib/assets/favicon.svg` directly —
it's a plain SVG, no build step required.
