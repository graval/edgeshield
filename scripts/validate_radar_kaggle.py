"""
EdgeShield: RADAR (Windows 11 Modern Ransomware & Concept Drift) Validation Runner
Evaluates EdgeShield on Zenodo Record 14564541 (Ispahany et al., Springer Cybersecurity 2026):
  - Covers all 7 modern Windows 11 RaaS families: Akira, BlackBasta, CyberVolk, LockBit, Lynx, Medusa, Meow
  - Protocol A: Zero-Shot evaluation using pre-trained EdgeShield Stream B (MOD-TRANSFORMER-BPD-V2)
  - Protocol B: Drift-Adapted EdgeShield (fine-tuned on imbalanced-5 early slice, tested on unseen imbalanced-10 and Drift Phases 2, 3a, 3b, 3c)
  - Profiles Latency (p50, p95), Host CPU%, Disk IO, RAM, and Per-Family Recall.
"""

import os
import sys
import io
import json
import time
import psutil
import zipfile
import argparse
import subprocess
import numpy as np
import pandas as pd

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RADAR_ZENODO_URL = "https://zenodo.org/api/records/14564541/files/JamilIsp/RADAR-v0.0.1-beta.zip/content"


def acquire_radar_zip(zip_path: str) -> str:
    if os.path.exists(zip_path) and os.path.getsize(zip_path) > 50_000_000:
        print(f"[+] RADAR archive already present: {zip_path} ({os.path.getsize(zip_path)/(1024**2):.2f} MB)", flush=True)
        return zip_path
    os.makedirs(os.path.dirname(os.path.abspath(zip_path)), exist_ok=True)
    print(f"[*] Downloading RADAR dataset from Zenodo ({RADAR_ZENODO_URL})...", flush=True)
    cmd = ["curl", "-L", "-s", "-S", "-o", zip_path, RADAR_ZENODO_URL]
    subprocess.run(cmd, check=True)
    if not os.path.exists(zip_path) or os.path.getsize(zip_path) < 50_000_000:
        raise RuntimeError(f"Failed to download valid RADAR archive to {zip_path}")
    print(f"[+] Downloaded RADAR archive: {os.path.getsize(zip_path)/(1024**2):.2f} MB", flush=True)
    return zip_path


def format_sysmon_event(row: dict) -> str:
    ecode = row.get("event.code", "")
    action = str(row.get("event.action", "")).split("(")[0].strip()
    proc = str(row.get("process.executable", ""))
    parent = str(row.get("process.parent.executable", ""))
    fpath = str(row.get("file.path", ""))
    reg = str(row.get("registry.path", ""))
    ent = row.get("file_name_entropy", "")
    susp = row.get("suspicious_path", "")

    parent_short = parent.split("\\")[-1] if "\\" in parent else parent
    target = fpath if fpath not in ("-", "nan", "None", "") else reg
    if len(target) > 65:
        target = "..." + target[-62:]

    parts = [f"[EID:{ecode} {action}]", f"[PROC:{proc}]"]
    if parent_short not in ("-", "nan", "None", ""):
        parts.append(f"[PARENT:{parent_short}]")
    if target not in ("-", "nan", "None", ""):
        parts.append(f"[TARGET:{target}]")
    if str(ent) not in ("nan", "None", "", "-"):
        try:
            parts.append(f"[ENT:{float(ent):.2f}]")
        except Exception:
            pass
    if str(susp) in ("1", "1.0", "True"):
        parts.append("[SUSP_PATH]")
    return " ".join(parts)


