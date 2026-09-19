import json
import re

from .cache import load_cache, save_cache
from .claude_client import ask_claude, MODEL_NAME


SYSTEM_PROMPT = """
You are an opinion claim extraction system for CommentMap.

CommentMap does not summarize comments.
Its purpose is to identify distinct opinions and arguments expressed
across comments.

Extract claims from each comment.

Rules:
1. A single comment may contain zero, one, or multiple claims.
2. Split a comment into multiple claims when it expresses multiple
   independent opinions.
3. Do not invent information that is not present in the comment.
4. Ignore content that contains no meaningful opinion or argument,
   such as simple timestamps or meaningless reactions.
5. Keep each claim short, clear, and self-contained.
6. Preserve the language of the original comment.
7. Do not merge claims from different comments.
8. Do not decide whether claims from different comments are similar.
   That will be handled in a later stage.
9. Do not classify sentiment or stance at this stage.
10. A claim should be understandable without reading the original
    comment whenever the original comment provides enough information.
11. Avoid ambiguous references such as "it", "they", "this", "that",
    "this video", "this product", or similar expressions when their
    referent can be identified from the comment.
12. Replace an ambiguous reference with its actual subject only when
    that subject is explicitly identifiable from the comment.
13. Never guess or add missing context merely to make a claim
    self-contained.
14. Preserve the meaning, certainty, and strength of the original
    statement. Do not strengthen speculation into fact.
15. Return JSON only. Do not include Markdown or explanations.

Output format:

{
  "results": [
    {
      "comment_id": "original comment id",
      "claims": [
        {
          "text": "self-contained claim"
        }
      ]
    }
  ]
}
"""


def build_prompt(comments):
    """
    Claude에 전달할 댓글 데이터를 만든다.
    """

    comment_data = []

    for comment in comments:
        comment_data.append({
            "id": comment["id"],
            "text": comment.get(
                "analysis_text",
                comment.get("text", "")
            )
        })

    return (
        "Extract claims from the following comments.\n\n"
        + json.dumps(
            comment_data,
            ensure_ascii=False,
            indent=2
        )
    )


def clean_json_response(response_text):
    """
    Claude가 JSON을 Markdown 코드 블록으로 감싼 경우
    코드 블록을 제거한다.
    """

    text = response_text.strip()

    code_block_match = re.fullmatch(
        r"```(?:json)?\s*(.*?)\s*```",
        text,
        flags=re.DOTALL | re.IGNORECASE
    )

    if code_block_match:
        text = code_block_match.group(1).strip()

    return text


def parse_response(response_text):
    """
    Claude의 JSON 응답을 Python 객체로 변환하고
    기본적인 응답 구조를 검증한다.
    """

    cleaned_response = clean_json_response(
        response_text
    )

    try:
        data = json.loads(
            cleaned_response
        )

    except json.JSONDecodeError as error:
        raise ValueError(
            "Claude 응답을 JSON으로 변환하지 못했습니다.\n"
            f"응답 내용:\n{response_text}"
        ) from error

    if not isinstance(data, dict):
        raise ValueError(
            "Claude 응답의 최상위 구조가 객체가 아닙니다."
        )

    results = data.get(
        "results"
    )

    if not isinstance(results, list):
        raise ValueError(
            "Claude 응답에 results 리스트가 없습니다."
        )

    validated_results = []

    for result in results:

        if not isinstance(result, dict):
            continue

        comment_id = result.get(
            "comment_id"
        )

        claims = result.get(
            "claims",
            []
        )

        if not comment_id:
            continue

        if not isinstance(claims, list):
            continue

        valid_claims = []

        for claim in claims:

            if not isinstance(claim, dict):
                continue

            text = claim.get(
                "text",
                ""
            ).strip()

            if not text:
                continue

            valid_claims.append({
                "text": text
            })

        validated_results.append({
            "comment_id": comment_id,
            "claims": valid_claims
        })

    return validated_results


def make_cache_data(comments):
    """
    claim extraction 결과를 구분하기 위한
    캐시 입력 데이터를 만든다.

    모델이나 프롬프트가 변경되면
    기존 캐시를 사용하지 않는다.
    """

    comment_data = []

    for comment in comments:
        comment_data.append({
            "id": comment["id"],
            "text": comment.get(
                "analysis_text",
                comment.get("text", "")
            )
        })

    return {
        "model": MODEL_NAME,
        "system_prompt": SYSTEM_PROMPT,
        "comments": comment_data
    }


def extract_claims_with_claude(comments):
    """
    하나의 댓글 batch에서 claim을 추출한다.

    동일한 입력의 결과가 캐시에 있으면
    Claude API를 다시 호출하지 않는다.
    """

    if not comments:
        return []

    cache_data = make_cache_data(
        comments
    )

    cached_result = load_cache(
        "claim_extractor",
        cache_data
    )

    if cached_result is not None:
        print(
            "Claim extraction: 캐시 사용 (API 호출 없음)"
        )

        return cached_result

    print(
        "Claim extraction: Claude API 호출"
    )

    prompt = build_prompt(
        comments
    )

    response = ask_claude(
        prompt=prompt,
        system_prompt=SYSTEM_PROMPT,
        max_tokens=2048
    )

    result = parse_response(
        response
    )

    save_cache(
        "claim_extractor",
        cache_data,
        result
    )

    return result