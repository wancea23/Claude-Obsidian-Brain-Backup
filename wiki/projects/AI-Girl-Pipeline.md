# AI Girl — Generation Pipeline & LoRA Training

> How the AI-Girl persona is actually generated locally, and the plan to train her own
> character LoRA. Companion to [[AI-Girl-Catalog|AI Girl Catalog]] (the reference library).
> **Started**: 2026-06-06

**See also**: [[AI-Girl-Catalog|reference catalog]] · [[../decisions/AI-Girl-decisions|decisions (why)]] · [[../todo/AI-Girl-todo|todo / dataset status]] · [[AI-Cosplay-Model-Room]] · [[LowBitrate-Blur]]

---

## TL;DR
The model the user downloaded (**Moody Pro Mix V11 DPO**) is **Z-Image Turbo**, NOT Stable Diffusion,
so it crashed in SD.Next. It runs in **ComfyUI**. Face consistency is currently done with a
**ReActor face-swap**; the real goal is a **character LoRA** trained from a Leonardo-built dataset.

## 1. The original problem
- User installed **SD.Next** (vladmandic/automatic) at `F:\automatic`; selecting the model crashed
  with `Failed to load CLIPTextModel ... is not a complete model`.
- Root cause: `moodyProMix_zitV11DPO.safetensors` is a **Z-Image Turbo (ZIT)** model — Alibaba Tongyi
  **NextDiT / Lumina2-based DiT**, with a Qwen3-4B text encoder. Not SD1.5/SDXL/Flux. SD.Next can't run it.
- Quick fix applied: pointed SD.Next's `config.json` at `v1-5-pruned-fp16-emaonly` (a real, complete SD1.5)
  so SD.Next at least works for SD models.

## 2. ComfyUI setup (where it actually runs)
- **App**: ComfyUI Desktop, `F:\ComfyUI\Comfy Desktop`. **Core**: `C:\Users\johns\ComfyUI-Installs\ComfyUI\ComfyUI`.
- **venv python 3.13.12**: `...\ComfyUI\.venv\Scripts\python.exe`. **Server**: http://127.0.0.1:8188.
- **Models dir** (NOT on F:): `C:\Users\johns\ComfyUI-Shared\models\`
  - `diffusion_models/moodyProMix_zitV11DPO.safetensors` (12 GB — the ZIT model)
  - `text_encoders/qwen_3_4b.safetensors` (8 GB — from HF Comfy-Org/z_image_turbo)
  - `vae/ae.safetensors` (0.3 GB)
- Z-Image is **built into ComfyUI core** — node `TextEncodeZImageOmni`. `CLIPLoader` type=`stable_diffusion`
  works (it auto-detects qwen3_4b → z_image text encoder as long as type isn't flux/flux2).

## 3. CORRECT turbo settings (critical)
Z-Image Turbo is CFG-distilled. Use **low** settings (confirmed from a Civitai gen):
- **CFG 1**, **steps ~9**, sampler **sa_solver**, scheduler **simple**.
- (Early mistake: cfg 5 / 28 steps / euler → over-baked, cartoony. Fixed.)

## 4. Realism comes from LoRAs (to download)
Base Moody alone is glossy/idealized. A Civitai reference gen used Moody + a stack of **Z-Image-Turbo LoRAs**
for photorealism. Download checklist (into `ComfyUI-Shared/models/loras/`):

| Resource | Type | Version | Weight used | Have? |
|---|---|---|---|---|
| Moody Pro Mix | checkpoint | ZIT V11 DPO | — | ✅ yes (`diffusion_models/moodyProMix_zitV11DPO.safetensors`) |
| Realistic Snapshot (Z-Image-Turbo) | LoRA | v5 (Real Life) | 0.6 | ⬜ download |
| Beautify – Supermodel face (BSF) | LoRA | ZImageTurbo | 1.0 | ⬜ download |
| Detail slider for Z-Image | LoRA | v1.0 | 0.4 | ⬜ download |
| Detailed Perfection (Hands + Feet + Face + skin) | LoRA | Perfection zit v1.1 | 1.3 | ⬜ download |

Notes:
- These are general photoreal/quality enhancers (skin, hands/feet, detail) — useful for **any** realistic gen.
- The reference gen also used one explicitly-NSFW LoRA (`[ZIT] Mystic XXX v7.0 @ 0.7`); not part of the
  SFW identity pipeline and not catalogued here as a build target.
- Gen settings on that reference: **CFG 1, ~9 steps, sa_solver, simple** (matches §3).
- ComfyUI API needs real `LoraLoader` nodes — it does **not** parse A1111 `<lora:...>` text syntax, so each
  LoRA above becomes a chained `LoraLoader` node with the weight shown.
- **Our trained character LoRA**: `a1g1rl_zimage_lora_v1.safetensors` (trigger `a1g1rl`) — the identity layer
  that replaces face-swap; stack it on top of Moody with the realism LoRAs above.

## 5. Face consistency — ReActor face-swap
- Z-Image **Omni image-reference** does NOT work on the Turbo checkpoint (reference_latents crash the sampler).
- So: generate scene from text → **ReActor** swaps the reference face on.
- Node: `custom_nodes/ComfyUI-ReActor`; `inswapper_128.onnx` in install `models/insightface/`.
- **Key unlock**: `insightface 1.0.1` installs as a pure-python wheel on py3.13 (no compiler). onnxruntime 1.26 too.
- Limitation user noticed: inswapper is 128px → face ~90% match (rounder chin, bigger eyes). LoRA is the real fix.

## 6. Helper scripts (in `C:\Users\johns\ComfyUI-Shared\`)
Driven via the ComfyUI API (no MCP exists). Defaults already set to cfg 1 / steps 9 / sa_solver / simple.
- `gen.py "prompt" [--w --h --steps --cfg --sampler --seed --batch]` — plain text2img.
- `gen_face.py "prompt" [--ref model-reference.jpg --restore none]` — text2img + ReActor face-swap (main one).

## 7. The character LoRA (the real goal)
- **One** character LoRA (not separate face/body). Dataset = ~30 images, identity constant, vary everything else.
- Dataset built in **Leonardo AI** (Character Reference on `model-reference.jpg`).
- Prompt list: `Code/AI-Girl/PROMPTS-easy.txt` (36 shots, plain copy-paste; made **filter-safe** — dropped
  "young"/body-shape terms that tripped Leonardo's filter).
- Training: **DONE locally** on the 8 GB 3060 Ti (Ostris AI Toolkit, base `Tongyi-MAI/Z-Image-Turbo`, 2500 steps).
  Output `a1g1rl_zimage_lora_v1.safetensors` in `ComfyUI-Shared/models/loras/`. (Earlier "Civitai-cloud-only /
  local impractical" assumption was wrong.) Full recipe: [[../ai-girl-lora-training-local|Local LoRA Training Runbook]].
- Status & next steps: see [[../todo/AI-Girl-todo|todo]].

[[../index|Vault Index]]
