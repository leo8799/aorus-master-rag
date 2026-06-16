from __future__ import annotations

import re
import unicodedata

_LATIN_TOKEN_RE = re.compile(r"[a-z0-9]+(?:[.+_/-][a-z0-9]+)*")
_CJK_RE = re.compile(r"[\u3400-\u9fff]+")
_LATINISH_RE = re.compile(r"^[a-z0-9][a-z0-9 .+_/-]*[a-z0-9]$|^[a-z0-9]$")
_CJK_CHAR_RE = re.compile(r"[\u3400-\u9fff]")
_COMMON_SIMPLIFIED_TO_TRADITIONAL = str.maketrans(
    {
        "显": "顯",
        "与": "與",
        "卡": "卡",
        "变": "變",
        "压": "壓",
        "数": "數",
        "屏": "螢",
        "幕": "幕",
        "画": "畫",
        "图": "圖",
        "储": "儲",
        "备": "備",
        "电": "電",
        "池": "池",
        "量": "量",
        "处": "處",
        "理": "理",
        "器": "器",
        "内": "內",
        "存": "存",
        "连": "連",
        "接": "接",
        "端": "端",
        "摄": "攝",
        "像": "像",
        "头": "頭",
        "麦": "麥",
        "克": "克",
        "风": "風",
        "网": "網",
        "络": "路",
        "蓝": "藍",
        "牙": "牙",
        "颜": "顏",
        "色": "色",
    }
)


def fold_text(text: str) -> str:
    folded = unicodedata.normalize("NFKC", text)
    folded = folded.replace("®", "").replace("™", "")
    folded = folded.replace("×", "x").replace("：", ":")
    return folded.lower()


def char_ngrams(value: str, min_n: int = 2, max_n: int = 3) -> list[str]:
    grams: list[str] = []
    for n in range(min_n, max_n + 1):
        if len(value) < n:
            continue
        grams.extend(value[i : i + n] for i in range(0, len(value) - n + 1))
    return grams


def tokenize(text: str) -> list[str]:
    folded = fold_text(text)
    tokens = _LATIN_TOKEN_RE.findall(folded)

    for seq in _CJK_RE.findall(folded):
        tokens.extend(seq)
        tokens.extend(seq)
        tokens.extend(char_ngrams(seq, 2, 3))

    unit_matches = re.findall(
        r"\d+(?:\.\d+)?\s?(?:gb|tb|wh|w|hz|mhz|ghz|kg|mm|nits|cores|threads)",
        folded,
    )
    tokens.extend(match.replace(" ", "") for match in unit_matches)
    return tokens


def looks_latinish(text: str) -> bool:
    return bool(_LATINISH_RE.match(fold_text(text).strip()))


def contains_alias(text: str, alias: str) -> bool:
    folded_text = fold_text(text)
    folded_alias = fold_text(alias).strip()
    if not folded_alias:
        return False

    if looks_latinish(folded_alias):
        pattern = rf"(?<![a-z0-9]){re.escape(folded_alias)}(?![a-z0-9])"
        return bool(re.search(pattern, folded_text))
    return folded_alias in folded_text


def estimate_token_count(text: str) -> int:
    latin = _LATIN_TOKEN_RE.findall(fold_text(text))
    cjk_chars = re.findall(r"[\u3400-\u9fff]", text)
    punctuation = re.findall(r"[^\s\w\u3400-\u9fff]", text)
    return max(1, len(latin) + len(cjk_chars) + len(punctuation) // 2)


def contains_cjk(text: str) -> bool:
    return bool(_CJK_CHAR_RE.search(text))


def normalize_traditional_output(text: str) -> str:
    return text.translate(_COMMON_SIMPLIFIED_TO_TRADITIONAL)
