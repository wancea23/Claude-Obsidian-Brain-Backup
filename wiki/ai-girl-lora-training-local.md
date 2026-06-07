# AI Girl — Local LoRA Training Runbook (Z-Image Turbo, 8 GB)

Runbook for the character LoRA we trained **locally** on an RTX 3060 Ti (8 GB). Companion to
[[projects/AI-Girl-Pipeline|Pipeline]] · [[decisions/AI-Girl-decisions|Decisions]] · [[todo/AI-Girl-todo|Todo]].
Done 2026-06-07. **Overturns** the earlier "must use Civitai cloud, local impractical on 8 GB" plan — it worked locally.

## Result
- **Output**: `a1g1rl_zimage_lora_v1.safetensors` (85 MB, LoRA dim 16). Trigger word: **`a1g1rl`**.
- **Installed to**: `C:\Users\johns\ComfyUI-Shared\models\loras\a1g1rl_zimage_lora_v1.safetensors`.
- Intermediate checkpoints (steps 1250–2250) kept in `C:\Users\johns\ai-toolkit\output\a1g1rl_zimage_lora_v1\`.
- Identity holds across close-up / half-body / full-body samples. ~3 h wall-clock, 2500 steps, ~4–5 s/it.

## Trainer: Ostris AI Toolkit (NOT kohya)
- kohya/sd-scripts do **not** support Z-Image yet. **ai-toolkit** has native `arch: "zimage"` support
  (`extensions_built_in/diffusion_models/z_image/`, diffusers `ZImagePipeline` + `ZImageTransformer2DModel`).
- Cloned to `C:\Users\johns\ai-toolkit` (OUTSIDE OneDrive — never put venvs/models in the synced folder).

## Python 3.12, not 3.13 (the big gotcha — see [[mistakes]])
- System python is 3.13; ai-toolkit deps (`scipy==1.12.0`, old `numpy` via librosa/numba) have **no cp313
  wheels** → pip tries to compile from source → fails (no Fortran/MSVC). Fought it twice, then switched.
- Fix: build venv with **`py -3.12 -m venv venv`** (3.12 was already installed via the py launcher).
- Also bumped `scipy==1.12.0` → `scipy>=1.14.1` in `requirements.txt` (kept after the 3.12 switch).
- Install: `torch==2.9.1 torchvision==0.24.1 torchaudio==2.9.1 --index-url .../whl/cu128`, then `-r requirements.txt`.

## Base model: train on base Z-Image-Turbo, apply on Moody
- ai-toolkit's loader uses `from_pretrained(subfolder="transformer")` → needs a **diffusers-format repo**,
  NOT the single-file `moodyProMix_zitV11DPO.safetensors` (ComfyUI format). So we can't train on Moody directly.
- Trained on **`Tongyi-MAI/Z-Image-Turbo`** (ungated, auto-downloaded, has transformer/text_encoder/vae/tokenizer).
- The LoRA still stacks on Moody at inference — standard "train on base, apply on merge" pattern. Confirmed it learns her.

## Captioning (character-LoRA strategy)
- One `.txt` per image in `Code/AI-Girl/dataset/`, generated from `PROMPTS-easy.txt`.
- **Strip the identity block** (face/eyes/hair/skin) and quality tags; keep only what VARIES
  (outfit, pose, background, light) and **prefix `a1g1rl`**. Forces the trigger token to absorb her face
  instead of binding it to words like "hazel eyes". (Image 36's prompt was blank in the file → captioned by hand.)

## 8 GB config (key knobs)
Config: `C:\Users\johns\ai-toolkit\config\a1g1rl_zimage.yaml`. What makes it fit 8 GB:
- `quantize: true` + `qtype: qfloat8`, `quantize_te: true` (float8 transformer + Qwen3 TE).
- `low_vram: true`, `layer_offloading: true`, `*_percent: 1.0` (stream all blocks from CPU).
- `gradient_checkpointing: true`, `batch_size: 1`, `cache_text_embeddings: true`, resolution `[512, 768]`.
- `optimizer: adamw8bit`, `lr: 1e-4`, `steps: 2500`, network lora `linear/alpha: 16`.
- Z-Image is only ~6B params (vs Qwen-Image 20B) → 8 GB is comfortable with this stack.

## Re-run / resume
```
cd C:\Users\johns\ai-toolkit
set HF_HUB_ENABLE_HF_TRANSFER=1
.\venv\Scripts\python.exe -u run.py config/a1g1rl_zimage.yaml
```
Samples land in `output/a1g1rl_zimage_lora_v1/samples/` (`__000NNNNNN_{0..3}.jpg` = step + prompt index).
If over-baked at 2500, try the step-2000/2250 checkpoints at lower strength.

## Use in ComfyUI
- `LoraLoader` on top of Moody, strength ~0.8–1.0, put `a1g1rl` in the prompt.
- Keep ZIT settings: CFG 1, ~9 steps, sa_solver, simple. Stack realism LoRAs (see Pipeline §4) after it.

[[index|Vault Index]]