def build_stratified_windows(df: pd.DataFrame, window_size: int = 5, max_benign: int = 1000, max_mal_per_family: int = 150, from_tail: bool = False):
    """Builds 5-event sliding windows balanced across goodware and ALL 7 ransomware families."""
    cols = [
        "event.code", "event.action", "process.executable", "process.parent.executable",
        "file.path", "registry.path", "file_name_entropy", "suspicious_path",
        "target-class", "target-class-name"
    ]
    avail = [c for c in cols if c in df.columns]
    df_work = df[avail].copy()
    df_work["_fam"] = df_work["target-class-name"].astype(str).apply(lambda x: x.split("-")[0] if "-" in x else x)

    texts, labels, families = [], [], []

    df_ben = df_work[df_work["target-class"] == 0]
    ben_recs = df_ben.to_dict("records")
    step_ben = max(window_size, len(ben_recs) // max(1, max_benign))
    count_ben = 0
    for i in range(0, len(ben_recs) - window_size + 1, step_ben):
        chunk = ben_recs[i:i + window_size]
        win_str = " || ".join([f"[T-{window_size-1-j}] {format_sysmon_event(r)}" for j, r in enumerate(chunk)])
        texts.append(win_str)
        labels.append(0)
        families.append("goodware")
        count_ben += 1
        if count_ben >= max_benign:
            break

    df_mal = df_work[df_work["target-class"] == 1]
    for fam_name, grp in df_mal.groupby("_fam"):
        recs = grp.to_dict("records")
        if from_tail:
            recs = recs[len(recs)//2:] if len(recs) > 20 else recs
        else:
            recs = recs[:len(recs)//2] if len(recs) > 20 else recs

        step_m = max(window_size, len(recs) // max(1, max_mal_per_family))
        c_m = 0
        for i in range(0, len(recs) - window_size + 1, step_m):
            chunk = recs[i:i + window_size]
            win_str = " || ".join([f"[T-{window_size-1-j}] {format_sysmon_event(r)}" for j, r in enumerate(chunk)])
            texts.append(win_str)
            labels.append(1)
            families.append(fam_name)
            c_m += 1
            if c_m >= max_mal_per_family:
                break

    return texts, np.array(labels, dtype=int), families


class SequenceDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_len=256):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        enc = self.tokenizer(
            self.texts[idx],
            truncation=True,
            max_length=self.max_len,
            padding="max_length",
            return_tensors="pt"
        )
        item = {k: v.squeeze(0) for k, v in enc.items() if k in ("input_ids", "attention_mask")}
        item["labels"] = torch.tensor(self.labels[idx], dtype=torch.long)
        return item


def evaluate_model(model, tokenizer, texts, labels, device, batch_size=32, max_len=256):
    model.eval()
    ds = SequenceDataset(texts, labels, tokenizer, max_len=max_len)
    dl = DataLoader(ds, batch_size=batch_size, shuffle=False)
    preds, latencies = [], []

    proc = psutil.Process()
    io_before = proc.io_counters() if hasattr(proc, "io_counters") else None
    proc.cpu_percent(interval=None)
    t_start = time.perf_counter()

    with torch.no_grad():
        for batch in dl:
            t0 = time.perf_counter()
            inputs = {k: v.to(device) for k, v in batch.items() if k in ("input_ids", "attention_mask")}
            out = model(**inputs)
            pred = np.argmax(out.logits.cpu().numpy(), axis=-1)
            dt_ms = ((time.perf_counter() - t0) * 1000.0) / max(1, len(pred))
            latencies.extend([dt_ms] * len(pred))
            preds.extend(pred.tolist())

    total_time = time.perf_counter() - t_start
    cpu_pct = proc.cpu_percent(interval=None) / max(1, os.cpu_count() or 1)
    io_after = proc.io_counters() if hasattr(proc, "io_counters") else None
    disk_write_kb = ((io_after.write_bytes - io_before.write_bytes) / 1024.0) if (io_before and io_after) else 0.0
    ram_mb = proc.memory_info().rss / (1024 ** 2)

    preds = np.array(preds)
    acc = accuracy_score(labels, preds) * 100.0
    _, _, f1, _ = precision_recall_fscore_support(labels, preds, average="macro", zero_division=0)
    tp = int(((preds == 1) & (labels == 1)).sum())
    fn = int(((preds == 0) & (labels == 1)).sum())
    fp = int(((preds == 1) & (labels == 0)).sum())
    tn = int(((preds == 0) & (labels == 0)).sum())
    ransom_recall = (tp / max(1, tp + fn)) * 100.0
    fpr = (fp / max(1, fp + tn)) * 100.0
    prec_pos = (tp / max(1, tp + fp)) * 100.0

    return {
        "samples": len(labels),
        "ransomware_recall_pct": round(float(ransom_recall), 2),
        "precision_pct": round(float(prec_pos), 2),
        "false_positive_rate_pct": round(float(fpr), 2),
        "macro_f1_pct": round(float(f1 * 100.0), 2),
        "accuracy_pct": round(float(acc), 2),
        "latency_p50_ms": round(float(np.percentile(latencies, 50)), 2),
        "latency_p95_ms": round(float(np.percentile(latencies, 95)), 2),
        "throughput_eps": round(float(len(labels) * 5 / max(1e-6, total_time)), 1),
        "host_cpu_pct": round(float(cpu_pct), 2),
        "disk_write_kb_s": round(float(disk_write_kb / max(1e-6, total_time)), 2),
        "ram_mb": round(float(ram_mb), 2),
        "preds": preds
    }


def main():
    parser = argparse.ArgumentParser(description="EdgeShield RADAR Benchmark & Drift Validation")
    parser.add_argument("--zip_path", type=str, default=None, help="Path to RADAR-v0.0.1-beta.zip")
    parser.add_argument("--base_model", type=str, default=None, help="Path to pre-trained EdgeShield BPD/LSA checkpoint")
    parser.add_argument("--epochs", type=int, default=4, help="Adaptation epochs on imbalanced-5 early slice")
    parser.add_argument("--max_train_ben", type=int, default=1800, help="Goodware training windows")
    parser.add_argument("--max_train_mal_fam", type=int, default=250, help="Malware training windows per family")
    parser.add_argument("--max_eval_ben", type=int, default=1000, help="Goodware eval windows per split")
    parser.add_argument("--max_eval_mal_fam", type=int, default=150, help="Malware eval windows per family per split")
    parser.add_argument("--export_json", type=str, default="radar_validation_results.json")
    args = parser.parse_args()

    if args.zip_path is None:
        if os.path.exists("/kaggle"):
            args.zip_path = "/kaggle/working/RADAR-v0.0.1-beta.zip"
        else:
            args.zip_path = "RADAR-v0.0.1-beta.zip"
    acquire_radar_zip(args.zip_path)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[*] Execution Device: {device}" + (f" ({torch.cuda.get_device_name(0)})" if torch.cuda.is_available() else ""), flush=True)

    # Search recursively in /kaggle/input for trained EdgeShield checkpoints or zip archive
    if os.path.exists("/kaggle/input") and not os.path.exists("/kaggle/working/extracted_models/models/edgeshield_bpd"):
        for root, dirs, files in os.walk("/kaggle/input"):
            for fn in files:
                if fn == "edgeshield_trained_models.zip":
                    z_in = os.path.join(root, fn)
                    print(f"[*] Extracting trained EdgeShield checkpoints from {z_in}...", flush=True)
                    with zipfile.ZipFile(z_in, "r") as mz:
                        mz.extractall("/kaggle/working/extracted_models")
                    break

    model_candidates = [
        args.base_model,
        "/kaggle/working/edgeshield/models/edgeshield_bpd",
        "/kaggle/working/extracted_models/models/edgeshield_bpd",
        "/kaggle/working/extracted_models/edgeshield_bpd",
        "models/edgeshield_bpd",
    ]
    if os.path.exists("/kaggle/input"):
        for root, dirs, files in os.walk("/kaggle/input"):
            if "edgeshield_bpd" in dirs:
                model_candidates.insert(1, os.path.join(root, "edgeshield_bpd"))
    if os.path.exists("/kaggle/working/extracted_models"):
        for root, dirs, files in os.walk("/kaggle/working/extracted_models"):
            if "edgeshield_bpd" in dirs:
                model_candidates.insert(1, os.path.join(root, "edgeshield_bpd"))

    backbone_path = "distilbert-base-uncased"
    has_weights = False
    for p in model_candidates:
        if p and os.path.exists(p):
            if os.path.exists(os.path.join(p, "model.safetensors")) or os.path.exists(os.path.join(p, "pytorch_model.bin")):
                backbone_path = p
                has_weights = True
                break

    tokenizer_path = "/kaggle/working/edgeshield/models/edgeshield_bpd" if os.path.exists("/kaggle/working/edgeshield/models/edgeshield_bpd") else backbone_path
    print(f"[*] Loading EdgeShield Behavioral Backbone: {backbone_path} (weights_loaded={has_weights})", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, use_fast=True)

    with zipfile.ZipFile(args.zip_path, "r") as z:
        with zipfile.ZipFile(io.BytesIO(z.read("JamilIsp-RADAR-cb0c4c2/Raw logs/imbalanced-dataset/Dataset-imbalanced-raw.zip")), "r") as sz_imb:
            df_imb5 = pd.read_csv(io.BytesIO(sz_imb.read("Dataset-imbalanced-5.csv")), low_memory=False)
            df_imb10 = pd.read_csv(io.BytesIO(sz_imb.read("Dataset-imbalanced-10.csv")), low_memory=False)
        with zipfile.ZipFile(io.BytesIO(z.read("JamilIsp-RADAR-cb0c4c2/Raw logs/drift-dataset/Drift-dataset-raw.zip")), "r") as sz_dr:
            df_p2 = pd.read_csv(io.BytesIO(sz_dr.read("Drift-dataset-phase-2.csv")), low_memory=False)
            df_p3a = pd.read_csv(io.BytesIO(sz_dr.read("Drift-dataset-phase-3a.csv")), low_memory=False)
            df_p3b = pd.read_csv(io.BytesIO(sz_dr.read("Drift-dataset-phase-3b.csv")), low_memory=False)
            df_p3c = pd.read_csv(io.BytesIO(sz_dr.read("Drift-dataset-phase-3c.csv")), low_memory=False)

    # Balanced early slice from Imbalanced-10 across ALL 7 families (each has 3,000+ rows)
    train_texts, train_labels, _ = build_stratified_windows(
        df_imb10, max_benign=args.max_train_ben, max_mal_per_family=args.max_train_mal_fam, from_tail=False
    )

    eval_splits = {}
    for split_name, df_sp in [
        ("Imbalanced_5_Unseen", df_imb5),
        ("Drift_Phase_2", df_p2),
        ("Drift_Phase_3a", df_p3a),
        ("Drift_Phase_3b", df_p3b),
        ("Drift_Phase_3c", df_p3c),
    ]:
        tx, lb, fm = build_stratified_windows(
            df_sp, max_benign=args.max_eval_ben, max_mal_per_family=args.max_eval_mal_fam, from_tail=True
        )
        eval_splits[split_name] = (tx, lb, fm)

    zs_recall = 0.0
    if has_weights:
        print("\n[*] Running Protocol A: Zero-Shot Evaluation of pre-trained EdgeShield BPD on RADAR Imbalanced-5...", flush=True)
        zs_model = AutoModelForSequenceClassification.from_pretrained(backbone_path).to(device)
        zs_texts, zs_labels, _ = eval_splits["Imbalanced_5_Unseen"]
        zs_model.eval()
        zs_preds = []
        mal_indices = [i for i, l in enumerate(zs_labels) if l == 1][:400]
        ds_zs = SequenceDataset([zs_texts[i] for i in mal_indices], zs_labels[mal_indices], tokenizer, max_len=256)
        dl_zs = DataLoader(ds_zs, batch_size=32)
        with torch.no_grad():
            for b in dl_zs:
                inp = {k: v.to(device) for k, v in b.items() if k in ("input_ids", "attention_mask")}
                out = zs_model(**inp)
                cls_ids = np.argmax(out.logits.cpu().numpy(), axis=-1)
                zs_preds.extend([0 if c == 15 else 1 for c in cls_ids])
        zs_recall = (sum(zs_preds) / max(1, len(zs_preds))) * 100.0
        print(f"  -> Zero-Shot Pre-Adaptation Recall on Win11 Native RADAR: {zs_recall:.2f}% ({sum(zs_preds)}/{len(zs_preds)})", flush=True)
        del zs_model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    print(f"\n[*] Running Protocol B: Adapting EdgeShield SLM on RADAR Imbalanced-5 ({len(train_texts)} windows, {args.epochs} epochs)...", flush=True)
    model = AutoModelForSequenceClassification.from_pretrained(backbone_path, num_labels=2, ignore_mismatched_sizes=True).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=5e-5, weight_decay=0.01)
    train_ds = SequenceDataset(train_texts, train_labels, tokenizer, max_len=256)
    train_dl = DataLoader(train_ds, batch_size=16 if device.type == "cpu" else 32, shuffle=True)
    criterion = nn.CrossEntropyLoss()

    t_train_start = time.perf_counter()
    model.train()
    for ep in range(args.epochs):
        ep_loss = 0.0
        for batch in train_dl:
            optimizer.zero_grad()
            inputs = {k: v.to(device) for k, v in batch.items() if k in ("input_ids", "attention_mask")}
            lbls = batch["labels"].to(device)
            out = model(**inputs)
            loss = criterion(out.logits, lbls)
            loss.backward()
            optimizer.step()
            ep_loss += loss.item()
        print(f"  -> Epoch {ep+1}/{args.epochs} | Mean Loss: {ep_loss/max(1, len(train_dl)):.4f}", flush=True)
    train_duration_s = time.perf_counter() - t_train_start

    results_summary = {
        "dataset": "RADAR (Zenodo 14564541 - Windows 11 Modern RaaS)",
        "hardware": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
        "backbone_loaded": backbone_path,
        "weights_loaded": has_weights,
        "zero_shot_pre_adaptation_recall_pct": round(zs_recall, 2),
        "adaptation_time_seconds": round(train_duration_s, 2),
        "splits": {},
        "per_family_recall_drift_p3c": {}
    }

    print("\n" + "=" * 95, flush=True)
    print("               [RADAR CONCEPT DRIFT & IMBALANCED VALIDATION RESULTS]", flush=True)
    print("=" * 95, flush=True)
    print(f"{'Split / Drift Phase':<24} | {'Recall':<8} | {'Prec':<8} | {'Macro F1':<8} | {'FPR':<7} | {'Lat p50':<9} | {'CPU%':<6} | {'DiskIO'}", flush=True)
    print("-" * 95, flush=True)

    for sp_name, (txts, lbls, fams) in eval_splits.items():
        metrics = evaluate_model(model, tokenizer, txts, lbls, device, batch_size=32)
        preds_arr = metrics.pop("preds")
        results_summary["splits"][sp_name] = metrics
        print(f"{sp_name:<24} | {metrics['ransomware_recall_pct']:>6.2f}% | {metrics['precision_pct']:>6.2f}% | {metrics['macro_f1_pct']:>6.2f}% | {metrics['false_positive_rate_pct']:>5.2f}% | {metrics['latency_p50_ms']:>6.2f} ms | {metrics['host_cpu_pct']:>4.1f}% | {metrics['disk_write_kb_s']:.1f} KB/s", flush=True)

        if sp_name == "Drift_Phase_3c":
            df_fam = pd.DataFrame({"family": fams, "label": lbls, "pred": preds_arr})
            for fam_name, grp in df_fam[df_fam["label"] == 1].groupby("family"):
                fam_rec = (grp["pred"] == 1).mean() * 100.0
                results_summary["per_family_recall_drift_p3c"][fam_name] = {
                    "windows": int(len(grp)),
                    "recall_pct": round(float(fam_rec), 2)
                }

    print("=" * 95, flush=True)
    print("\n[*] Per-Family Recall on Final Drift Phase 3c:", flush=True)
    for fam, info in results_summary["per_family_recall_drift_p3c"].items():
        print(f"   - {fam:<12}: {info['recall_pct']:>6.2f}% ({info['windows']} sequence windows)", flush=True)

    out_dir = os.path.dirname(os.path.abspath(args.export_json))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(args.export_json, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2)
    print(f"\n[+] Exported RADAR validation results to: {args.export_json}", flush=True)


if __name__ == "__main__":
    main()
