import math


def find_hidden_opinions(claims, clusters, comments):
    """
    전체 댓글에서는 일정 비율 존재하지만
    인기 댓글에서는 상대적으로 덜 노출되는 의견을 찾는다.

    특정 주제나 키워드에 의존하지 않고
    댓글의 분포와 좋아요 수만 이용한다.
    """

    if not comments or not claims or not clusters:
        return []

    # 좋아요가 많은 댓글부터 정렬
    sorted_comments = sorted(
        comments,
        key=lambda comment: comment.get("likes", 0),
        reverse=True
    )

    # 전체 댓글 중 상위 30%를 인기 댓글로 사용
    # 데이터가 적어도 최소 3개는 확보
    top_count = max(
        3,
        math.ceil(len(comments) * 0.3)
    )

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

        # 전체 댓글에서 이 의견이 차지하는 비율
        share = len(cluster) / len(comments)

        # 인기 댓글 중 이 의견에 해당하는 댓글 수
        top_cluster_count = sum(
            1
            for comment in cluster
            if comment["id"] in top_ids
        )

        # 인기 댓글에서의 의견 비율
        top_share = (
            top_cluster_count
            / len(top_comments)
        )

        # 전체에서는 어느 정도 존재하지만
        # 인기 댓글에서는 상대적으로 덜 보이는 경우
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