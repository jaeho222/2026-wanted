from .preprocess import preprocess_comments
from .embed import embed_comments
from .cluster import cluster_comments
from .extract import extract_claims
from .relate import build_relations
from .hidden import find_hidden_opinions


def make_topic(claims, max_claims=3):
    """
    주요 claim을 이용해 전체 댓글의 topic을 구성한다.

    현재는 임시 방식이며,
    이후 Claude 기반 topic 생성으로 교체할 수 있다.
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


def analyze(comments, n_clusters=None):
    """
    댓글 리스트를 분석하여 최종 OpinionMap을 생성한다.
    """

    if not comments:
        return {
            "topic": "분석할 주제가 없습니다.",
            "meta": {
                "total_comments": 0,
                "analyzed_comments": 0,
                "topic_count": 0,
                "claim_count": 0
            },
            "claims": [],
            "relations": [],
            "hidden_opinions": []
        }

    # 1. 댓글 전처리
    processed_comments = preprocess_comments(
        comments
    )

    if not processed_comments:
        return {
            "topic": "분석할 주제가 없습니다.",
            "meta": {
                "total_comments": len(comments),
                "analyzed_comments": 0,
                "topic_count": 0,
                "claim_count": 0
            },
            "claims": [],
            "relations": [],
            "hidden_opinions": []
        }

    # 2. 댓글 Embedding
    embeddings = embed_comments(
        processed_comments
    )

    # 3. 의미 기반 Clustering
    clusters = cluster_comments(
        processed_comments,
        embeddings,
        n_clusters=n_clusters
    )

    # 4. Cluster에서 Claim 추출
    claims = extract_claims(
        clusters,
        embeddings,
        processed_comments
    )

    # 5. Claim Embedding
    claim_comments = [
        {
            "id": claim["id"],
            "text": claim["text"],
            "analysis_text": claim["text"],
            "likes": 0,
            "time": "1970-01-01T00:00:00Z"
        }
        for claim in claims
    ]

    claim_embeddings = embed_comments(
        claim_comments
    )

    # 6. Claim 관계 분석
    relations = build_relations(
        claims,
        claim_embeddings
    )

    # 7. 전체 Topic 생성
    topic = make_topic(
        claims
    )

    # 8. Hidden Opinion 분석
    hidden_opinions = find_hidden_opinions(
        claims,
        clusters,
        processed_comments
    )

    # 9. OpinionMap 생성
    return {
        "topic": topic,

        "meta": {
            "total_comments": len(comments),
            "analyzed_comments": len(processed_comments),
            "topic_count": len(clusters),
            "claim_count": len(claims)
        },

        "claims": claims,
        "relations": relations,
        "hidden_opinions": hidden_opinions
    }