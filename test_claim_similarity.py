import json

import numpy as np

from analyzer.preprocess import preprocess_comments
from analyzer.claim_extractor import extract_claims_with_claude
from analyzer.claim_merger import (
    flatten_claims,
    embed_claims,
    find_similar_claims
)


def select_comments(comments, sample_count=20):
    """
    데이터 전체 구간에서 댓글을 골고루 선택한다.
    """

    if len(comments) <= sample_count:
        return comments

    indices = np.linspace(
        0,
        len(comments) - 1,
        sample_count,
        dtype=int
    )

    indices = np.unique(indices)

    return [
        comments[index]
        for index in indices
    ]


def main():

    file_path = "data/comments_ai_jobs.json"

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:
        comments = json.load(file)

    processed_comments = preprocess_comments(
        comments
    )

    test_comments = select_comments(
        processed_comments,
        sample_count=20
    )

    print(
        f"전체 댓글 수: {len(processed_comments)}"
    )

    print(
        f"테스트 댓글 수: {len(test_comments)}"
    )

    print(
        "\nClaude claim 추출 중..."
    )

    claim_results = extract_claims_with_claude(
        test_comments
    )

    claims = flatten_claims(
        claim_results
    )

    print(
        f"추출된 claim 수: {len(claims)}"
    )

    if len(claims) < 2:
        print(
            "비교할 claim이 충분하지 않습니다."
        )
        return

    embeddings = embed_claims(
        claims
    )

    similarity_results = find_similar_claims(
        claims,
        embeddings,
        top_k=3
    )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "[CLAIM 유사도 결과]"
    )

    for index, result in enumerate(
        similarity_results,
        start=1
    ):
        claim = result["claim"]

        print(
            "\n"
            + "=" * 70
        )

        print(
            f"[Claim #{index}]"
        )

        print(
            claim["text"]
        )

        print(
            "\n[가장 가까운 Claim]"
        )

        for rank, candidate in enumerate(
            result["candidates"],
            start=1
        ):
            print(
                f"\n{rank}. "
                f"(유사도 {candidate['similarity']:.4f})"
            )

            print(
                candidate["text"]
            )


if __name__ == "__main__":
    main()