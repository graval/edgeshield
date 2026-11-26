# AGENTS.md: Universal AI Assistant Instructions & Project Governance

> **To any AI coding assistant (Antigravity, Claude, Cursor, Copilot, Gemini):**  
> Read this document to understand the repository boundaries, privacy governance, zero-hallucination policies, and git branching rules.

---

## 🚫 MANDATORY DIRECTIVE: ZERO HALLUCINATIONS & ZERO UNVERIFIED ASSUMPTIONS

Every AI assistant working on this codebase MUST strictly adhere to the following rules with ZERO exceptions:

1. **NO Fabricated or Hallucinated Metadata**:
   - **NEVER** invent, extrapolate, or hallucinate author names, affiliations, co-authors, citations, bibtex entries, benchmark numbers, dataset statistics, or license terms.
   - The verified canonical authors for EdgeShield doctoral research are:
     - **Candidate / Lead Author:** Gauravkumar Raval (GLS University)
     - **Doctoral Supervisor:** Dr. Tejaskumar Bhatt (GLS University)
   - Do NOT insert any placeholder or synthetic names (e.g., "Dave, Mayank", "John Doe", or imaginary co-authors). Any publication or citation must accurately reflect Gauravkumar Raval and Dr. Tejaskumar Bhatt.

2. **NO Unverified Assumptions**:
   - Never assume missing values, parameters, hardware specs, metrics, or research facts.
   - If any fact, author, institution, paper acceptance, or configuration detail is ambiguous or not grounded in a physical file or authoritative tool output, **STOP IMMEDIATELY and ask the user for confirmation**.
   - Do NOT fill in gaps with plausible-sounding guesses.

3. **Strict Empirical Grounding**:
   - Every metric, latency figure, parameter count, memory footprint, recall, precision, and F1 score cited in papers, reports, READMEs, or dashboards must come from actual, verified execution logs (`runs/`, Kaggle kernel logs, or local benchmark JSON outputs).
   - Never generate hypothetical benchmark tables or synthetic performance comparisons.

---

## 🏛️ The 3-Tier EdgeShield Repository Architecture

This public repository (`graval/edgeshield`) represents **Tier 3** of the EdgeShield project:

* **Tier 1 (Private: `graval/slm-gpu-trainer`):** Academic Research & Defense Archive (Doctoral milestones RDC2-RDC4, grant proposals, manuscripts, rebuttal letters).
* **Tier 2 (Private: `graval/edgeshield-experiments`):** Execution & Experiment Engine (Training pipelines, checkpoint registry, Kaggle cloud runners, multi-hardware benchmark logs).
* **Tier 3 (Public: `graval/edgeshield` - THIS REPO):** Public Artifact Release containing finalized, peer-reviewed EdgeShield library code, exported ONNX INT8 models, and clean replication scripts for peer review.

---

## 🔒 Repository Privacy, Release Separation & Git Branching Governance (MANDATORY)

### 1. Repository Privacy & Confidentiality Boundary
* **Development Repository (`graval/slm-gpu-trainer`) MUST ALWAYS REMAIN STRICTLY PRIVATE**:
  - Contains research-in-progress, internal defense milestones (RDC2, RDC3, RDC4), reviewer responses, experimental scratch scripts, and institutional progress tracking.
  - **NEVER** change this repository's visibility to public.

### 2. Public Release Repository Hygiene (`graval/edgeshield`)
* **Dedicated Standalone Public Repository**: Only the dedicated public repository (`graval/edgeshield`) is public.
* **Tier 2 → Tier 3 Promotion Gate**:
  - Never push unvalidated, draft, or in-progress experiment scripts directly to `graval/edgeshield`.
  - New dataset runners and Kaggle validation pipelines MUST be executed and verified in **Tier 2 (`graval/edgeshield-experiments`)** first using the canonical suite (`EdgeShield_Kaggle_Benchmark_Suite.ipynb`), and promoted here only after metrics stabilize for publication.
  - Do NOT commit ad-hoc or temporary notebooks (such as `EdgeShield_RADAR_Validation.ipynb`) to Tier 3. Tier 3 contains only clean, finalized standalone Python replication scripts (`benchmark_edgeshield.py`, `benchmark_onnx.py`).
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
