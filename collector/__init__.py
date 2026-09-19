from .clean import clean_comments
from .youtube import fetch_comments


def collect(
    url: str,
    max_comments: int | None = None,
    min_meaningful_chars: int = 2,
) -> list[dict]:
    """
    최종 공개 함수.

    YouTube URL
        -> 댓글 수집
        -> 전처리
        -> contracts/comments.schema.json 형식의 list[dict]
    """
    raw_comments = fetch_comments(
        url=url,
        max_comments=max_comments,
    )

    return clean_comments(
        raw_comments,
        min_meaningful_chars=min_meaningful_chars,
    )


__all__ = ["collect"]
