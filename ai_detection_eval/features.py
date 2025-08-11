from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple

try:
    import jieba  # type: ignore
    HAS_JIEBA = True
except Exception:
    HAS_JIEBA = False


CHINESE_CHAR_PATTERN = re.compile(r"[\u4e00-\u9fff]")
EN_WORD_PATTERN = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
NUM_PATTERN = re.compile(r"\d+")
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[。！？!?…])\s*|(?<=[\.!?])\s+")


EN_STOPWORDS_SMALL = {
    "the", "a", "an", "and", "or", "but", "if", "then", "else", "for", "of", "on", "in", "to",
    "with", "by", "from", "as", "at", "is", "are", "was", "were", "be", "been", "being", "that",
    "this", "it", "its", "we", "you", "they", "he", "she", "i"
}

CN_STOPWORDS_SMALL = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "也", "对", "与", "及", "并", "或", "而", "被"
}


def split_sentences(text: str) -> List[str]:
    parts = re.split(SENTENCE_SPLIT_PATTERN, text.strip())
    return [p for p in parts if p]


def basic_tokenize(text: str) -> List[str]:
    # 优先用 jieba 分词中文，英文/数字用正则
    words: List[str] = []
    if HAS_JIEBA:
        # jieba 对非中文会原样输出，后续再细分
        rough = list(jieba.cut(text, cut_all=False))
        for token in rough:
            # 对 token 再拆分出英文词与数字
            words.extend(EN_WORD_PATTERN.findall(token))
            words.extend(NUM_PATTERN.findall(token))
            # 保留中文字符序列（去除空白和标点）
            chinese_only = "".join(CHINESE_CHAR_PATTERN.findall(token))
            if chinese_only:
                # 对中文，保留词粒度（jieba 已切好）
                words.append(chinese_only)
    else:
        # 无 jieba 时，回退：英文词、数字、单个中文字符
        words.extend(EN_WORD_PATTERN.findall(text))
        words.extend(NUM_PATTERN.findall(text))
        words.extend(CHINESE_CHAR_PATTERN.findall(text))
    return [w for w in words if w.strip()]


def character_level_counts(text: str) -> Tuple[int, int, int, int]:
    total_chars = len(text)
    chinese_chars = len(CHINESE_CHAR_PATTERN.findall(text))
    english_chars = len(re.findall(r"[A-Za-z]", text))
    digit_chars = len(NUM_PATTERN.findall(text))
    return total_chars, chinese_chars, english_chars, digit_chars


def compute_ngram_repetition(tokens: List[str], n: int = 3) -> float:
    if len(tokens) < n:
        return 0.0
    ngrams = [" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]
    counts = Counter(ngrams)
    total = len(ngrams)
    repeated = sum(c for c in counts.values() if c > 1)
    return repeated / total if total else 0.0


def safe_div(n: float, d: float) -> float:
    return (n / d) if d else 0.0


@dataclass
class TextFeatures:
    # 基本计数
    num_characters: int
    num_chinese_characters: int
    num_english_characters: int
    num_digits: int
    num_tokens: int
    num_unique_tokens: int
    num_hapax_tokens: int
    num_sentences: int

    # 比率与分布
    average_sentence_length_tokens: float
    average_word_length_characters: float
    type_token_ratio: float
    hapax_ratio: float
    punctuation_ratio: float
    digit_ratio: float
    uppercase_ratio: float
    chinese_character_ratio: float
    english_character_ratio: float

    # 模板化与重复
    repeated_trigram_ratio: float
    repeated_fourgram_ratio: float

    # 停用词比例（粗略）
    english_stopword_ratio: float
    chinese_stopword_ratio: float

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


def extract_text_features(text: str) -> TextFeatures:
    sentences = split_sentences(text)
    tokens = basic_tokenize(text)
    num_tokens = len(tokens)

    total_chars, cn_chars, en_chars, digit_chars = character_level_counts(text)

    num_unique = len(set(tokens))
    token_counts = Counter(tokens)
    num_hapax = sum(1 for t, c in token_counts.items() if c == 1)

    sentence_lengths = [len(basic_tokenize(s)) for s in sentences] if sentences else []
    avg_sentence_len = sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0.0

    avg_word_len = sum(len(t) for t in tokens) / num_tokens if num_tokens else 0.0

    # 停用词比例（非常小的内置表，避免依赖下载）
    en_tokens_lower = [t.lower() for t in tokens]
    en_stop_count = sum(1 for t in en_tokens_lower if t in EN_STOPWORDS_SMALL)
    cn_stop_count = sum(1 for t in tokens if t in CN_STOPWORDS_SMALL)

    # 标点比例
    punct_count = len(re.findall(r"[\.,;:!?，。；：！？、—\-]", text))

    # 大写比例（英文）
    uppercase_count = len(re.findall(r"[A-Z]", text))

    repeated_tri = compute_ngram_repetition(tokens, n=3)
    repeated_four = compute_ngram_repetition(tokens, n=4)

    return TextFeatures(
        num_characters=total_chars,
        num_chinese_characters=cn_chars,
        num_english_characters=en_chars,
        num_digits=digit_chars,
        num_tokens=num_tokens,
        num_unique_tokens=num_unique,
        num_hapax_tokens=num_hapax,
        num_sentences=len(sentences),
        average_sentence_length_tokens=avg_sentence_len,
        average_word_length_characters=avg_word_len,
        type_token_ratio=safe_div(num_unique, num_tokens),
        hapax_ratio=safe_div(num_hapax, num_tokens),
        punctuation_ratio=safe_div(punct_count, total_chars),
        digit_ratio=safe_div(digit_chars, total_chars),
        uppercase_ratio=safe_div(uppercase_count, total_chars),
        chinese_character_ratio=safe_div(cn_chars, total_chars),
        english_character_ratio=safe_div(en_chars, total_chars),
        repeated_trigram_ratio=repeated_tri,
        repeated_fourgram_ratio=repeated_four,
        english_stopword_ratio=safe_div(en_stop_count, num_tokens),
        chinese_stopword_ratio=safe_div(cn_stop_count, num_tokens),
    )


def extract_features_for_texts(texts: List[str]) -> List[Dict[str, float]]:
    return [extract_text_features(t).to_dict() for t in texts]


