import math
from .embed import embed_comments
from .cluster import cluster_comments
from .extract import extract_claims
from .relate import build_relations


def make_topic(claims, max_claims=3):
    """
    특정 도메인 키워드에 의존하지 않고
    주요 claim을 이용해 전체 댓글의 topic을 구성한다.
    """

    if not claims:
        return "분석할 주제가 없습니다."

    ranked_claims = sorted(
        claims,
        key=lambda claim: claim["count"],
        reverse=True
    )

    selected = ranked_claims[:max_claims]

    topic_texts = [
        claim["text"]
        for claim in selected
    ]

    if len(topic_texts) == 1:
        return topic_texts[0]

    return " / ".join(topic_texts)


def find_hidden_opinions(claims, clusters, comments):
    """
    전체 댓글에서는 일정 비율 존재하지만
    인기 댓글에서는 상대적으로 덜 노출되는 의견을 찾는다.
    """

    if not comments:
        return []

    # 좋아요가 많은 순서대로 정렬
    sorted_comments = sorted(
        comments,
        key=lambda comment: comment["likes"],
        reverse=True
    )

    # 인기 댓글 = 상위 30%
    # 작은 데이터에서도 너무 적게 뽑히지 않도록 최소 3개 사용
    top_count = max(
        3,
        math.ceil(len(comments) * 0.3)
    )

    # 전체 댓글 수보다 많아지지 않도록 제한
    top_count = min(
        top_count,
        len(comments)
    )

    top_comments = sorted_comments[:top_count]

    top_ids = {
        comment["id"]
        for comment in top_comments
    }

    hidden_opinions = []

    for claim, cluster in zip(claims, clusters):

        # 전체 댓글에서 해당 의견이 차지하는 비율
        share = len(cluster) / len(comments)

        # 인기 댓글 중 해당 의견에 속하는 댓글 개수
        top_cluster_count = sum(
            1
            for comment in cluster
            if comment["id"] in top_ids
        )

        # 인기 댓글에서 해당 의견이 차지하는 비율
        top_share = (
            top_cluster_count
            / len(top_comments)
        )

        # 전체 비중에 비해 인기 댓글 노출 비중이
        # 절반 이하인 경우 hidden opinion으로 판단
        if (
            share >= 0.1
            and top_share <= share * 0.5
        ):
            hidden_opinions.append({
                "text": claim["text"],
                "share": round(share, 4),
                "top_share": round(top_share, 4)
            })

    return hidden_opinions


def analyze(comments, n_clusters=3):
    """
    댓글 리스트를 분석하여 최종 OpinionMap을 생성한다.
    """

    if not comments:
        return {
            "topic": "분석할 주제가 없습니다.",
            "meta": {
                "total_comments": 0,
                "topic_count": 0,
                "claim_count": 0
            },
            "claims": [],
            "relations": [],
            "hidden_opinions": []
        }

    # 1. 댓글 Embedding
    embeddings = embed_comments(comments)

    # 2. 비슷한 댓글끼리 Clustering
    clusters = cluster_comments(
        comments,
        embeddings,
        n_clusters=n_clusters
    )

    # 3. 각 Cluster에서 Claim 추출
    claims = extract_claims(
        clusters,
        embeddings,
        comments
    )

    # 4. Claim 자체를 다시 Embedding
    claim_comments = [
        {
            "id": claim["id"],
            "text": claim["text"],
            "likes": 0,
            "time": "1970-01-01T00:00:00Z"
        }
        for claim in claims
    ]

    claim_embeddings = embed_comments(claim_comments)

    # 5. Claim 사이 관계 생성
    relations = build_relations(
        claims,
        claim_embeddings
    )

    # 6. 핵심 Topic 생성
    topic = make_topic(claims)

    # 7. Hidden Opinion 계산
    hidden_opinions = find_hidden_opinions(
        claims,
        clusters,
        comments
    )

    # 8. 최종 OpinionMap
    opinion_map = {
        "topic": topic,

        "meta": {
            "total_comments": len(comments),
            "topic_count": len(clusters),
            "claim_count": len(claims)
        },

        "claims": claims,
        "relations": relations,
        "hidden_opinions": hidden_opinions
    }

    return opinion_map
