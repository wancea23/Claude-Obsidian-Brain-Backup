# AI Girl — Todo / Dataset Status

For [[../projects/AI-Girl-Pipeline|AI Girl Pipeline]]. Updated 2026-06-06.

## LoRA dataset progress
Prompt list: `Code/AI-Girl/PROMPTS-easy.txt` (36 shots). Images saved to `Code/AI-Girl/datafolder/` as `1..N.jpg`.

- [x] **1–36 generated** in Leonardo — Parts 1–3 all done, including full-body 27–36.
- [x] **Image 27 fix** — was thigh-cropped; regenerated full head-to-feet (front-loaded framing + footwear).
- [x] Shipped all 36 (decided natural angle/light variation is fine for a LoRA — not "drift").

### Quality flags to fix while generating
- [ ] **Lower Character Reference strength to ~0.5–0.65 on body shots** — 15/16/17 reverted to the
  brown turtleneck + door scene at high strength.
- [ ] **Stop adding turtlenecks** — already 5 (ref + 1, 3, 9, 15). Enough.
- [ ] Grey hoodie (5, 17) and door background (ref, 16, 17) also at quota.
- [ ] Prefer fresh outfits (dress, blazer, blouse, coat) + non-studio/non-door backgrounds.

## Pipeline next steps
- [ ] Download the **realism LoRAs** into `models/loras/` (Realistic Snapshot ZIT v5, Beautify BSF,
  Detailed Perfection, Detail slider, [ZIT] Mystic XXX). Then wire `LoraLoader` nodes into the gen scripts.
- [ ] Optional: GFPGAN face-restore (~340 MB) for sharper ReActor swaps (`--restore GFPGANv1.4.pth`).
- [ ] Optional: composite her into the specific `AI-Girl/scenes/door/*` backgrounds.

## LoRA training — DONE (2026-06-07) ✅
- [x] Captioned with trigger **`a1g1rl`** (identity-stripped). Kept all 36 (no cull needed).
- [x] Trained **locally on the 8 GB 3060 Ti** via Ostris AI Toolkit, base `Tongyi-MAI/Z-Image-Turbo`,
  2500 steps. (The old "Civitai cloud, local impractical" plan was wrong — see Runbook.)
- [x] Output `a1g1rl_zimage_lora_v1.safetensors` installed to `ComfyUI-Shared/models/loras/`.
- Full recipe: [[../ai-girl-lora-training-local|Local LoRA Training Runbook]].

## Next steps
- [ ] In ComfyUI: chain `LoraLoader` (a1g1rl @ ~0.8–1.0) on Moody; put `a1g1rl` in prompt; CFG 1 / 9 steps / sa_solver.
- [ ] Download the realism LoRAs (checklist in [[../projects/AI-Girl-Pipeline|Pipeline]] §4) and stack after a1g1rl.
- [ ] Test identity likeness on varied SFW prompts (outfits/settings); if 2500 is over-baked, try step-2000/2250.
- [ ] Now that the LoRA exists, the face-swap (ReActor) step can be dropped.

[[../index|Vault Index]]
