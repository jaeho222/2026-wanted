import json
import re

from .cache import load_cache, save_cache
from .claude_client import ask_claude, MODEL_NAME


SYSTEM_PROMPT = """
You are a stance classification system for CommentMap.

For each claim, classify its stance toward the supplied topic.

Allowed labels:
- positive
- negative
- neutral

Definitions:

positive:
The claim expresses approval, support, praise, satisfaction,
preference, or a favorable evaluation toward the topic or
an aspect of the topic.

negative:
The claim expresses disapproval, criticism, rejection,
dissatisfaction, concern, or an unfavorable evaluation toward
the topic or an aspect of the topic.

neutral:
The claim is descriptive, ambiguous, mixed, informational,
or does not clearly express a positive or negative stance.

Rules:

1. Judge the meaning of the claim, not individual keywords.

2. Use the topic only as context for understanding what the
   claim refers to.

3. Source comments may be used to resolve ambiguity.

4. Do not translate or rewrite the claim.

5. Do not invent sentiment or intention that is not expressed.

6. If both positive and negative attitudes are meaningfully
   present and neither clearly dominates, choose neutral.

7. If the stance is uncertain, choose neutral.

8. Return JSON only.
   Do not include Markdown or explanations.

Output format:

{
  "results": [
    {
      "claim_id": "c1",
      "stance": "positive"
    }
  ]
}
"""


VALID_STANCES = {
    "positive",
    "negative",
    "neutral"
}


def build_claim_data(claims):
    """
    Claude 입력과 캐시에 사용할
    claim 데이터를 만든다.
    """

    return [
        {
            "claim_id": claim["id"],
            "text": claim["text"],
            "sample_comments": claim.get(
                "sample_comments",
                []
            )
        }
        for claim in claims
    ]


def build_prompt(
    claims,
    topic
):
    """
    topic과 최종 claim들을 Claude에 전달한다.
    """

    data = {
        "topic": topic,
        "claims": build_claim_data(
            claims
        )
    }

    return (
        "Classify the stance of every claim.\n\n"
        + json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        )
    )


def clean_json_response(response_text):
    text = response_text.strip()

    match = re.fullmatch(
        r"```(?:json)?\s*(.*?)\s*```",
        text,
        flags=re.DOTALL | re.IGNORECASE
    )

    if match:
        text = match.group(1).strip()

    return text


def parse_response(response_text):
    cleaned = clean_json_response(
        response_text
    )

    try:
        data = json.loads(
            cleaned
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            "Claude stance 응답을 JSON으로 "
            "변환하지 못했습니다.\n"
            f"응답 내용:\n{response_text}"
        ) from error

    results = data.get(
        "results"
    )

    if not isinstance(results, list):
        raise ValueError(
            "Claude stance 응답에 "
            "results 리스트가 없습니다."
        )

    validated = []

    for result in results:
        if not isinstance(result, dict):
            continue

        claim_id = result.get(
            "claim_id"
        )
        stance = result.get(
            "stance"
        )

        if not isinstance(claim_id, str):
            continue

        if stance not in VALID_STANCES:
            continue

        validated.append({
            "claim_id": claim_id,
            "stance": stance
        })

    return validated


def classify_claim_stances(
    claims,
    topic=""
):
    """
    최종 claim들의 stance를 한 번의 batch로 판정한다.

    판정에 실패하거나 응답에서 누락된 claim은
    안전하게 neutral을 유지한다.
    """

    if not claims:
        return claims

    cache_data = {
        "model": MODEL_NAME,
        "system_prompt": SYSTEM_PROMPT,
        "topic": topic,
        "claims": build_claim_data(
            claims
        )
    }

    cached = load_cache(
        "stance_classifier",
        cache_data
    )

    if cached is not None:
        print(
            "Stance classification: 캐시 사용 "
            "(API 호출 없음)"
        )
        results = cached

    else:
        print(
            "Stance classification: Claude API 호출"
        )

        response = ask_claude(
            prompt=build_prompt(
                claims,
                topic
            ),
            system_prompt=SYSTEM_PROMPT,
            max_tokens=1024
        )

        results = parse_response(
            response
        )

        save_cache(
            "stance_classifier",
            cache_data,
            results
        )

    stance_lookup = {
        result["claim_id"]: result["stance"]
        for result in results
    }

    for claim in claims:
        claim["stance"] = stance_lookup.get(
            claim["id"],
            "neutral"
        )

    return claims