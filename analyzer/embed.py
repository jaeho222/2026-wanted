from sentence_transformers import SentenceTransformer


# 한국어를 포함한 다국어 문장을 벡터로 변환하는 모델
MODEL_NAME = "intfloat/multilingual-e5-small"

# 모델은 한 번만 불러온다.
model = SentenceTransformer(MODEL_NAME)


def embed_comments(comments):
    """
    댓글 리스트를 받아 각 댓글의 text를 Embedding 벡터로 변환한다.

    입력:
        comments.schema.json 형식의 댓글 리스트

    출력:
        댓글 순서와 동일한 순서의 Embedding 벡터 리스트
    """

    # 댓글이 없으면 빈 리스트 반환
    if not comments:
        return []

    # 댓글에서 text만 추출
    texts = [comment["text"] for comment in comments]

    # 로컬 모델로 Embedding 생성
    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    return embeddings