from .preprocess import preprocess_comments
from .claim_extractor import extract_claims_with_claude
from .claim_merger import merge_claims
from .claim_builder import build_final_claims
from .relation_builder import build_relations


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


def build_hidden_opinions(
    claims,
    total_comments
):
    """
    전체 댓글에서 차지하는 비율은 낮지만
    독립적인 claim으로 살아남은 의견을 찾는다.

    특정 키워드나 주제에 의존하지 않고
    claim의 실제 등장 비율을 이용한다.
    """

    if not claims or total_comments <= 0:
        return []

    counts = [
        claim.get("count", 0)
        for claim in claims
        if claim.get("count", 0) > 0
    ]

    if not counts:
        return []

    top_count = max(counts)

    hidden_opinions = []

    for claim in claims:
        count = claim.get(
            "count",
            0
        )

        if count <= 0:
            continue

        share = (
            count / total_comments
        )

        top_share = (
            count / top_count
        )

        # 가장 많이 등장한 핵심 의견은
        # hidden opinion으로 보지 않는다.
        if count >= top_count:
            continue

        # 전체 댓글의 10% 이하이면서
        # 최다 의견보다 충분히 작은 경우만
        # 소수 의견 후보로 사용한다.
        if (
            share <= 0.10
            and top_share <= 0.50
        ):
            hidden_opinions.append({
                "text": claim["text"],
                "share": round(
                    share,
                    4
                ),
                "top_share": round(
                    top_share,
                    4
                )
            })

    return hidden_opinions


def analyze(
    comments,
    topic="",
    use_api=False
):
    """
    CommentMap 전체 분석 파이프라인.

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

    processed_comments = preprocess_comments(
        comments
    )

    if not processed_comments:
        return empty_result(
            total_comments=len(comments),
            topic=topic
        )

    if not use_api:
        raise RuntimeError(
            "Claude API 사용이 비활성화되어 있습니다. "
            "API 테스트가 필요한 경우에만 "
            "analyze(..., use_api=True)를 사용하세요."
        )

    # 1. 댓글에서 개별 주장 추출
    claim_results = extract_claims_with_claude(
        processed_comments
    )

    # 2. 같은 의미의 주장 병합
    groups = merge_claims(
        claim_results
    )

    # 3. 최종 claim 생성
    claims = build_final_claims(
        groups,
        processed_comments
    )

    # 4. claim 사이의 관계 생성
    relations = build_relations(
        claims
    )

    # 5. 소수 의견 탐색
    hidden_opinions = build_hidden_opinions(
        claims,
        len(processed_comments)
    )

    return {
        "topic": topic,
        "meta": {
            "total_comments": len(comments),
            "analyzed_comments": len(
                processed_comments
            ),
            "topic_count": len(groups),
            "claim_count": len(claims)
        },
        "claims": claims,
        "relations": relations,
        "hidden_opinions": hidden_opinions
    }