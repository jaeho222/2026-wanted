import json
import sys

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
    데이터 전체에서 댓글을 골고루 선택하고,
    각 댓글과 의미적으로 가장 비슷한 댓글을 출력한다.
    """

    similarity_matrix = cosine_similarity_matrix(
        embeddings
    )

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

    sample_indices = np.unique(
        sample_indices
    )

    for index in sample_indices:

        similarities = similarity_matrix[index]

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

    if len(sys.argv) < 2:
        print(
            "사용법: "
            "python test_similarity.py <댓글 JSON 파일>"
        )
        return

    file_path = sys.argv[1]

    try:
        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:
            comments = json.load(file)

    except FileNotFoundError:
        print(
            f"파일을 찾을 수 없습니다: "
            f"{file_path}"
        )
        return

    except json.JSONDecodeError:
        print(
            f"올바른 JSON 파일이 아닙니다: "
            f"{file_path}"
        )
        return

    if not isinstance(comments, list):
        print(
            "댓글 JSON의 최상위 구조는 "
            "리스트여야 합니다."
        )
        return

    processed_comments = preprocess_comments(
        comments
    )

    print(
        f"데이터 파일: {file_path}"
    )

    print(
        f"원본 댓글 수: {len(comments)}"
    )

    print(
        f"분석 댓글 수: "
        f"{len(processed_comments)}"
    )

    if not processed_comments:
        print(
            "분석 가능한 댓글이 없습니다."
        )
        return

    embeddings = embed_comments(
        processed_comments
    )

    show_similar_comments(
        processed_comments,
        embeddings,
        sample_count=10,
        top_k=3
    )


if __name__ == "__main__":
    main()