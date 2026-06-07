# AI Girl — Chat History

## 2026-06-07 — Finished dataset (36), trained the character LoRA LOCALLY on 8 GB

**What we did**
- Reviewed the full **36-image** dataset (Parts 1–3 all generated, incl. the previously-missing full-body 27–36).
  Fixed image 27 (thigh-crop → full head-to-feet) by front-loading framing tokens + adding footwear to all
  full-body prompts in `PROMPTS-easy.txt`. Concluded the set is consistent enough — over-called "drift" earlier;
  angle/lighting variation is normal and good for a LoRA. Shipped all 36.
- Captioned the dataset (`Code/AI-Girl/dataset/*.txt`): identity-stripped, trigger `a1g1rl` prefixed.
- **Trained the character LoRA locally** on the RTX 3060 Ti (8 GB) — proving the old "Civitai cloud only" plan
  unnecessary. Trainer = **Ostris AI Toolkit** (kohya doesn't support Z-Image). Base = `Tongyi-MAI/Z-Image-Turbo`.
  ~3 h, 2500 steps. Output `a1g1rl_zimage_lora_v1.safetensors` → copied into `ComfyUI-Shared/models/loras/`.
  Step-2500 samples confirm strong identity across close-up/half/full body.
- Hit Python-3.13 wheel hell (scipy/numpy source builds) → rebuilt venv on **Python 3.12**. See [[../mistakes]].
- Saved the realism-LoRA **download checklist** (versions + weights) to Pipeline §4. Goal reference image is
  sexualized content — did NOT curate it into the vault or build the repro workflow (out of scope).

**Key files**
- Runbook: [[../ai-girl-lora-training-local|Local LoRA Training Runbook]] — full recipe to re-run.
- `C:\Users\johns\ai-toolkit\` — trainer, `config/a1g1rl_zimage.yaml`, `output/a1g1rl_zimage_lora_v1/`.
- `Code/AI-Girl/dataset/` — 36 images + captions.

**See**: [[../ai-girl-lora-training-local|Training Runbook]] · [[../projects/AI-Girl-Pipeline|Pipeline]] · [[../decisions/AI-Girl-decisions|Decisions]] · [[../todo/AI-Girl-todo|Todo]]

---

## 2026-06-06 — Diagnosed crash, built ComfyUI Z-Image pipeline + face-swap, started LoRA dataset

**What we did**
- Diagnosed why "Stable Diffusion" crashed: the Moody model is **Z-Image Turbo**, not SD. SD.Next can't run it.
  Patched SD.Next `config.json` to a real SD1.5 so it works for SD models.
- Stood up **ComfyUI Desktop**, placed the 3 Z-Image files (diffusion model + qwen_3_4b TE + ae VAE),
  and drove generation via the **API on :8188** with helper scripts `gen.py` / `gen_face.py`.
- Found correct **Turbo settings**: CFG 1, steps ~9, sa_solver/simple (earlier cfg 5/28/euler = cartoony).
- Installed **ReActor face-swap** (insightface 1.0.1 pure-wheel on py3.13) for single-reference face match.
- Decided the real fix is a **character LoRA**; wrote a 36-shot Leonardo prompt list
  (`Code/AI-Girl/PROMPTS-easy.txt`), made it filter-safe, added per-image outfits + poses.
- Reviewed images **1–17** (in `Code/AI-Girl/datafolder/`): high quality, strong consistent identity;
  flagged turtleneck/door reversion on body shots and the missing full-body shots.

**Key files**
- `C:\Users\johns\ComfyUI-Shared\` — gen.py, gen_face.py, models, output.
- `Code/AI-Girl/PROMPTS-easy.txt` — dataset prompts. `Code/AI-Girl/datafolder/` — generated images.

**See**: [[../projects/AI-Girl-Pipeline|Pipeline]] · [[../decisions/AI-Girl-decisions|Decisions]] · [[../todo/AI-Girl-todo|Todo]]

[[../index|Vault Index]]
