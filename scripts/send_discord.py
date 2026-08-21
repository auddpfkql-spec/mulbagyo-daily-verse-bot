"""오늘의 절을 계산해 Discord Webhook으로 임베드 1회 전송.

Cowork 예약 실행이 하루 한 번 이 스크립트를 돌리는 것을 전제로 한다 — 상시 봇
로그인 없음, requests로 webhook에 POST 한 번 보내고 끝.

사용 예:
  python scripts/send_discord.py --dry-run
  python scripts/send_discord.py --dry-run --date 2026-09-01
  python scripts/send_discord.py --dry-run --data data/samples/sample_10.json --index 0
  DISCORD_WEBHOOK_URL=... python scripts/send_discord.py
"""
import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cycle import get_cycle_state, TOTAL  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TEAL = 0x14B8A6  # 청록색 (Tailwind teal-500)


def build_embed(verse: dict, state: dict, today: date) -> dict:
    return {
        "title": f"🌊 오늘의 물바교 말씀 · {today.strftime('%Y.%m.%d')}",
        "description": f"{verse['text']}\n— {verse['id']}",
        "color": TEAL,
        "fields": [
            {"name": "묵상", "value": verse["meditation"], "inline": False},
            {"name": "기도", "value": verse["prayer"], "inline": False},
        ],
        "footer": {"text": f"{state['day_in_cycle']}일째 · 전체 {TOTAL}일 순환"},
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="테스트용 오늘 날짜 오버라이드 YYYY-MM-DD")
    ap.add_argument("--index", type=int, help="특정 절 강제 지정 (0-based, 테스트용)")
    ap.add_argument("--data", default=None, help="verses.json 대신 쓸 파일 경로 (샘플 테스트용)")
    ap.add_argument("--dry-run", action="store_true", help="전송하지 않고 콘솔에만 출력")
    args = ap.parse_args()

    data_path = Path(args.data) if args.data else ROOT / "data" / "verses.json"
    if not data_path.exists():
        sys.exit(f"데이터 파일 없음: {data_path} (아직 저작 전이면 --data 로 샘플 파일을 지정하세요)")
    verses = json.loads(data_path.read_text(encoding="utf-8"))

    settings_path = ROOT / "config" / "settings.json"
    cfg = json.loads(settings_path.read_text(encoding="utf-8"))

    today = date.fromisoformat(args.date) if args.date else date.today()
    start_date = date.fromisoformat(cfg["start_date"])
    state = get_cycle_state(start_date, today)
    idx = args.index if args.index is not None else state["index"]

    if idx >= len(verses):
        sys.exit(f"인덱스 {idx} 가 데이터 길이({len(verses)})를 벗어남")

    embed = build_embed(verses[idx], state, today)
    payload = {"embeds": [embed]}

    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL") or cfg.get("webhook_url_local")
    if not webhook_url:
        sys.exit("DISCORD_WEBHOOK_URL 이 설정되지 않았습니다 (환경변수 또는 config/settings.json의 webhook_url_local)")

    import requests

    resp = requests.post(webhook_url, json=payload, timeout=10)
    resp.raise_for_status()
    print(f"전송 완료: {verses[idx]['id']} ({resp.status_code})")


if __name__ == "__main__":
    main()
