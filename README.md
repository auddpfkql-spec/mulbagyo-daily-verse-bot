# 물바교 "오늘의 말씀" 디스코드 봇

`물바교_정전.md`(366절)를 매일 하나씩 Discord 채널에 임베드로 올리는 스크립트.
상시 봇 프로세스가 아니라, **하루 한 번 실행되고 끝나는 스크립트**다 (Cowork 예약 실행 전제).

## 구조
- `data/raw_parsed.json` — 파서 산출물 (구조적 필드만 채워짐)
- `data/verses.json` — 최종본 (묵상·기도·theme_tag까지 전부 채워진 366절)
- `scripts/parse_canon.py` — 정전.md → raw_parsed.json
- `scripts/validate.py` — 데이터 무결성 검사 (`--stage raw|final`)
- `scripts/cycle.py` — 시작일 기준 오늘 인덱스 계산
- `scripts/send_discord.py` — Discord Webhook으로 오늘의 임베드 전송
- `config/settings.json` — `start_date`(순환 시작일), 로컬 테스트용 `webhook_url_local`
- `docs/authoring_guide.md` — theme_tag 분류·묵상/기도 생성 규칙
- `docs/pado-mun_reference.md` — 기도 톤 레퍼런스 원문

## 로컬 테스트
```bash
python scripts/parse_canon.py                 # 366절 파싱
python scripts/validate.py --stage raw         # 무결성 확인
python scripts/cycle.py --self-test            # 순환 로직 확인
python scripts/send_discord.py --dry-run --date 2026-09-01   # 임베드 콘솔 출력만
```
저작 전(`verses.json` 없음) 단계에서도 `--data data/samples/sample_10.json --index 0` 처럼
지정하면 샘플 데이터로 dry-run 확인 가능.

## 실전 전송
```bash
DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..." python scripts/send_discord.py
```

## Cowork 예약 실행 설정
1. 이 폴더를 업로드
2. 매일 원하는 시각에 `python scripts/send_discord.py` 실행되도록 예약
3. 환경변수 `DISCORD_WEBHOOK_URL` 에 실제 채널 webhook URL 등록
   (Discord 채널 설정 → 연동 → 웹훅 → 새 웹훅 → URL 복사)
4. 순환 시작일을 바꾸고 싶으면 `config/settings.json`의 `start_date` 한 줄만 수정
