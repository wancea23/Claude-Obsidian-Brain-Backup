# Python — Chat History

> Log of important Claude Code sessions for this project.
> Paste key decisions, solutions, and context from past chats here.

---

## Format

```
### [YYYY-MM-DD] Session title
**What was asked**: brief description
**What was done**: summary of changes made
**Key decisions**: why X was chosen over Y
**Files changed**: list of modified files
**Outcome**: did it work? any follow-up needed?
```

---

## Sessions

### [2026-06-02] LowBitrate Blur — AI photo "phone camera" realism filter
**What was asked**: Build a script to add "low bitrate blur" so AI-generated photos stop looking too clean/spottable. Clarified later: NOT pixelation — the subtle "painted" smear a Xiaomi/phone camera makes under bad lighting.
**What was done**: Created `Python/LowBitrate Blur/lowbitrate.py`. First version used downscale + multi-pass JPEG → came out blocky/deep-fried. Reworked into two modes: `phone` (default, edge-preserving denoise smear + grain + MIUI sharpen halo, full-res, no blocking) and `compress` (the old heavy chain, kept opt-in).
**Key decisions**: Painterly look = edge-preserving smoothing, NOT compression. Approximated bilateral filter with scipy (local variance → edge weight) since no cv2. Presets clean/xiaomi/lowlight/night.
**Files changed**: `Python/LowBitrate Blur/lowbitrate.py` (new)
**Outcome**: Works, verified on synthetic test imgs — edges crisp, flats smeared, no pixelation. Follow-up offered: EXIF injection (fake phone make/model). See [[../projects/LowBitrate-Blur|LowBitrate Blur project page]].

*(No earlier sessions logged)*

---

## How to use
After finishing a session on this project, summarize it here.
Focus on: decisions made, mistakes caught, patterns that worked.

[[../projects/Python|Back to Python]] · [[../index|Vault Index]]
