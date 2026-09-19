import re
import unicodedata

import emoji

_WHITESPACE_RE = re.compile(r"\s+")
_URL_RE = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
_LONG_REPEAT_RE = re.compile(r"(.)\1{9,}", re.DOTALL)


def normalize_text(text: str) -> str:
    """
    비교/분석하기 좋게 최소한만 정규화합니다.
    원문의 의미를 바꾸는 적극적인 교정은 하지 않습니다.
    """
    text = unicodedata.normalize("NFKC", str(text))
    text = text.replace("\x00", "")
    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip()


def _meaningful_char_count(text: str) -> int:
    return sum(1 for char in text if char.isalnum())


def is_too_short(text: str, min_meaningful_chars: int = 2) -> bool:
    """
    한글/영문/숫자 등 의미 있는 문자가 너무 적으면 제거합니다.
    기본값 2이므로 '굿', 'ㅇㅇ' 정도는 남고 한 글자 반응은 제거됩니다.
    """
    return _meaningful_char_count(text) < min_meaningful_chars


def is_emoji_only(text: str) -> bool:
    """
    이모지를 제거한 뒤 글자/숫자가 하나도 없으면 emoji-only 댓글로 봅니다.
    """
    without_emoji = emoji.replace_emoji(text, replace="")
    return _meaningful_char_count(without_emoji) == 0


def is_spam(text: str) -> bool:
    """
    MVP용 보수적인 스팸 필터입니다.
    정상 댓글을 과하게 버리지 않도록 명백한 경우만 제거합니다.
    """
    urls = _URL_RE.findall(text)

    # 링크가 2개 이상이면 광고성 가능성이 높다고 보고 제거
    if len(urls) >= 2:
        return True

    # 링크 하나만 있고, 링크를 제외하면 의미 있는 내용이 거의 없는 경우
    if len(urls) == 1:
        without_url = _URL_RE.sub("", text)
        if _meaningful_char_count(without_url) < 2:
            return True

    # 같은 문자가 지나치게 길게 반복되는 댓글
    if _LONG_REPEAT_RE.search(text):
        return True

    return False


def clean_comments(
    comments: list[dict],
    min_meaningful_chars: int = 2,
) -> list[dict]:
    """
    중복 / 스팸 / emoji-only / 너무 짧은 댓글을 제거합니다.

    출력 객체는 schema에 맞춰 id, text, likes, time만 유지합니다.
    """
    cleaned: list[dict] = []
    seen_texts: set[str] = set()

    for comment in comments:
        text = normalize_text(comment.get("text", ""))

        if not text:
            continue

        if is_emoji_only(text):
            continue

        if is_too_short(text, min_meaningful_chars=min_meaningful_chars):
            continue

        if is_spam(text):
            continue

        # 대소문자/공백 차이만 있는 사실상 같은 댓글 제거
        duplicate_key = _WHITESPACE_RE.sub(" ", text).casefold()

        if duplicate_key in seen_texts:
            continue

        seen_texts.add(duplicate_key)

        cleaned.append(
            {
                "id": str(comment["id"]),
                "text": text,
                "likes": int(comment.get("likes", 0)),
                "time": str(comment["time"]),
            }
        )

    return cleaned
