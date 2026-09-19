import argparse
import json
from pathlib import Path

from jsonschema import Draft7Validator, FormatChecker

from collector import collect


def load_schema(schema_path: Path) -> dict:
    with schema_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def validate_comments(comments: list[dict], schema_path: Path) -> None:
    schema = load_schema(schema_path)

    validator = Draft7Validator(
        schema,
        format_checker=FormatChecker(),
    )

    errors = sorted(
        validator.iter_errors(comments),
        key=lambda error: list(error.path),
    )

    if errors:
        messages = []
        for error in errors:
            location = " -> ".join(map(str, error.path)) or "(root)"
            messages.append(f"{location}: {error.message}")

        raise ValueError(
            "comments.schema.json 검증 실패:\n- "
            + "\n- ".join(messages)
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="YouTube 댓글을 수집·정제해 comments.json으로 저장합니다."
    )

    parser.add_argument("url", help="분석할 YouTube URL")
    parser.add_argument(
        "--max-comments",
        type=int,
        default=None,
        help="테스트용 최대 수집 개수. 생략하면 가능한 만큼 수집합니다.",
    )
    parser.add_argument(
        "--output",
        default="comments.json",
        help="출력 파일 경로 (기본값: comments.json)",
    )
    parser.add_argument(
        "--schema",
        default="contracts/comments.schema.json",
        help="JSON Schema 경로",
    )

    args = parser.parse_args()

    comments = collect(
        args.url,
        max_comments=args.max_comments,
    )

    schema_path = Path(args.schema)
    validate_comments(comments, schema_path)

    output_path = Path(args.output)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(
            comments,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(f"완료: 정제된 댓글 {len(comments)}개")
    print(f"스키마 검증: PASS")
    print(f"저장 위치: {output_path.resolve()}")


if __name__ == "__main__":
    main()
