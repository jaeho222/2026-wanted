import numpy as np

from .embed import embed_comments
from .relation_matcher import match_claim_relations


def embed_final_claims(claims):
    """
    최종 claim들을 E5 embedding으로 변환한다.
    """

    if not claims:
        return np.empty((0, 0))

    claim_comments = []

    for claim in claims:
        claim_comments.append({
            "id": claim["id"],
            "text": claim["text"],
            "analysis_text": claim["text"]
        })

    embeddings = embed_comments(
        claim_comments
    )

    return np.asarray(
        embeddings
    )


def calculate_similarity_matrix(embeddings):
    """
    normalize된 E5 embedding을 이용해
    claim 간 cosine similarity를 계산한다.
    """

    embeddings = np.asarray(
        embeddings
    )

    if len(embeddings) == 0:
        return np.empty((0, 0))

    return np.matmul(
        embeddings,
        embeddings.T
    )


def build_relation_candidates(
    claims,
    embeddings,
    top_k=3
):
    """
    E5를 이용해 관계가 있을 가능성이 높은
    claim 조합을 찾는다.

    여기서는 관계의 방향을 판단하지 않는다.
    E5는 후보를 줄이는 역할만 한다.
    """

    if len(claims) < 2:
        return []

    similarity_matrix = (
        calculate_similarity_matrix(
            embeddings
        )
    )

    candidate_pairs = []
    seen_pairs = set()

    for index_a in range(
        len(claims)
    ):
        similarities = similarity_matrix[
            index_a
        ]

        ranked_indices = np.argsort(
            similarities
        )[::-1]

        selected_count = 0

        for index_b in ranked_indices:

            if index_a == index_b:
                continue

            index_b = int(
                index_b
            )

            pair_key = tuple(
                sorted(
                    (
                        index_a,
                        index_b
                    )
                )
            )

            if pair_key not in seen_pairs:
                seen_pairs.add(
                    pair_key
                )

                candidate_pairs.append({
                    "index_a": pair_key[0],
                    "index_b": pair_key[1]
                })

            selected_count += 1

            if selected_count >= top_k:
                break

    return candidate_pairs


def build_directional_pairs(
    candidate_pairs,
    claims
):
    """
    하나의 관계 후보에 대해
    A -> B와 B -> A를 모두 만든다.

    support / attack은 방향성이 있기 때문에
    두 방향을 각각 판정한다.
    """

    directional_pairs = []

    for pair in candidate_pairs:
        index_a = pair[
            "index_a"
        ]

        index_b = pair[
            "index_b"
        ]

        directional_pairs.append({
            "from_index": index_a,
            "to_index": index_b,
            "claim_a": claims[
                index_a
            ]["text"],
            "claim_b": claims[
                index_b
            ]["text"]
        })

        directional_pairs.append({
            "from_index": index_b,
            "to_index": index_a,
            "claim_a": claims[
                index_b
            ]["text"],
            "claim_b": claims[
                index_a
            ]["text"]
        })

    return directional_pairs


def classify_relation_candidates(
    directional_pairs
):
    """
    방향이 포함된 claim pair를
    Claude에게 전달해 관계를 판정한다.
    """

    if not directional_pairs:
        return []

    matcher_input = []

    for pair in directional_pairs:
        matcher_input.append({
            "claim_a": pair["claim_a"],
            "claim_b": pair["claim_b"]
        })

    decisions = match_claim_relations(
        matcher_input
    )

    classified = []

    for decision in decisions:

        pair_id = decision[
            "pair_id"
        ]

        if not (
            0 <= pair_id < len(
                directional_pairs
            )
        ):
            continue

        pair = directional_pairs[
            pair_id
        ]

        classified.append({
            "from_index": pair[
                "from_index"
            ],
            "to_index": pair[
                "to_index"
            ],
            "relation": decision[
                "relation"
            ]
        })

    return classified


def build_relations(
    claims,
    top_k=3
):
    """
    최종 claim 사이의 방향성 관계를 만든다.

    과정:
    1. E5로 관계 후보 탐색
    2. 각 후보를 양방향 pair로 변환
    3. Claude가 각 방향의 관계 판정
    4. none 제거
    5. OpinionMap relation 형태로 변환
    """

    if len(claims) < 2:
        return []

    embeddings = embed_final_claims(
        claims
    )

    candidate_pairs = (
        build_relation_candidates(
            claims,
            embeddings,
            top_k=top_k
        )
    )

    directional_pairs = (
        build_directional_pairs(
            candidate_pairs,
            claims
        )
    )

    classified = (
        classify_relation_candidates(
            directional_pairs
        )
    )

    relations = []

    seen_relations = set()

    for result in classified:

        relation = result[
            "relation"
        ]

        if relation == "none":
            continue

        from_claim = claims[
            result["from_index"]
        ]

        to_claim = claims[
            result["to_index"]
        ]

        relation_key = (
            from_claim["id"],
            to_claim["id"],
            relation
        )

        if relation_key in seen_relations:
            continue

        seen_relations.add(
            relation_key
        )

        relations.append({
            "from": from_claim["id"],
            "to": to_claim["id"],
            "type": relation
        })

    return relations