import json
import numpy as np

from analyzer.preprocess import preprocess_comments
from analyzer.embed import embed_comments


def cosine_similarity_matrix(embeddings):
    """
    normalize된 embedding들의 cosine similarity를 계산한다.
    """

    embeddings = np.asarray(embeddings)

    return np.matmul(
        embeddings,
        embeddings.T
    )


def show_similar_comments(
    comments,
    embeddings,
    sample_count=10,
    top_k=3
):
    """
    일부 댓글을 골라 각 댓글과 의미적으로
    가장 비슷한 댓글 TOP K를 출력한다.
    """

    similarity_matrix = cosine_similarity_matrix(
        embeddings
    )

    # 데이터 전체 구간에서 골고루 샘플을 선택
    sample_count = min(
        sample_count,
        len(comments)
    )

    sample_indices = np.linspace(
        0,
        len(comments) - 1,
        sample_count,
        dtype=int
    )

    for index in sample_indices:

        similarities = similarity_matrix[index]

        # 자기 자신은 제외
        ranked_indices = np.argsort(
            similarities
        )[::-1]

        ranked_indices = [
            i
            for i in ranked_indices
            if i != index
        ][:top_k]

        print("\n" + "=" * 70)

        print(
            f"[기준 댓글 #{index + 1}]"
        )
        print(
            comments[index]["text"]
        )

        print("\n[가장 비슷한 댓글]")

        for rank, similar_index in enumerate(
            ranked_indices,
            start=1
        ):
            score = similarities[
                similar_index
            ]

            print(
                f"\n{rank}. "
                f"(유사도 {score:.3f})"
            )

            print(
                comments[similar_index]["text"]
            )


def main():

    # 실제 수집 댓글 불러오기
    with open(
        "comments.json",
        "r",
        encoding="utf-8"
    ) as file:
        comments = json.load(file)

    # 전처리
    processed_comments = preprocess_comments(
        comments
    )

    print(
        f"분석 댓글 수: "
        f"{len(processed_comments)}"
    )

    # Embedding
    embeddings = embed_comments(
        processed_comments
    )

    # 비슷한 댓글 확인
    show_similar_comments(
        processed_comments,
        embeddings,
        sample_count=10,
        top_k=3
    )


if __name__ == "__main__":
    main()