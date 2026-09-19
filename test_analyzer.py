import json

from analyzer import analyze


test_comments = [
    {
        "id": "cmt_001",
        "text": "가격이 너무 비싸다",
        "likes": 500,
        "time": "2026-09-19T12:00:00Z"
    },
    {
        "id": "cmt_002",
        "text": "이 가격이면 작년 모델 쓰는 게 낫다",
        "likes": 320,
        "time": "2026-09-19T12:01:00Z"
    },
    {
        "id": "cmt_003",
        "text": "가격이 너무 많이 올랐다",
        "likes": 200,
        "time": "2026-09-19T12:02:00Z"
    },

    {
        "id": "cmt_004",
        "text": "디자인이 정말 예쁘다",
        "likes": 400,
        "time": "2026-09-19T12:03:00Z"
    },
    {
        "id": "cmt_005",
        "text": "외관 디자인은 마음에 든다",
        "likes": 250,
        "time": "2026-09-19T12:04:00Z"
    },
    {
        "id": "cmt_006",
        "text": "이번 디자인은 진짜 잘 뽑았다",
        "likes": 180,
        "time": "2026-09-19T12:05:00Z"
    },

    {
        "id": "cmt_007",
        "text": "발열이 너무 심하다",
        "likes": 15,
        "time": "2026-09-19T12:06:00Z"
    },
    {
        "id": "cmt_008",
        "text": "게임하면 휴대폰이 너무 뜨거워진다",
        "likes": 8,
        "time": "2026-09-19T12:07:00Z"
    },
    {
        "id": "cmt_009",
        "text": "오래 사용하면 발열 문제가 있다",
        "likes": 3,
        "time": "2026-09-19T12:08:00Z"
    }
]


result = analyze(
    test_comments,
    n_clusters=3
)

print(
    json.dumps(
        result,
        ensure_ascii=False,
        indent=2
    )
)

from analyzer.relate import get_nli_scores

relation_tests = [
    # 같은 방향의 주장
    (
        "가격이 너무 비싸다",
        "이 돈을 주고 살 가치는 없다"
    ),

    # 서로 반대되는 주장
    (
        "이번 가격 인상은 합리적이다",
        "이번 가격 인상은 합리적이지 않다"
    ),

    # 서로 다른 주제
    (
        "배우의 연기가 훌륭했다",
        "음식의 양이 너무 적다"
    ),

    # 게임 분야
    (
        "이번 캐릭터는 너무 강하다",
        "신규 캐릭터의 성능을 낮춰야 한다"
    ),

    # 영화 분야
    (
        "영화의 결말이 좋았다",
        "마지막 결말은 정말 별로였다"
    )
]

print("\n=== NLI 범용 테스트 ===")

for text_a, text_b in relation_tests:
    scores = get_nli_scores(text_a, text_b)

    print("\nA:", text_a)
    print("B:", text_b)
    print(scores)