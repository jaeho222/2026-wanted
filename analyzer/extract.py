import numpy as np

def classify_stance(text):
    """
    대표 논점의 기본적인 긍정/부정/중립 입장을 판별한다.
    추후 더 정교한 모델로 교체할 수 있다.
    """

    positive_words = [
        "좋다", "좋아", "예쁘다", "마음에 든다",
        "괜찮다", "만족", "추천", "훌륭하다",
        "납득", "찬성"
    ]

    negative_words = [
        "싫다", "비싸다", "심하다", "별로",
        "아쉽다", "문제", "불만", "최악",
        "반대", "부족하다", "뜨겁다"
    ]

    positive_score = sum(
        1 for word in positive_words
        if word in text
    )

    negative_score = sum(
        1 for word in negative_words
        if word in text
    )

    if positive_score > negative_score:
        return "positive"

    if negative_score > positive_score:
        return "negative"

    return "neutral"

def extract_claims(clusters, embeddings, comments):
    """
    각 클러스터에서 대표 논점(claim)을 추출한다.

    입력:
        clusters: cluster_comments()가 만든 댓글 그룹
        embeddings: 전체 댓글의 임베딩 벡터
        comments: 전체 댓글 리스트

    출력:
        OpinionMap의 claims 형식에 가까운 리스트
    """

    claims = []

    # 댓글 id → embedding 위치
    id_to_index = {
        comment["id"]: index
        for index, comment in enumerate(comments)
    }

    for cluster_index, cluster in enumerate(clusters):

        if not cluster:
            continue

        # 현재 클러스터 댓글들의 embedding 가져오기
        cluster_embeddings = np.array([
            embeddings[id_to_index[comment["id"]]]
            for comment in cluster
        ])

        # 클러스터 중심 계산
        centroid = np.mean(cluster_embeddings, axis=0)

        # 중심과 각 댓글 사이의 거리 계산
        distances = np.linalg.norm(
            cluster_embeddings - centroid,
            axis=1
        )

        # 중심과 가장 가까운 댓글 선택
        representative_index = np.argmin(distances)
        representative_comment = cluster[representative_index]

        claim = {
            "id": f"c{cluster_index + 1}",
            "text": representative_comment["text"],
            "count": len(cluster),
            "stance": classify_stance(representative_comment["text"]),
            "sample_comments": [
                comment["text"]
                for comment in cluster[:3]
            ]
        }

        claims.append(claim)

    return claims