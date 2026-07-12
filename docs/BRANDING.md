# Branding

## Favicon

Source: `frontend/src/lib/assets/favicon.svg` (imported and linked in
`frontend/src/routes/+layout.svelte`).

Literal tally marks: four vertical strokes struck through by a fifth
diagonal line, the classic way to count in groups of five. It's a direct,
on-brand pun with the product name "Tally" — instantly recognizable as a
counting/tracking mark and avoids any ambiguity with unrelated symbols
(earlier drafts built around a "+" and a checkmark both risked reading as
something else, like a cross).

- Background: rounded square, `#2563eb` (blue-600)
- Glyph: white, round-capped strokes (`stroke-width="4"`) on a 48x48 canvas
  - Four verticals at `x=13,19,25,31`, spanning `y=10` to `y=38`
  - One diagonal strike from `(9,36)` to `(35,10)`
- Tested legible down to 16x16

To update the favicon, edit `frontend/src/lib/assets/favicon.svg` directly —
it's a plain SVG, no build step required.
