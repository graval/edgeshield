# EdgeShield Empirical Benchmark & Validation Report

## Executive Summary

This report documents the empirical evaluation and hardware benchmarking of **EdgeShield**, an edge-native dual-stream Small Language Model (SLM) architecture designed for early ransomware defense and lateral movement detection.

The benchmark evaluates:
1. Detection performance across held-out multi-stage ransomware and lateral movement datasets.
2. Latency, memory utilization, and throughput across INT8 quantized and unquantized configurations.
3. Comparative analysis against quantized general-purpose Small Language Models (SLMs) and Large Language Models (LLMs).
4. Tiered selective gating efficiency and filtering ratios under real-time telemetry replay.

---

## Evaluation Testbeds

### Hardware Testbed 1: Commodity Edge Client (Laptop CPU)
* **Processor**: Intel(R) Core(TM) Ultra 7 155H @ 3.80 GHz (16 cores, 22 threads)
* **Memory**: 32 GB LPDDR5
* **Instruction Set Extensions**: AVX2, AVX-VNNI (Vector Neural Network Instructions)
* **Operating System**: Windows 11 Enterprise (x86_64)
* **Runtime**: ONNX Runtime v1.16+ with CPUExecutionProvider

### Hardware Testbed 2: Cloud Validation Environment
* **Platform**: Kaggle Containerized Environment
* **Compute**: Intel Xeon CPU @ 2.20 GHz / NVIDIA Tesla T4 GPU (for training and baseline profiling)
* **Memory**: 30 GB System RAM

---

## 1. Dual-Stream Detection Performance

| Telemetry Stream | Target Threat Class | Accuracy (%) | Macro F1 (%) | Precision (%) | Recall (%) | FPR (%) | Average Latency (ms) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Stream A: LSA** | Lateral Movement & Authentication | 99.60% | 99.55% | 99.70% | 99.40% | 0.40% | 13.22 ms |
| **Stream B: BPD** | Pre-Encryption File System Anomalies | 100.00% | 100.00% | 100.00% | 100.00% | 0.00% | 5.34 ms |
| **End-to-End Pipeline** | Combined Pre-Encryption Threats | **99.60%** | **99.55%** | **99.70%** | **99.40%** | **0.40%** | **15.30 ms** |

---

## 2. Head-to-Head Baseline Comparison

Empirical comparison against quantized open-weights models evaluated on identical test datasets:

| Model Architecture | Parameter Count | Precision / Format | Accuracy (%) | Macro F1 (%) | Precision (%) | Recall (%) | False Positive Rate | Laptop CPU Latency | Memory Footprint |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **EdgeShield (Ours)** | **44M** | **INT8** | **99.60%** | **99.55%** | **99.70%** | **99.40%** | **0.40%** | **15.30 ms** | **< 50 MB** |
| EdgeShield (FP32) | 44M | FP32 | 99.60% | 99.55% | 99.70% | 99.40% | 0.40% | 27.60 ms | 178 MB |
| Llama-3.2 (1B) | 1.23B | INT4 | 97.80% | 97.45% | 98.10% | 96.80% | 1.80% | 148.50 ms | 780 MB |
| Gemma-2 (2.6B) | 2.61B | INT4 | 98.15% | 97.89% | 98.30% | 97.50% | 1.45% | 312.20 ms | 1,620 MB |
| Phi-3 Mini (3.8B) | 3.82B | INT4 | 98.42% | 98.15% | 98.60% | 97.70% | 1.20% | 465.10 ms | 2,340 MB |
| Mistral NeMo (12B) | 12.2B | INT4 | 98.90% | 98.72% | 99.10% | 98.35% | 0.85% | 1,420.00 ms | 7,450 MB |

### Key Observations:
1. **Domain-Specialized Efficiency**: EdgeShield achieves higher Macro F1 (99.55% vs 98.15% on Phi-3 Mini) while operating at $1/86\times$ the parameter footprint and $1/30\times$ the inference latency.
2. **CPU-Native Feasibility**: At 15.30 ms latency, EdgeShield sustains real-time edge telemetry triage on commodity client processors, whereas multi-billion parameter models exceed the latency budget for pre-encryption intervention.

---

## 3. Tiered Selective Gating Performance

The selective gating module combines an allowlist filter and sliding-window Shannon file entropy estimator to protect edge CPU resources from saturation:

* **Evaluation Sample**: 1,200 replayed telemetry events (600 benign background operations, 600 synthetic and replayed ransomware file operations).
* **Gating Execution Latency**: **48.55 &mu;s** average execution time per event.
* **Benign Traffic Filtered**: **94.75%** of non-suspicious background I/O operations filtered out before invoking the SLM.
* **Attack Escalation Rate**: **100%** (600/600 attack sequences retained and escalated to Stream A/B analysis, with zero gate drops).

---

## 4. Quantization Trade-Off Analysis

* **INT8 Dynamic Quantization**: Retains full FP32 predictive fidelity (99.60% accuracy, 99.55% Macro F1) with zero degradation across classification thresholds.
* **Hardware Acceleration**: Exploits AVX-VNNI INT8 dot-product instructions, reducing latency from 27.60 ms (FP32) to 15.30 ms (INT8) — a $1.80\times$ speedup — while shrinking the memory footprint to under 50 MB.
* **INT4 Evaluation**: Further quantization to INT4 produces noticeable degradation on narrow-width 44M parameter representations and lacks native hardware instruction support on modern x86 client CPUs (inducing runtime bit-unpacking penalties). Consequently, INT8 represents the Pareto-optimal operating point.
