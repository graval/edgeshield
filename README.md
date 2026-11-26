# EdgeShield: Dual-Stream SLM Architecture for Pre-Encryption Ransomware Defense

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![ONNX Runtime](https://img.shields.io/badge/ONNX_Runtime-INT8_Quantized-orange.svg)](https://onnxruntime.ai/)

EdgeShield is an edge-native cybersecurity framework that uses a dual-stream Small Language Model (SLM) architecture and tiered selective gating to intercept ransomware and lateral movement before cryptographic execution begins.

Designed specifically for resource-constrained edge computing environments, EdgeShield operates efficiently on commodity edge CPUs without requiring discrete hardware accelerators (GPUs or NPUs).

---

## Key Highlights

- **Dual-Stream Detection**:
  - **Stream A (LSA)**: Log Sequence Analyzer based on `microsoft/deberta-v3-small` (44M backbone parameters, 142M total deployed including 128k embeddings) fine-tuned for host audit telemetry and lateral movement detection.
  - **Stream B (BPD)**: Behavioral Pattern Detector featuring an attention-based threat scoring head for pre-encryption file system access anomalies.
- **Tiered Selective Gating**:
  - Two-stage filter combining known-process fast-path allowlisting with sliding-window Shannon file entropy triage.
  - Executes in **48.55 &mu;s**, filtering out **94.75%** of benign telemetry while escalating 100% of suspicious attack sequences to the SLM.
- **Edge Deployment & Quantization**:
  - Post-training dynamic INT8 quantization deployed via ONNX Runtime with AVX-VNNI acceleration.
  - Inference latency of **15.30 ms** on standard physical laptop CPUs (Intel Core Ultra 7 255H) with an active process working set of **318.5 MB RAM** (versus 2,400+ MB for 3.8B LLMs, an ~8x memory reduction).

---

## 🗺️ Version & Research Lineage Roadmap

To maintain strict academic rigor and avoid confusion between previously accepted conference findings and ongoing journal research, this repository follows a versioned lineage:

| Version | Milestone / Paper | Status | Key Artifacts & Capabilities |
| :--- | :--- | :--- | :--- |
| **`v1.0.0-temscon`** | **IEEE TEMSCON-ASPAC 2026** (Oct 2026) | **Accepted & In Press** (Paper ID #171) | • Dual-Stream SLM Architecture (Stream A LSA + Stream B BPD)<br>• Baseline lateral movement & ransomware early warning formulation<br>• Initial LMD-2023 evaluation on commodity CPU |
| **`v2.0.0-current`** (`main`) | **Proposed Journal Expansion** (Target: TBD) | **Manuscript in Preparation / Target: TBD** | • **Tiered Selective Gating** ($48.55\ \mu\text{s}$ microsecond triage, 94.75% benign filtering)<br>• **Cross-Hardware Benchmarks** (Intel Core Ultra 7 255H, Intel Arc 140T, Kaggle Xeon, Dual Tesla T4)<br>• **Out-of-Distribution Generalization** (DARPA OpTC, RADAR Windows 11 Concept Drift, Mordor)<br>• **Dynamic INT8 Quantization** with AVX-VNNI acceleration |

> **Reproducibility Note:** To inspect or replicate *only* the baseline conference artifact, checkout the tag:  
> `git checkout v1.0.0-temscon`

---

## Empirical Benchmark Performance

Empirical evaluation on held-out test splits across Darpa OpTC, RansomHub, and LockBit 3.0 telemetry streams:

| Architecture / Model | Parameters | Quantization | Accuracy (%) | Macro F1 (%) | Precision (%) | Recall (%) | FPR (%) | CPU Latency (ms) | Memory RSS (MB) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **EdgeShield (Ours)** | **44M (142M\*)** | **INT8** | **99.67%** | **99.67%** | **99.67%** | **99.67%** | **0.40%** | **15.30** | **318.5** |
| EdgeShield (FP32) | 44M (142M\*) | FP32 | 99.67% | 99.67% | 99.67% | 99.67% | 0.40% | 27.60 | 540 |
| Llama-3.2 (1B) | 1.23B | INT4 | 97.80% | 97.45% | 98.10% | 96.80% | 1.80% | 148.50 | 780 |
| Gemma-2 (2.6B) | 2.61B | INT4 | 98.15% | 97.89% | 98.30% | 97.50% | 1.45% | 312.20 | 1,620 |
| Phi-3 Mini (3.8B) | 3.82B | INT4 | 98.42% | 98.15% | 98.60% | 97.70% | 1.20% | 465.10 | 2,340 |
| Mistral NeMo (12B) | 12.2B | INT4 | 98.90% | 98.72% | 99.10% | 98.35% | 0.85% | 1,420.00 | 7,450 |

> **Note on Model Architecture & Memory Footprint:** DeBERTa-v3 Small comprises a 44M-parameter encoder backbone plus 98M embedding parameters for its 128k multilingual vocabulary (142M total deployed parameters). Process memory reflects peak active working set (RSS) profiled under continuous ONNX Runtime inference on a physical Intel Core Ultra 7 255H workstation.

### Multi-Hardware Deployment Matrix

Empirical evaluation across physical endpoint hardware and cloud execution profiles:

| Hardware Environment | Processor / Silicon | Execution Provider | INT8 Batch Latency | INT8 Streaming Latency | Peak Process Working Set (RSS) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Physical Laptop CPU** | **Intel Core Ultra 7 255H (16 Cores)** | `CPUExecutionProvider` | **15.30 ms (64.9 FPS)** | **20.45 ms (LSA) / 12.48 ms (BPD)** | **320.55 MB** |
| **Physical Laptop GPU** | **Intel Arc 140T GPU (8 Xe-Cores)** | `DmlExecutionProvider` (DirectML) | **17.73 ms (LSA)** | **35.40 ms (Combined)** | **643.14 MB** |
| **Cloud Virtual CPU** | **Intel Xeon @ 2.20GHz (4 vCPUs)** | `CPUExecutionProvider` | **99.94 ms (10.0 FPS)** | **24.80 ms (Streaming)** | **350.20 MB** |
| **Cloud Accelerator** | **NVIDIA Tesla T4 (Linux VM)** | `CPUExecutionProvider` / CUDA | **67.18 ms (14.8 FPS)** | **1.82 ms (Streaming)** | **402.10 MB** |

---

## Repository Structure

```
edgeshield/
├── edgeshield/                     # Core EdgeShield Python library
│   ├── bpd/                        # Stream B: Behavioral Pattern Detector
│   ├── lsa/                        # Stream A: Log Sequence Analyzer
│   ├── correlation/                # Multi-stream correlation engine
│   ├── edge_deploy/                # ONNX Runtime INT8 deployment runner
│   ├── selective_gating.py         # 2-stage tiered selective gating module
│   ├── pipeline.py                 # Integrated inference and triage pipeline
│   └── taxonomy.py                 # Threat taxonomy mappings
├── docs/                           # Empirical validation diagrams and benchmarks
│   └── selective_gating_benchmark_plots_laptop_cpu.png
├── models/                         # Model tokenizers and configurations
│   ├── edgeshield_lsa/             # LSA model configuration and vocab
│   └── edgeshield_bpd/             # BPD model configuration and vocab
├── scripts/                        # Evaluation and benchmarking scripts
│   ├── benchmark_edgeshield.py     # End-to-end framework benchmark
│   ├── benchmark_onnx.py           # ONNX latency and throughput benchmark
│   ├── export_onnx.py              # Export PyTorch models to ONNX INT8
│   └── run_full_pipeline.py        # Full pipeline demonstration
├── benchmark_results.json          # Empirical benchmark evaluation results
├── BENCHMARK_VALIDATION_REPORT.md  # Detailed benchmark validation report
├── requirements.txt                # Python dependencies
└── LICENSE                         # Apache 2.0 License
```

---

## Quickstart

### 1. Installation

```bash
git clone https://github.com/graval/edgeshield.git
cd edgeshield
pip install -r requirements.txt
```

### 2. Run the Benchmark

To replicate the empirical evaluation on commodity CPU hardware:

```bash
python scripts/benchmark_edgeshield.py
```

### 3. Run Pipeline Evaluation with Selective Gating

```bash
python scripts/run_full_pipeline.py
```

---

## 📦 Model Checkpoints & Pre-Trained Weights

Model checkpoints and quantized ONNX artifacts are hosted on **Hugging Face Hub** and **Kaggle Models** with tagged release revisions to prevent confusion between versions:

* **Hugging Face Hub Model Repository:** [`graval/edgeshield`](https://huggingface.co/graval/edgeshield)
  * **Tag `v1.0-temscon`:** Baseline PyTorch checkpoints for Stream A (LSA) and Stream B (BPD) corresponding to the IEEE TEMSCON-ASPAC 2026 conference publication.
  * **Tag `v2.0-int8-quantized` (`main`):** Production INT8 ONNX models with AVX-VNNI acceleration and Tiered Selective Gating configurations.
* **Kaggle Models Repository:** [`gauravr1/edgeshield-models`](https://www.kaggle.com/models/gauravr1/edgeshield-models)
  * Versioned bundle used directly in Kaggle Cloud benchmark validation kernels.

---

## 📚 Citation

If you find this research or code useful, please cite the appropriate publication corresponding to the version or components used:

### 1. Conference Baseline (Preliminary Dual-Stream SLM Architecture)

```bibtex
@inproceedings{raval2026edgeshield_temscon,
  author    = {Raval, Gauravkumar and Bhatt, Tejaskumar},
  title     = {{EdgeShield: Lightweight Dual-Stream Small Language Model Architecture for Pre-Encryption Ransomware Defense on Edge Devices}},
  booktitle = {Proceedings of the 5th IEEE Technology and Engineering Management Conference - Asia Pacific (TEMSCON-ASPAC)},
  year      = {2026},
  note      = {Accepted and In Press}
}
```

### 2. Proposed Extended Journal Article (Full Framework, Tiered Gating & Multi-Hardware Benchmarks)

```bibtex
@article{raval2026edgeshield_journal,
  author  = {Raval, Gauravkumar and Bhatt, Tejaskumar},
  title   = {{EdgeShield: A High-Throughput Edge-Native Small Language Model Architecture for Pre-Encryption Ransomware Early Warning and Lateral Movement Interception}},
  journal = {Target Journal: TBD (Manuscript in Preparation)},
  year    = {2026},
  note    = {Under Submission / Pre-submission Draft}
}
```
