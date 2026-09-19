import json
import re

from .cache import load_cache, save_cache
from .claude_client import ask_claude, MODEL_NAME


SYSTEM_PROMPT = """
You are a claim relation classification system for CommentMap.

CommentMap visualizes the structure of opinions and arguments
expressed across comments.

Your task is to determine the relationship between two distinct claims.

Possible relations:

- "support":
  Claim A provides a reason, evidence, explanation, or argument
  that supports Claim B.

- "attack":
  Claim A contradicts, challenges, rejects, or provides a reason
  against Claim B.

- "related":
  Claim A and Claim B concern meaningfully related issues, but
  neither clearly supports nor attacks the other.

- "none":
  There is no meaningful argumentative relationship between them.

Rules:
1. Do not classify two claims as "support" merely because they express
   similar opinions.
2. Do not classify two claims as "attack" merely because their
   sentiment is different.
3. Topic similarity alone is not enough for "support" or "attack".
4. Use "related" only when there is a meaningful semantic connection.
5. Use "none" when the connection is weak or incidental.
6. Judge the direction from Claim A to Claim B.
7. Do not judge whether either claim is factually true.
8. Do not invent missing context.
9. Preserve uncertainty expressed in the claims.
10. Return JSON only. Do not include Markdown or explanations.

Output format:

{
  "results": [
    {
      "pair_id": 0,
      "relation": "support"
    }
  ]
}
"""


def build_prompt(claim_pairs):
    """
    관계를 판정할 claim pair를
    Claude에 전달할 형태로 만든다.
    """

    pair_data = []

    for pair in claim_pairs:
        pair_data.append({
            "pair_id": pair["pair_id"],
            "claim_a": pair["claim_a"],
            "claim_b": pair["claim_b"]
        })

    return (
        "Classify the relationship from Claim A to Claim B "
        "for each pair.\n\n"
        + json.dumps(
            pair_data,
            ensure_ascii=False,
            indent=2
        )
    )


def clean_json_response(response_text):
    """
    JSON 응답이 Markdown 코드 블록으로
    감싸져 있으면 제거한다.
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
    Claude 응답을 JSON으로 변환하고
    relation 값을 검증한다.
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
            "Claude relation 응답을 "
            "JSON으로 변환하지 못했습니다.\n"
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

    valid_relations = {
        "support",
        "attack",
        "related",
        "none"
    }

    for result in results:

        if not isinstance(result, dict):
            continue

        pair_id = result.get(
            "pair_id"
        )

        relation = result.get(
            "relation"
        )

        if not isinstance(pair_id, int):
            continue

        if relation not in valid_relations:
            continue

        validated_results.append({
            "pair_id": pair_id,
            "relation": relation
        })

    return validated_results


def make_cache_data(claim_pairs):
    """
    모델, 프롬프트, claim pair를 포함해
    relation 결과의 캐시 키를 만든다.
    """

    pair_data = []

    for pair in claim_pairs:
        pair_data.append({
            "pair_id": pair["pair_id"],
            "claim_a": pair["claim_a"],
            "claim_b": pair["claim_b"]
        })

    return {
        "model": MODEL_NAME,
        "system_prompt": SYSTEM_PROMPT,
        "pairs": pair_data
    }


def match_claim_relations(
    claim_pairs,
    batch_size=20
):
    """
    claim pair의 관계를 판정한다.

    동일한 batch의 캐시가 존재하면
    API를 호출하지 않는다.
    """

    if not claim_pairs:
        return []

    indexed_pairs = []

    for pair_id, pair in enumerate(
        claim_pairs
    ):
        indexed_pairs.append({
            "pair_id": pair_id,
            "claim_a": pair["claim_a"],
            "claim_b": pair["claim_b"]
        })

    all_results = []

    for start in range(
        0,
        len(indexed_pairs),
        batch_size
    ):
        batch = indexed_pairs[
            start:start + batch_size
        ]

        cache_data = make_cache_data(
            batch
        )

        cached_result = load_cache(
            "relation_matcher",
            cache_data
        )

        if cached_result is not None:
            print(
                "Relation matching: 캐시 사용 "
                "(API 호출 없음)"
            )

            all_results.extend(
                cached_result
            )

            continue

        print(
            "Relation matching: Claude API 호출"
        )

        prompt = build_prompt(
            batch
        )

        response = ask_claude(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            max_tokens=2048
        )

        batch_results = parse_response(
            response
        )

        save_cache(
            "relation_matcher",
            cache_data,
            batch_results
        )

        all_results.extend(
            batch_results
        )

    return all_results