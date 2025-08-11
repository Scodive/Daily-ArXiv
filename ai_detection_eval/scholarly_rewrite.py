from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from typing import List, Tuple

import requests

try:
    import jieba  # type: ignore
    HAS_JIEBA = True
except Exception:
    HAS_JIEBA = False


SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[。！？!?…])\s*|(?<=[\.!?])\s+")


def split_sentences(text: str) -> List[str]:
    parts = re.split(SENTENCE_SPLIT_PATTERN, text.strip())
    return [p for p in parts if p]


def tokenize_cn_en(text: str) -> List[str]:
    if HAS_JIEBA:
        return [w.strip() for w in jieba.lcut(text) if w.strip()]
    # fallback：英文词、数字、单个中文
    words: List[str] = []
    words.extend(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", text))
    words.extend(re.findall(r"\d+", text))
    words.extend(re.findall(r"[\u4e00-\u9fff]", text))
    return words


def split_overlong_sentence(sent: str, max_tokens: int = 35) -> List[str]:
    tokens = tokenize_cn_en(sent)
    if len(tokens) <= max_tokens:
        return [sent]
    # 仅基于标点尝试分段
    parts = re.split(r"([，,；;：:———])", sent)
    # 合并标点
    merged: List[str] = []
    buf = ""
    for i in range(0, len(parts), 2):
        chunk = parts[i]
        punct = parts[i + 1] if i + 1 < len(parts) else ""
        candidate = (buf + chunk + punct).strip()
        if not candidate:
            continue
        if len(tokenize_cn_en(candidate)) > max_tokens and buf:
            merged.append(buf)
            buf = (chunk + punct).strip()
        else:
            buf = candidate
    if buf:
        merged.append(buf)
    return merged if merged else [sent]


def heuristic_rewrite(text: str) -> str:
    # 非对抗：仅做句长优化与轻量净化（去多余空白）
    sentences = split_sentences(text)
    rewritten: List[str] = []
    for s in sentences:
        for piece in split_overlong_sentence(s, max_tokens=35):
            rewritten.append(piece.strip())
    return "\n".join(rewritten)


def call_gemini_rewrite(text: str, api_key: str, model: str = "gemini-2.0-flash-exp") -> str:
    # 仅用于质量与清晰度提升，不进行任何对抗检测的目标设定
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    prompt = (
        "你是学术写作助手。请在保持事实准确与语义不变的前提下，提升以下文本的清晰度、结构性、术语准确性与可读性。"
        "要求：\n"
        "- 不改变事实与结论，不杜撰数据，不加入来源不明的信息；\n"
        "- 将过长句子适度拆分，避免模板化连接词，增强逻辑衔接；\n"
        "- 改善学术表达与术语一致性；\n"
        "- 不进行任何规避或对抗检测的处理。\n\n"
        "待改进文本：\n" + text
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.4,
            "topP": 0.8,
            "topK": 40,
            "maxOutputTokens": 4096,
        },
    }
    resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return text


def process_file(input_path: Path, output_path: Path, use_llm: bool) -> None:
    text = input_path.read_text(encoding="utf-8", errors="ignore")
    interim = heuristic_rewrite(text)
    if use_llm:
        api_key = os.getenv("GEMINI_API_KEY")
        model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        if not api_key:
            raise RuntimeError("未设置 GEMINI_API_KEY 环境变量。若不想用 LLM，请添加 --no-llm 参数。")
        final_text = call_gemini_rewrite(interim, api_key=api_key, model=model)
    else:
        final_text = interim
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(final_text, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="学术写作质量增强（非对抗），支持 jieba 与可选 LLM 重写")
    parser.add_argument("input", help="输入文件或目录")
    parser.add_argument("output", help="输出文件或目录")
    parser.add_argument("--no-llm", action="store_true", help="不调用 LLM，仅进行启发式句长优化")
    args = parser.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)
    use_llm = not args.no_llm

    if in_path.is_file():
        if out_path.exists() and out_path.is_dir():
            out_file = out_path / in_path.name
        else:
            out_file = out_path
        process_file(in_path, out_file, use_llm)
    else:
        # 目录：批处理 .txt
        out_path.mkdir(parents=True, exist_ok=True)
        for p in sorted(in_path.glob("**/*.txt")):
            rel = p.relative_to(in_path)
            out_file = out_path / rel
            process_file(p, out_file, use_llm)


if __name__ == "__main__":
    main()


