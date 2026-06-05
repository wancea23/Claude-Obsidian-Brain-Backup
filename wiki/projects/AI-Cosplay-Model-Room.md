# AI Cosplay Model — Room Art-Direction & Consistency

> Notes on making an AI virtual-girl (cosplay persona) and her bedroom set
> read as a *real photo*, not AI-generated — and on keeping the set
> consistent across many scene generations.
> **Started**: 2026-06-02

**Catalog**: [[AI-Girl-Catalog|AI Girl Catalog]] (model refs, scene backgrounds, wardrobe)
**Related tool**: [[LowBitrate-Blur|LowBitrate Blur]] (phone-camera realism filter — run renders through it to kill the clean-CGI sheen)

---

## The persona
- AI virtual girl, primary activity = **cosplay**. Room should signal a working cosplayer.

## "This looks AI" tells found in the room renders
1. **Wrong-gender / too-uniform clothing rack** — original rack was all men's earth-tone coats, identical length & palette. Real girls' racks = mixed colors, lengths, garment types; women's shoes below.
2. **Uncanny wall art** — original was a symmetric grid of ~13 near-identical moody portraits of the *same person*. Nobody frames 13 selfies. Replaced with a **manga panel collage** (a real, recognizable aesthetic) → big improvement.
3. **All-beige monochrome palette** — bed, rug, walls, furniture, clothes all one muted tone. Real rooms have 1–2 "wrong" color accents.
4. **Too-clean / sparse surfaces** — empty desk, unbranded amber bottles on the nightstand, spotless floor. Lived-in clutter sells "real."
5. **Too-perfect symmetric pendant-lamp glow** on the ceiling.

## Cosplayer-identity items (strongest authenticity wins, still missing)
- **Wig head / styrofoam head with a wig** — single biggest "she cosplays" signal.
- Dress form / mannequin with a half-finished costume.
- Craft evidence: EVA foam, hot glue gun, sewing machine, fabric, thread.
- Ring light + phone tripod in a corner.
- A few figures (nendoroids) on a small shelf; pegboard of enamel pins.
- A couple of **costume pieces + a colorful wig** mixed into the rack.

## Key principle: don't max it out
A wall papered edge-to-edge ("weeb shrine") swings back into looking staged.
Real fan rooms are curated: one main series + scattered extras, plus a few
normal-girl items (skincare, plants, fairy lights).

---

## Cross-scene CONSISTENCY (important lesson)

**Diffusion will NOT reproduce fine wall detail identically across generations.**
Every render re-hallucinates the wall from scratch:
- Detailed/legible art (manga panels, posters with text/faces) → mutates,
  warps, and produces gibberish kanji + melted faces on any close shot.
- Different angle or seed → a completely different collage.

### Why the manga collage still "works"
It's **low-information decor**: the brain reads "manga wall = texture," nobody
memorizes which panels are where, so per-scene drift doesn't matter. The wide
shot hid the garbled panels. **It survives *because* it's unspecific.**

### Full-frame "edit" prompts throw away the camera
Tried to edit the **door-peek source** (img 3) — swap posters→manga, rack→wardrobe,
remove nightstand item — with the instruction *"don't go in the room / don't
change anything else."* The model **discarded the hallway POV and regenerated
the whole room from inside** (img 4: nice room, wrong shot).
- Prose like "don't change the camera" means nothing to a text-to-image model.
- A high-strength full-frame edit regenerates everything and picks the *easier*
  composition (a full room is easier to draw than a tiny dark door-sliver).
- The target region was ~8% of frame and near-black → no signal to preserve.

**Fixes:**
- **Inpaint with a mask** — mask ONLY the room visible through the door gap;
  everything outside (door, frame, hall) stays pixel-identical. Denoise ~0.6–0.75.
  (Manga will be unreadable mush at that size — fine/realistic through a dark door.)
- **Composite (recommended)** — take the good full-room render, scale down +
  darken + skew to the viewing angle, paste into the doorway gap, mask the door
  edge back over it. Bonus: the peek shot then shows *literally the same room* as
  the inside shots → real cross-scene consistency.
- Don't chase legible manga in the doorway shot; keep it the moody "room glimpsed
  from the hall," save the readable wall for close inside shots.

### Rules that follow
- Prefer **low-information / abstract** wall decor (tapestry, pegboard of pins,
  fairy lights, posters seen at an angle or partially blocked). Avoid readable
  text and detailed faces in wall art.
- **Keep camera distance** on wall-facing shots, or block the wall partially
  (wig head / shelf in front) so garbled detail is never scrutinized.
- For a **hero item that must be pixel-identical every scene** → don't trust the
  prompt; **composite the real PNG in post** (standard pro workflow). Other
  options: IP-adapter/ControlNet reference (reduces but doesn't kill drift),
  fixed seed + prompt (similar not identical), or train a **LoRA of the room**
  for scale.
- Treat the room prompt as **"vibe consistency," not "pixel consistency."**

---

## Next steps
1. Rack → women's clothing + a couple costume pieces + a colorful wig; women's shoes.
2. Add cosplay identity: **wig head**, a small figure shelf, costume on a dress form.
3. Break the beige with 1–2 color accents.
4. Clutter desk / nightstand / floor a little.
5. Run final renders through `lowbitrate.py --mode phone` to remove the CGI sheen.

[[../index|Vault Index]]
