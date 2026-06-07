# AI Girl — Decisions (the WHY)

Companion to [[../projects/AI-Girl-Pipeline|AI Girl Pipeline]] and [[../projects/AI-Girl-Catalog|Catalog]].

## Run in ComfyUI, not SD.Next
The model is **Z-Image Turbo** (NextDiT/Lumina2 DiT), not Stable Diffusion. SD.Next is built around
SD/SDXL/Flux pipelines and physically can't load it (CLIPTextModel missing → "not a complete model").
ComfyUI has native Z-Image support (`TextEncodeZImageOmni`, z_image text encoder). Decision: ComfyUI is the host.

## CFG 1 / steps 9 / sa_solver, not cfg 5 / 28 / euler
Z-Image **Turbo** is CFG-distilled — high CFG and step counts over-bake it into a cartoony, saturated look.
Confirmed correct settings from a real Civitai generation: **CFG 1, ~9 steps, sa_solver, simple**.

## Stay on Moody (don't switch to SDXL/Flux)
User wants the Moody look + realism LoRAs they saw on Civitai. Evidence (many ZImageTurbo LoRAs exist)
shows Z-Image-Turbo LoRAs train fine, overruling the usual "don't train on a Turbo/distilled model" caution.
So: keep Moody, stack realism LoRAs, and train her character LoRA for ZIT.

## Face consistency = ReActor face-swap, not Omni / IPAdapter / img2img
- **Omni reference** (Z-Image's native image conditioning) crashes the sampler on the Turbo checkpoint
  (reference_latents shape mismatch) — Turbo isn't Omni/Edit-trained.
- **IPAdapter / InstantID / PuLID** are SDXL-architecture only — don't attach to Z-Image.
- **img2img low-denoise** can't change outfit without drifting the face.
- → **ReActor** (inswapper_128) is the only single-reference option that's pose/outfit-independent.
  Accepted limit: 128px swap ≈ 90% identity. The LoRA is the permanent fix.

## insightface via 1.0.1 pure-python wheel
py3.13 + no MSVC compiler = old insightface 0.7.3 would fail to build. insightface **1.0.1** ships a
pure-python wheel → installs clean. This is what made local face-swap possible.

## One character LoRA, not separate face + body
A single balanced dataset (face close-ups + half + full body) captures identity AND proportions.
Separate face/body LoRAs conflict and add complexity for no benefit.

## Dataset: build in Leonardo, vary everything but identity, keep backgrounds simple
- Only 1 real reference exists → bootstrap a varied set in Leonardo via Character Reference.
- Vary outfit/pose/background/light so the LoRA learns *her*, not an outfit/scene. Never reuse the
  brown-turtleneck + door (that's the reference; it bakes in).
- Backgrounds mostly plain studio for close-ups; simple blurred indoor/outdoor for body shots.

## Prompts made filter-safe
Leonardo flagged some prompts. Cause = "young" + body-shape terms ("slim athletic build, narrow waist,
defined collarbones"). Fix: "woman in her mid 20s" + "slim build", drop the body-shape emphasis, soften
tank/crop → sleeveless/casual. Face identity preserved.

## On body shots, lower Character Reference strength (~0.5–0.65)
At high strength Leonardo copies the *whole* reference (brown turtleneck + door) on wider shots.
Lower strength keeps her face but lets the prompt's outfit/background win.

## Train LOCALLY on 8 GB — overturns "Civitai cloud only" (2026-06-07)
Earlier todo said local training was impractical on 8 GB VRAM → use Civitai cloud. **Wrong.** Z-Image is only
~6B params; with float8 quant + full layer-offloading + gradient checkpointing it trains fine on the 3060 Ti
(~3 h, 2500 steps). Did it locally, free. Full recipe: [[../ai-girl-lora-training-local|Training Runbook]].

## Trainer = Ostris AI Toolkit, not kohya
kohya/sd-scripts have no Z-Image support. ai-toolkit has native `arch: "zimage"`. That's the only mature local
option for ZIT LoRAs right now.

## Train on base Z-Image-Turbo, not the Moody single-file
ai-toolkit loads the transformer via `from_pretrained(subfolder="transformer")` → needs a diffusers-format
repo, which `moodyProMix_zitV11DPO.safetensors` (single-file ComfyUI format) is not. So train on
`Tongyi-MAI/Z-Image-Turbo` (base) and stack the LoRA on Moody at inference — the normal train-on-base pattern.
It still learns her cleanly.

## Use Python 3.12 for the trainer venv, not 3.13
ai-toolkit's pinned deps (scipy 1.12, old numpy via librosa/numba) have no cp313 wheels → source builds fail
with no compiler. 3.12 has wheels for the whole stack. See [[../mistakes]].

## Caption = trigger + variable attributes only (strip identity)
Captions keep `a1g1rl` + outfit/pose/background/light and DROP the face/hair/skin description, so the trigger
token absorbs her identity rather than binding it to generic words. Standard character-LoRA practice.

[[../index|Vault Index]]
