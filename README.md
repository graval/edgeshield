# EdgeShield: Dual-Stream SLM Architecture for Pre-Encryption Ransomware Defense

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![ONNX Runtime](https://img.shields.io/badge/ONNX_Runtime-INT8_Quantized-orange.svg)](https://onnxruntime.ai/)

EdgeShield is an edge-native cybersecurity framework that uses a dual-stream Small Language Model (SLM) architecture and tiered selective gating to intercept ransomware and lateral movement before cryptographic execution begins.

Designed specifically for resource-constrained edge computing environments, EdgeShield operates efficiently on commodity edge CPUs without requiring discrete hardware accelerators (GPUs or NPUs).

---

## Key Highlights

- **Dual-Stream Detection**:
  - **Stream A (LSA)**: Log Sequence Analyzer based on `microsoft/deberta-v3-small` (44M parameters) fine-tuned for host audit telemetry and lateral movement detection.
  - **Stream B (BPD)**: Behavioral Pattern Detector featuring an attention-based threat scoring head for pre-encryption file system access anomalies.
- **Tiered Selective Gating**:
  - Two-stage filter combining known-process fast-path allowlisting with sliding-window Shannon file entropy triage.
  - Executes in **48.55 &mu;s**, filtering out **94.75%** of benign telemetry while escalating 100% of suspicious attack sequences to the SLM.
- **Edge Deployment & Quantization**:
  - Post-training dynamic INT8 quantization deployed via ONNX Runtime with AVX-VNNI acceleration.
  - Inference latency of **15.30 ms** on standard laptop CPUs with a working memory footprint of under **50 MB RAM**.

---

## Empirical Benchmark Performance

Empirical evaluation on held-out test splits across Darpa OpTC, RansomHub, and LockBit 3.0 telemetry streams:

| Architecture / Model | Parameters | Quantization | Accuracy (%) | Macro F1 (%) | Precision (%) | Recall (%) | FPR (%) | CPU Latency (ms) | Memory (MB) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **EdgeShield (Ours)** | **44M** | **INT8** | **99.60%** | **99.55%** | **99.70%** | **99.40%** | **0.40%** | **15.30** | **< 50** |
| EdgeShield (FP32) | 44M | FP32 | 99.60% | 99.55% | 99.70% | 99.40% | 0.40% | 27.60 | 178 |
| Llama-3.2 (1B) | 1.23B | INT4 | 97.80% | 97.45% | 98.10% | 96.80% | 1.80% | 148.50 | 780 |
| Gemma-2 (2.6B) | 2.61B | INT4 | 98.15% | 97.89% | 98.30% | 97.50% | 1.45% | 312.20 | 1,620 |
| Phi-3 Mini (3.8B) | 3.82B | INT4 | 98.42% | 98.15% | 98.60% | 97.70% | 1.20% | 465.10 | 2,340 |
| Mistral NeMo (12B) | 12.2B | INT4 | 98.90% | 98.72% | 99.10% | 98.35% | 0.85% | 1,420.00 | 7,450 |

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

## Citation

If you find this research or code useful, please cite our conference paper:

```bibtex
@inproceedings{raval2026edgeshield,
  author    = {Raval, Gauravkumar and Bhatt, Tejaskumar},
  title     = {{EdgeShield: Lightweight Dual-Stream Small Language Model Architecture for Pre-Encryption Ransomware Defense on Edge Devices}},
  booktitle = {Proceedings of the IEEE Technology and Engineering Management Conference - Asia Pacific (TEMSCON-ASPAC)},
  year      = {2026},
  note      = {Accepted and In Press}
}
```
