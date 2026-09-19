import json

from analyzer import analyze


DATA_PATH = "data/comments_ai_jobs.json"
SAMPLE_SIZE = 10


def load_comments():
    """
    실제 수집 데이터에서 소량의 댓글만 가져온다.
    """

    with open(
        DATA_PATH,
        "r",
        encoding="utf-8"
    ) as file:
        comments = json.load(file)

    return comments[:SAMPLE_SIZE]


def print_result(result):
    """
    최종 OpinionMap 결과를 보기 좋게 출력한다.
    """

    print("\n========== TOPIC ==========")
    print(
        result.get("topic", "")
        or "(현재 테스트에서는 topic 없음)"
    )

    print("\n========== META ==========")
    print(
        json.dumps(
            result.get("meta", {}),
            ensure_ascii=False,
            indent=2
        )
    )

    print("\n========== CLAIMS ==========")

    for claim in result.get(
        "claims",
        []
    ):
        print(
            f'\n[{claim["id"]}] '
            f'{claim["text"]}'
        )
        print(
            f'  count: {claim["count"]}'
        )
        print(
            f'  stance: {claim["stance"]}'
        )

        for sample in claim.get(
            "sample_comments",
            []
        ):
            print(
                f"  - {sample}"
            )

    print("\n========== RELATIONS ==========")

    relations = result.get(
        "relations",
        []
    )

    if not relations:
        print("(관계 없음)")

    for relation in relations:
        print(
            f'{relation["from"]} '
            f'--{relation["type"]}--> '
            f'{relation["to"]}'
        )

    print("\n========== HIDDEN OPINIONS ==========")

    hidden_opinions = result.get(
        "hidden_opinions",
        []
    )

    if not hidden_opinions:
        print("(숨은 의견 없음)")

    for opinion in hidden_opinions:
        print(
            f'- {opinion["text"]} '
            f'(share={opinion["share"]}, '
            f'top_share={opinion["top_share"]})'
        )


def main():
    comments = load_comments()

    print(
        f"Loaded {len(comments)} comments "
        f"from {DATA_PATH}"
    )

    result = analyze(
        comments,
        topic="AI and the future of jobs",
        use_api=True
    )

    print_result(
        result
    )


if __name__ == "__main__":
    main()