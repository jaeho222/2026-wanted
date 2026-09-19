import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification


MODEL_NAME = "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
model.eval()


def get_nli_scores(text_a, text_b):
    """
    두 claim의 NLI 관계 점수를 계산한다.

    반환:
    {
        "entailment": ...,
        "neutral": ...,
        "contradiction": ...
    }
    """

    inputs = tokenizer(
        text_a,
        text_b,
        return_tensors="pt",
        truncation=True,
        max_length=256
    )

    with torch.no_grad():
        outputs = model(**inputs)

    probabilities = torch.softmax(
        outputs.logits,
        dim=-1
    )[0]

    scores = {}

    for index, probability in enumerate(probabilities):
        label = model.config.id2label[index].lower()
        scores[label] = float(probability)

    return scores


def classify_relation(claim_a, claim_b):
    """
    NLI 결과를 CommentMap relation으로 변환한다.

    entailment     -> support
    contradiction  -> attack
    neutral        -> related 또는 관계 없음
    """

    scores_ab = get_nli_scores(
        claim_a["text"],
        claim_b["text"]
    )

    scores_ba = get_nli_scores(
        claim_b["text"],
        claim_a["text"]
    )

    entailment = max(
        scores_ab.get("entailment", 0.0),
        scores_ba.get("entailment", 0.0)
    )

    contradiction = max(
        scores_ab.get("contradiction", 0.0),
        scores_ba.get("contradiction", 0.0)
    )

    # 강한 모순 관계
    if contradiction >= 0.70:
        return "attack"

    # 강한 함의 관계
    if entailment >= 0.70:
        return "support"

    # 어느 정도 의미 관계가 있는 경우
    if (
        entailment >= 0.40
        or contradiction >= 0.40
    ):
        return "related"

    return None


def build_relations(claims, claim_embeddings=None):
    """
    모든 claim 쌍을 비교하여 relation을 생성한다.

    claim_embeddings는 기존 analyzer와의 호환성을 위해
    인자로 받지만 현재 NLI 방식에서는 사용하지 않는다.
    """

    relations = []

    for i in range(len(claims)):
        for j in range(i + 1, len(claims)):

            relation_type = classify_relation(
                claims[i],
                claims[j]
            )

            if relation_type is None:
                continue

            relations.append({
                "from": claims[i]["id"],
                "to": claims[j]["id"],
                "type": relation_type
            })

    return relations