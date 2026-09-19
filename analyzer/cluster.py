import numpy as np

from sklearn.cluster import AgglomerativeClustering


def cluster_comments(comments, embeddings, n_clusters=3):
    """
    댓글 임베딩의 cosine 유사도를 기준으로
    의미가 비슷한 댓글끼리 클러스터링한다.
    """

    if not comments:
        return []

    if len(comments) != len(embeddings):
        raise ValueError(
            "댓글 개수와 임베딩 개수가 일치하지 않습니다."
        )

    n_clusters = min(n_clusters, len(comments))

    embeddings = np.asarray(embeddings)

    clustering = AgglomerativeClustering(
        n_clusters=n_clusters,
        metric="cosine",
        linkage="average"
    )

    labels = clustering.fit_predict(embeddings)

    clusters = [
        []
        for _ in range(n_clusters)
    ]

    for comment, label in zip(comments, labels):
        clusters[label].append(comment)

    return clusters