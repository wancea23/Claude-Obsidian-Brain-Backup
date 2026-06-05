# LowBitrate Blur — AI-photo "phone camera" realism filter

> CLI script that degrades too-clean (AI-generated) images so they read as
> ordinary phone photos. Defeats casual "this looks AI" eyeballing.
> **Created**: 2026-06-02

**Path**: `Code/Python/LowBitrate Blur/lowbitrate.py`
**Stack**: Python, Pillow, numpy, scipy

---

## What it does

Two modes, selected with `--mode`:

### `phone` (default) — the "painted" low-light look
Mimics phone night/low-light image processing (Xiaomi/MIUI signature).
Pipeline (`phone_look()`):
1. **Edge-preserving smooth** (`edge_preserving_smooth`) — fast bilateral-style
   "surface blur". Box-filter local variance of luminance drives a per-pixel
   weight: flats (low var) get gaussian-blurred, edges (high var) kept crisp.
   `detail` folds a fraction of original micro-detail back in.
2. **Unsharp halo** (`unsharp`) — the MIUI over-sharpen ring on edges.
3. **Chroma blur** — gentle color-channel smear (YCbCr, blur Cb/Cr only).
4. **Luma grain** — residual sensor noise added back AFTER denoise.
5. **One** high-quality JPEG pass. Full resolution kept → **no pixelation**.

Presets (subtle→strong): `clean`, `xiaomi` (default), `lowlight`, `night`.

### `compress` — heavy recompression chain (can pixelate)
The original "been-through-WhatsApp" chain: pre-blur → noise → chroma blur →
downscale → multi-pass JPEG (generation loss) → upscale → banding → final JPEG.
Presets: `light`, `whatsapp`, `facebook`, `deepfried`.

---

## Key knobs

| Mode | Flag | Meaning |
|------|------|---------|
| phone | `--smooth` | denoise smear radius (px) |
| phone | `--detail` | 0..1, higher = keeps more texture (less painted) |
| phone | `--grain` | residual grain sigma |
| phone | `--sharpen` | over-sharpen halo amount |
| both | `--chroma` | color smear radius |
| both | `--quality` | final JPEG quality |
| compress | `--downscale` `--passes` `--banding` `--noise` `--blur` | heavy-chain knobs |
| both | `--seed` | repeatable grain |

Accepts a single file or a folder (batch → `lowbitrate_out/`).

---

## Notes & Gotchas

- **The first version over-did it.** Downscale + multi-pass JPEG = blocky
  *pixelation*, which is the WRONG artifact for the "painted" phone look the
  user wanted. The fix was edge-preserving smoothing at full resolution, not
  compression. That distinction (smear vs. block) is the whole point.
- No OpenCV on this machine — bilateral is approximated with scipy
  `uniform_filter` (local variance) + `gaussian_filter`, blended by an
  edge-weight. Fast and good enough; swap to `cv2.bilateralFilter` if cv2
  ever gets installed.
- **Honest limit**: this fools humans, not necessarily AI detectors — many key
  on frequency-domain fingerprints that survive recompression. EXIF injection
  (fake phone make/model + timestamp) is often a bigger tell than pixels;
  not implemented yet (possible follow-up).

---

## Related

- [[Python|Python project hub]] (lives under `Python/`)
- [[../chat-history/Python-chats|Python chat history]]

[[../index|Vault Index]]
