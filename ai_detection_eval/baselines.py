from __future__ import annotations

import csv
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, List, Dict

from .features import extract_text_features


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def iter_texts_from_dir(root: Path) -> Iterable[Dict[str, str]]:
    for p in sorted(root.glob("**/*.txt")):
        yield {"path": str(p), "text": read_text_file(p)}


def export_features_csv(text_items: Iterable[Dict[str, str]], out_csv: Path) -> None:
    rows: List[Dict[str, float]] = []
    meta: List[Dict[str, str]] = []
    for item in text_items:
        feats = extract_text_features(item["text"]).to_dict()
        feats_row = {**{"path": item["path"]}, **feats}
        rows.append(feats_row)
    if not rows:
        return
    headers = list(rows[0].keys())
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def main(root_dir: str, out_csv: str) -> None:
    root = Path(root_dir)
    out = Path(out_csv)
    out.parent.mkdir(parents=True, exist_ok=True)
    export_features_csv(iter_texts_from_dir(root), out)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="导出文本特征CSV（科研评测用，非对抗）")
    parser.add_argument("root_dir", help="文本目录，例如 generated_articles/")
    parser.add_argument("out_csv", help="输出CSV路径，例如 ai_detection_eval/output/features.csv")
    args = parser.parse_args()
    main(args.root_dir, args.out_csv)


