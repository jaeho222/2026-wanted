from sentence_transformers import SentenceTransformer


MODEL_NAME = "intfloat/multilingual-e5-small"

model = SentenceTransformer(MODEL_NAME)


def embed_comments(comments):
    """
    댓글을 의미 벡터(embedding)로 변환한다.

    preprocess를 거친 댓글은 analysis_text를 사용하고,
    없는 경우 기존 text를 사용한다.
    """

    if not comments:
        return []

    texts = []

    for comment in comments:
        text = comment.get(
            "analysis_text",
            comment.get("text", "")
        )

        # E5 모델은 passage prefix를 붙여 사용하는 것이 권장된다.
        texts.append(
            f"passage: {text}"
        )

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    return embeddings