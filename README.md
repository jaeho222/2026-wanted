# 2026-wanted
원티드 챔피언쉽

Collector

YouTube URL을 입력하면 댓글을 수집·전처리하여
contracts/comments.schema.json 형식의 comments.json을 생성합니다.

설치

프로젝트 루트에서 가상환경을 활성화한 뒤 필요한 패키지를 설치합니다.

pip install -r requirements.txt

프로젝트 루트에 .env 파일을 만들고 YouTube Data API v3 키를 설정합니다.

YOUTUBE_API_KEY=YOUR_API_KEY

.env는 GitHub에 커밋하지 않습니다.

테스트

pytest -q

댓글 수집

처음에는 댓글 100개만 테스트하는 것을 권장합니다.

python run_collector.py "YOUTUBE_URL" --max-comments 100

전체 수집:

python run_collector.py "YOUTUBE_URL"

정상 실행되면 프로젝트 루트에 comments.json이 생성되고,
contracts/comments.schema.json 검증까지 통과합니다.

Python에서 직접 사용

from collector import collect

comments = collect("YOUTUBE_URL")

출력 형식

[
  {
    "id": "Ugx...",
    "text": "댓글 내용",
    "likes": 12,
    "time": "2026-09-19T03:20:00Z"
  }
]

각 필드는 다음 의미입니다.

필드

설명

id

YouTube 댓글 고유 ID

text

전처리된 댓글 본문

likes

댓글 좋아요 수

time

댓글 작성 시각(ISO 8601)

전처리

Collector에서는 다음 항목을 제거합니다.

중복 댓글

스팸성 댓글

이모지만 있는 댓글

너무 짧은 댓글

링크만 있거나 링크가 과도하게 포함된 댓글

파일 구성

collector/youtube.py — YouTube URL 파싱 및 댓글 수집

collector/clean.py — 댓글 전처리

collector/__init__.py — collect(url) 제공

run_collector.py — comments.json 생성

test_collector.py — Collector 테스트

토픽 분류, 클러스터링, 주장/반론 분석은 analyzer/에서 처리합니다.

