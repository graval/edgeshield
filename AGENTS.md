# AGENTS.md: Universal AI Assistant Instructions & Project Governance

> **To any AI coding assistant (Antigravity, Claude, Cursor, Copilot, Gemini):**  
> Read this document to understand the repository boundaries, privacy governance, and git branching policies.

---

## 🔒 Repository Privacy, Release Separation & Git Branching Governance (MANDATORY)

### 1. Repository Privacy & Confidentiality Boundary
* **Development Repository (`graval/slm-gpu-trainer`) MUST ALWAYS REMAIN STRICTLY PRIVATE**:
  - Contains research-in-progress, internal defense milestones (RDC2, RDC3, RDC4), reviewer responses, experimental scratch scripts, and institutional progress tracking.
  - **NEVER** change this repository's visibility to public.

### 2. Public Release Repository Hygiene (`graval/edgeshield`)
* **Dedicated Standalone Public Repository**: Only the dedicated public repository (`graval/edgeshield`) is public.
* **STRICT PROHIBITION ON INTERNAL MILESTONES**:
  - **NEVER** commit, push, or copy internal university/doctoral milestone materials (`rdc2/`, `rdc3/`, `rdc4/`, defense slide decks, viva notes, reviewer response letters, candidate progress tracking, internal trial notebooks) into the public repository.
  - The public repository must contain ONLY finalized, peer-reviewed, reproducible artifacts:
    1. Core EdgeShield library and runtime architecture (`edgeshield/`)
    2. Model weights and ONNX exports (`models/` - INT8 & FP32)
    3. Benchmark replication scripts (`benchmark_edgeshield.py`, `benchmark_onnx.py`)
    4. Empirical evaluation results and validation reports
    5. Accepted and published peer-reviewed paper sources and preprints (only post-formal acceptance/publication)
    6. Clean, user-facing documentation (`README.md`, `LICENSE`, quickstart guide)

### 3. Git Branching & Merging Policy (Zero Direct Commits to `main`)
* **NEVER commit directly to the `main` branch** in any repository.
* **Mandatory Feature Branching Workflow**:
  1. Always branch off `main` to a dedicated feature/fix branch:
     `git checkout -b <type>/<description>` (e.g., `feat/edgeshield-slm-framework`, `fix/table-metrics`)
  2. Perform and verify all commits on the feature branch.
  3. Push the feature branch to remote:
     `git push origin <type>/<description>`
  4. Merge into `main` via formal merge or Pull Request:
     `git checkout main; git merge <type>/<description>; git push origin main`
  5. Return to the working feature branch for subsequent tasks.

---

## 🏗️ Core Architecture & Paradigms

### Dual-Model Architecture
* **Classifier SLM (`microsoft/deberta-v3-small`, 44M params):** Stream A (LSA) evaluates host telemetry with sub-20ms latency.
* **Behavioral Pattern Detector (Stream B BPD):** Transformer backbone with Attention Threat Scoring Head for pre-encryption ransomware warning.
* **Tiered Selective Gating:** Fast-path allowlist & Shannon entropy triage running in $48.55\ \mu\text{s}$.
* **Quantization:** Dynamic INT8 post-training quantization via ONNX Runtime (AVX-VNNI acceleration).
