import numpy as np

from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score


def _make_clustering(n_clusters):
    """
    Agglomerative Clustering 모델을 생성한다.

    cosine distance를 기준으로 댓글 임베딩을 묶는다.
    """

    return AgglomerativeClustering(
        n_clusters=n_clusters,
        metric="cosine",
        linkage="average"
    )


def _find_best_cluster_count(embeddings):
    """
    여러 클러스터 개수를 시험한 뒤
    silhouette score가 가장 높은 개수를 선택한다.

    특정 영상이나 주제에 맞춘 고정 클러스터 수를 사용하지 않고,
    현재 댓글의 임베딩 분포를 기준으로 자동 결정한다.
    """

    num_comments = len(embeddings)

    # 댓글이 매우 적은 경우
    if num_comments <= 2:
        return 1

    # 지나치게 많은 후보를 검사하지 않도록 제한한다.
    #
    # 데이터가 많아질수록 탐색 가능한 최대 cluster 수도
    # 완만하게 증가하도록 한다.
    max_clusters = min(
        15,
        max(2, int(np.sqrt(num_comments)) + 2),
        num_comments - 1
    )

    best_n_clusters = 2
    best_score = -1.0

    for n_clusters in range(2, max_clusters + 1):

        clustering = _make_clustering(n_clusters)

        labels = clustering.fit_predict(embeddings)

        # 모든 데이터가 하나의 cluster로 묶이는 등의
        # 비정상적인 경우를 방지한다.
        unique_labels = np.unique(labels)

        if len(unique_labels) < 2:
            continue

        try:
            score = silhouette_score(
                embeddings,
                labels,
                metric="cosine"
            )
        except ValueError:
            continue

        if score > best_score:
            best_score = score
            best_n_clusters = n_clusters

    return best_n_clusters


def cluster_comments(
    comments,
    embeddings,
    n_clusters=None
):
    """
    댓글 임베딩을 기반으로 의미적으로 비슷한 댓글을 묶는다.

    n_clusters가 지정되면 해당 값을 사용하고,
    지정되지 않으면 데이터에 맞춰 자동으로 결정한다.
    """

    if not comments:
        return []

    if len(comments) != len(embeddings):
        raise ValueError(
            "댓글 개수와 임베딩 개수가 일치하지 않습니다."
        )

    embeddings = np.asarray(embeddings)

    # 댓글이 하나뿐이면 하나의 cluster 반환
    if len(comments) == 1:
        return [comments]

    # 외부에서 cluster 수를 지정하지 않은 경우
    # 자동으로 적절한 cluster 수 탐색
    if n_clusters is None:
        n_clusters = _find_best_cluster_count(
            embeddings
        )

    # 안전 범위 보정
    n_clusters = max(
        1,
        min(n_clusters, len(comments))
    )

    # cluster가 하나인 경우
    if n_clusters == 1:
        return [comments]

    clustering = _make_clustering(
        n_clusters
    )

    labels = clustering.fit_predict(
        embeddings
    )

    clusters = [
        []
        for _ in range(n_clusters)
    ]

    for comment, label in zip(
        comments,
        labels
    ):
        clusters[label].append(comment)

    # 혹시 비어 있는 cluster가 있다면 제거
    clusters = [
        cluster
        for cluster in clusters
        if cluster
    ]

    return clusters