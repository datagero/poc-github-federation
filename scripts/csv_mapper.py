#!/usr/bin/env python3
import argparse
import csv
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

PROFILE_DIR_DEFAULT = ".bank-profiles"
REQUIRED_FIELDS = ["date", "description", "amount"]


def detect_profile(profile_dir: Path, bank_name: Optional[str], headers: List[str]) -> Optional[Dict]:
    if not profile_dir.exists():
        return None
    # Prefer explicit bank profile
    if bank_name:
        p = profile_dir / f"{bank_name}.json"
        if p.exists():
            return json.loads(p.read_text())
    # Fallback: try header-signature based profile
    sig = "__headers__" + "|".join(headers)
    p = profile_dir / f"{sig}.json"
    if p.exists():
        return json.loads(p.read_text())
    return None


def save_profile(profile_dir: Path, bank_name: Optional[str], headers: List[str], mapping: Dict[str, str], date_format: Optional[str]):
    profile_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "bank_name": bank_name,
        "headers": headers,
        "mapping": mapping,
        "date_format": date_format,
    }
    if bank_name:
        (profile_dir / f"{bank_name}.json").write_text(json.dumps(data, indent=2))
    # Also save a header-signature keyed profile for auto-detect
    sig = "__headers__" + "|".join(headers)
    (profile_dir / f"{sig}.json").write_text(json.dumps(data, indent=2))


def prompt_for_mapping(headers: List[str], sample_rows: List[Dict[str, str]]) -> Tuple[Dict[str, str], Optional[str]]:
    print("Unrecognized headers. Please map to required fields: date, description, amount")
    print("Available headers:")
    for idx, h in enumerate(headers):
        ex = sample_rows[0].get(h, "") if sample_rows else ""
        print(f"  [{idx}] {h} e.g. '{ex}'")

    mapping = {}
    for req in REQUIRED_FIELDS:
        while True:
            val = input(f"Map '{req}' to header name or index: ").strip()
            if val.isdigit():
                i = int(val)
                if 0 <= i < len(headers):
                    mapping[req] = headers[i]
                    break
            elif val in headers:
                mapping[req] = val
                break
            print("Invalid selection, try again.")

    # Try to infer a date format from samples
    date_format = None
    samples = [r.get(mapping["date"], "") for r in sample_rows[:5]]
    candidates = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y", "%m-%d-%Y"]
    for c in candidates:
        ok = True
        for s in samples:
            if not s:
                continue
            try:
                datetime.strptime(s, c)
            except Exception:
                ok = False
                break
        if ok:
            date_format = c
            break

    return mapping, date_format


def normalize_row(row: Dict[str, str], mapping: Dict[str, str], date_format: Optional[str]) -> Dict[str, str]:
    out = {
        "date": row.get(mapping["date"], ""),
        "description": row.get(mapping["description"], ""),
        "amount": row.get(mapping["amount"], ""),
    }
    # Normalize date to ISO if possible
    if out["date"] and date_format:
        try:
            out["date"] = datetime.strptime(out["date"], date_format).date().isoformat()
        except Exception:
            pass
    return out


def process_csv(path: Path, profile_dir: Path, bank_name: Optional[str], output: Optional[Path]) -> None:
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        rows = list(reader)

    profile = detect_profile(profile_dir, bank_name, headers)
    if profile is None:
        mapping, date_format = prompt_for_mapping(headers, rows[:5])
        save_profile(profile_dir, bank_name, headers, mapping, date_format)
    else:
        mapping = profile["mapping"]
        date_format = profile.get("date_format")

    normalized = [normalize_row(r, mapping, date_format) for r in rows]

    if output:
        with output.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["date", "description", "amount"])
            w.writeheader()
            w.writerows(normalized)
        print(f"Wrote normalized CSV to {output}")
    else:
        for r in normalized:
            print(json.dumps(r))


def process_qif(path: Path, output: Optional[Path]) -> None:
    # Minimal QIF parser: transactions separated by '^', lines start with D(date), T(amount), P(payee)
    content = path.read_text(encoding="utf-8")
    chunks = [c.strip() for c in content.split("^") if c.strip()]
    rows = []
    for c in chunks:
        d = ""; t = ""; p = ""
        for line in c.splitlines():
            if not line:
                continue
            tag = line[0]
            val = line[1:].strip()
            if tag == "D":
                d = val
            elif tag == "T":
                t = val
            elif tag == "P":
                p = val
        # Try basic date normalization (common QIF format is mm/dd'yy)
        iso = d
        for fmt in ("%m/%d'%y", "%m/%d/%Y", "%Y-%m-%d"):
            try:
                iso = datetime.strptime(d, fmt).date().isoformat()
                break
            except Exception:
                pass
        rows.append({"date": iso, "description": p, "amount": t})

    if output:
        with output.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["date", "description", "amount"])
            w.writeheader()
            w.writerows(rows)
        print(f"Wrote normalized CSV to {output}")
    else:
        for r in rows:
            print(json.dumps(r))


def main():
    ap = argparse.ArgumentParser(description="Column Mapper for CSV/QIF -> normalized transactions")
    ap.add_argument("input", help="Path to .csv or .qif file")
    ap.add_argument("--bank-name", help="Bank/profile name for saving/reuse")
    ap.add_argument("--profile-dir", default=PROFILE_DIR_DEFAULT, help="Directory to store bank profiles")
    ap.add_argument("--output", help="Optional path to write normalized CSV")
    args = ap.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        raise SystemExit(f"Input not found: {in_path}")

    profile_dir = Path(args.profile_dir)
    out_path = Path(args.output) if args.output else None

    ext = in_path.suffix.lower()
    if ext == ".csv":
        process_csv(in_path, profile_dir, args.bank_name, out_path)
    elif ext == ".qif":
        process_qif(in_path, out_path)
    else:
        raise SystemExit("Unsupported file type. Use .csv or .qif")


if __name__ == "__main__":
    main()
