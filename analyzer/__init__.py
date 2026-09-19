from .preprocess import preprocess_comments
from .claim_extractor import extract_claims_with_claude
from .claim_merger import merge_claims
from .claim_builder import build_final_claims
from .stance_classifier import classify_claim_stances
from .relation_builder import build_relations
from .hidden import find_hidden_opinions


def empty_result(
    total_comments=0,
    topic=""
):
    """
    분석 결과가 없는 경우의
    기본 OpinionMap 구조를 반환한다.
    """

    return {
        "topic": topic,
        "meta": {
            "total_comments": total_comments,
            "analyzed_comments": 0,
            "topic_count": 0,
            "claim_count": 0
        },
        "claims": [],
        "relations": [],
        "hidden_opinions": []
    }


def analyze(
    comments,
    topic="",
    use_api=False
):
    """
    CommentMap 전체 분석 파이프라인.

    댓글에서 개별 claim을 추출한 뒤,
    동일한 의견을 병합하고 stance와
    claim 사이의 관계를 분석한다.

    마지막으로 전체 댓글 분포와
    좋아요 상위 댓글 분포를 비교하여
    hidden opinion을 찾는다.

    topic:
        collector 또는 웹페이지에서 얻은
        게시물/영상의 제목이나 주제.

    use_api:
        True일 때만 Claude 기반 분석을 허용한다.
    """

    if not comments:
        return empty_result(
            topic=topic
        )

    processed_comments = (
        preprocess_comments(
            comments
        )
    )

    if not processed_comments:
        return empty_result(
            total_comments=len(
                comments
            ),
            topic=topic
        )

    if not use_api:
        raise RuntimeError(
            "Claude API 사용이 비활성화되어 있습니다. "
            "API 테스트가 필요한 경우에만 "
            "analyze(..., use_api=True)를 사용하세요."
        )

    # 1. 댓글에서 개별 claim 추출
    claim_results = (
        extract_claims_with_claude(
            processed_comments
        )
    )

    # 2. 같은 의미의 claim 병합
    groups = merge_claims(
        claim_results
    )

    # 3. 최종 OpinionMap claim 생성
    claims = build_final_claims(
        groups,
        processed_comments
    )

    # build_final_claims에서 유효하지 않은
    # group이 제외될 가능성에 대비해
    # 최종 claim과 대응되는 group만 유지한다.
    valid_groups = [
        group
        for group in groups
        if any(
            claim.get(
                "text",
                ""
            ).strip()
            for claim in group.get(
                "claims",
                []
            )
        )
    ]

    # 4. 주제에 대한 stance 판정
    claims = classify_claim_stances(
        claims,
        topic
    )

    # 5. claim 사이 관계 생성
    relations = build_relations(
        claims
    )

    # 6. 전체 댓글 분포와 인기댓글 분포를
    # 비교해 hidden opinion 탐색
    hidden_opinions = (
        find_hidden_opinions(
            claims,
            valid_groups,
            processed_comments
        )
    )

    return {
        "topic": topic,
        "meta": {
            "total_comments": len(
                comments
            ),
            "analyzed_comments": len(
                processed_comments
            ),
            "topic_count": len(
                valid_groups
            ),
            "claim_count": len(
                claims
            )
        },
        "claims": claims,
        "relations": relations,
        "hidden_opinions": (
            hidden_opinions
        )
    }