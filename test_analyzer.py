import json

from analyzer import analyze


# A가 수집한 실제 댓글 불러오기
with open(
    "comments.json",
    "r",
    encoding="utf-8"
) as file:
    comments = json.load(file)


print(f"불러온 댓글 수: {len(comments)}")

result = analyze(comments)

print(
    json.dumps(
        result,
        ensure_ascii=False,
        indent=2
    )
)