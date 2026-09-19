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
    여러 독립 댓글에서 반복되었지만
    가장 많이 등장한 핵심 의견은 아닌 claim을
    hidden opinion 후보로 찾는다.

    단 한 번만 등장한 의견은
    우연한 개인 발언일 수 있으므로
    hidden opinion으로 분류하지 않는다.

    특정 주제, 키워드 또는 고정 비율 임계값에
    의존하지 않는다.
    """

    if not claims or total_comments <= 0:
        return []

    valid_claims = [
        claim
        for claim in claims
        if claim.get("count", 0) > 0
    ]

    if not valid_claims:
        return []

    top_count = max(
        claim.get("count", 0)
        for claim in valid_claims
    )

    # 모든 의견이 한 번씩만 등장했다면
    # 반복적으로 관측된 의견이 없으므로
    # hidden opinion을 만들지 않는다.
    if top_count <= 1:
        return []

    hidden_opinions = []

    for claim in valid_claims:
        count = claim.get(
            "count",
            0
        )

        # 한 댓글에서만 등장한 의견은
        # hidden opinion으로 확정하지 않는다.
        if count < 2:
            continue

        # 가장 많이 등장한 핵심 의견은
        # hidden opinion으로 보지 않는다.
        if count >= top_count:
            continue

        share = (
            count / total_comments
        )

        top_share = (
            count / top_count
        )

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

    # 5. 반복적으로 관측된 비주류 의견 탐색
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