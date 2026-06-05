# AI Girl — Reference Catalog

> Master reference library for the AI cosplay-girl persona: the model herself,
> reusable scene backgrounds, and her wardrobe/cosplay outfits. Use these as
> img2img / IP-adapter / inpaint anchors to keep generations consistent.
> **Started**: 2026-06-02

**See also**: [[AI-Cosplay-Model-Room|Room art-direction & consistency notes]] · [[LowBitrate-Blur|LowBitrate Blur realism filter]]

**Working library (canonical)**: `Code/AI-Girl/` — full-res originals you add to & organize:
`model/`, `scenes/door/`, `clothes/`, `renders/` (finished posts).
**Vault previews (this page)**: `graphify-out/wiki/assets/ai-girl/` — copies kept only so
images embed/render in Obsidian. Add new refs to `Code/AI-Girl/`; copy a preview here to show it.

---

## 1. Model reference

The character. Brown wavy hair with curtain bangs, brown ribbed turtleneck crop,
blue jeans, black nail polish. Mirror-selfie style.

![[model-reference.jpg]]

> **TODO** — add more model refs for a stable identity: face close-up (neutral,
> well-lit), full-body front, 3/4 and side profile, a few expressions, hair
> down vs. up. The more consistent angles, the better for LoRA / IP-adapter.

---

## 2. Scenes

Reusable environment backgrounds. The **door** is the signature establishing
shot — same hallway POV, different open-amount / lighting / tidiness so scenes
can match a mood. Keep the door + hallway pixel-stable; vary only the room.

### Door — hallway POV

| Variant | Door | Light | Tidy | Use |
|---------|------|-------|------|-----|
| Background (closed) | closed | hall | n/a | establishing / "before" |
| Half-open dim | ~1/2 | dim | — | moody peek, mystery |
| Semi-open (WIP) | ~2/3 | dim | messy | current incomplete scene |
| Full-open dim | full | dim | messy | night, lived-in |
| Full-open dim + tidy | full | dim | tidy | calm night |
| Full-open light + tidy | full | lit | tidy | clean daytime hero shot |

**Closed door (base / establishing)**
![[door-background.png]]

**Full open — light & tidy** (clearest look at the room: rack, white dresser, manga/photo wall, bed)
![[door-full-open-light-tidy.png]]

**Full open — dim & tidy**
![[door-full-open-dim-tidy.png]]

**Full open — dim**
![[door-full-open-dim.png]]

**Half open — dim**
![[door-half-open-dim.png]]

> **Consistency note**: through the door the room is small + dark, so detail
> drifts harmlessly between variants. For a hero room view, use the inside
> renders (see room page). Don't chase legible manga in door shots.

> **TODO** — add more scenes: full room interior(s), desk/vanity corner,
> bed close-up, mirror-selfie spot, bathroom, outdoor/balcony.

---

## 3. Clothes / cosplays

Wardrobe + costume catalog. Each outfit = a reference image + notes so the same
fit can be re-generated on the model.

> **TODO — empty.** Add per-outfit entries as they're created. Suggested fields:
> - thumbnail, outfit name, series/character (if cosplay), colors, key pieces,
>   wig, props, which scenes it suits.
> Starter set worth building: 2–3 casual fits (the brown-turtleneck baseline
> here is #1), plus the first cosplay with its wig + props.

---

## Workflow & naming
- **Add new references** to the working library `Code/AI-Girl/{model,scenes,clothes}/`.
- **To show one here**, copy it into `graphify-out/wiki/assets/ai-girl/...` and embed
  with bare filename: `![[door-background.png]]` (names are unique vault-wide).
- **Finished posts/renders** go in `Code/AI-Girl/renders/`.
- Descriptive kebab-case names: `door-full-open-light-tidy.png`.

[[../index|Vault Index]]
