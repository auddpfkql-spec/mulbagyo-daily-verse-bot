"""raw_parsed.json / verses.json 무결성 검사.

--stage raw   : 파서 산출물 검사 (카운트/중복id/절수 연속성)
--stage final : 저작 완료본 검사 (theme_tag 분포, 빈 필드, 글자수 규칙)
"""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOK_ORDER = ["파생기", "파현기", "청류의 말", "파문서", "파언집", "미류지언"]
EXPECTED_COUNT = {
    "파생기": 42, "파현기": 84, "청류의 말": 72,
    "파문서": 80, "파언집": 60, "미류지언": 28,
}
THEME_TAGS = {"다짐", "응시", "흘려보냄", "감사"}


def load(stage: str) -> list[dict]:
    path = ROOT / "data" / ("raw_parsed.json" if stage == "raw" else "verses.json")
    if not path.exists():
        raise SystemExit(f"파일 없음: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def check_common(verses: list[dict]) -> list[str]:
    errors = []
    if len(verses) != 366:
        errors.append(f"전체 절 수가 366이 아님: {len(verses)}")

    ids = [v["id"] for v in verses]
    dupes = [i for i, c in Counter(ids).items() if c > 1]
    if dupes:
        errors.append(f"중복 id: {dupes}")

    by_book = Counter(v["book"] for v in verses)
    for book, expected in EXPECTED_COUNT.items():
        got = by_book.get(book, 0)
        if got != expected:
            errors.append(f"{book} 절수 불일치: 예상 {expected}, 실제 {got}")

    # 장별 절 번호가 1부터 연속인지 (챕터 내 verse 번호 gap 체크)
    by_chapter: dict[tuple, list[int]] = defaultdict(list)
    for v in verses:
        by_chapter[(v["book"], v["chapter"])].append(v["verse"])
    for key, nums in by_chapter.items():
        nums.sort()
        if nums != list(range(1, len(nums) + 1)):
            errors.append(f"{key[0]} {key[1]}장 절번호 비연속: {nums}")

    return errors


def check_raw(verses: list[dict]) -> list[str]:
    errors = check_common(verses)
    for v in verses:
        if not v.get("text"):
            errors.append(f"{v['id']}: text 비어있음")
        if v["book"] != "파문서" and not v.get("era"):
            errors.append(f"{v['id']}: era 비어있음 (파문서 외 권은 자동 결정돼야 함)")
    return errors


def check_final(verses: list[dict]) -> list[str]:
    errors = check_common(verses)
    theme_counter = Counter()
    for v in verses:
        for field in ("era", "speaker", "theme_tag", "meditation", "prayer"):
            if not v.get(field):
                errors.append(f"{v['id']}: {field} 비어있음")
        tag = v.get("theme_tag")
        if tag and tag not in THEME_TAGS:
            errors.append(f"{v['id']}: 알 수 없는 theme_tag '{tag}'")
        theme_counter[tag] += 1

        med = v.get("meditation") or ""
        pray = v.get("prayer") or ""
        limit = 50 if v["book"] == "파언집" else 80
        if med and len(med) > limit + 20:  # 여유 20자
            errors.append(f"{v['id']}: meditation 길이 초과 ({len(med)}자) '{med}'")
        if pray and len(pray) > 40 + 15:
            errors.append(f"{v['id']}: prayer 길이 초과 ({len(pray)}자) '{pray}'")

    total = len(verses)
    if total:
        print("theme_tag 분포:")
        for tag in THEME_TAGS:
            n = theme_counter.get(tag, 0)
            print(f"  {tag}: {n} ({n/total:.0%})")

    return errors


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["raw", "final"], default="raw")
    args = ap.parse_args()

    verses = load(args.stage)
    errors = check_raw(verses) if args.stage == "raw" else check_final(verses)

    if errors:
        print(f"[{args.stage}] 오류 {len(errors)}건:")
        for e in errors:
            print(f"  - {e}")
        raise SystemExit(1)
    print(f"[{args.stage}] 검증 통과 ({len(verses)}절)")


if __name__ == "__main__":
    main()
