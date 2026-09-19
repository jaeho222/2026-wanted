from analyzer.claude_client import ask_claude


def main():
    response = ask_claude(
        prompt="다음 단어를 그대로 한 단어로 답해줘: 연결성공",
        max_tokens=20
    )

    print("Claude 응답:")
    print(response)


if __name__ == "__main__":
    main()