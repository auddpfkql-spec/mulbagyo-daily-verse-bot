"""저작 배치 병합 도구.

raw_parsed.json의 구조적 필드(id/book/chapter/verse/text/length_type/form)에
배치별 overrides 파일(id -> theme_tag/meditation/prayer, 필요시 era/speaker)을
덧씌워 data/verses.json에 누적한다. 이미 있는 id는 덮어쓰고, 최종적으로 정전 읽기
순서(파생기->파현기->청류의 말->파문서->파언집->미류지언, 장/절 순)로 정렬해 저장한다.

사용: python scripts/author_merge.py <overrides.json>
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_PATH = ROOT / "data" / "raw_parsed.json"
OUT_PATH = ROOT / "data" / "verses.json"

BOOK_ORDER = ["파생기", "파현기", "청류의 말", "파문서", "파언집", "미류지언"]
BOOK_RANK = {b: i for i, b in enumerate(BOOK_ORDER)}


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("사용법: python scripts/author_merge.py <overrides.json>")
    overrides_path = Path(sys.argv[1])
    overrides = json.loads(overrides_path.read_text(encoding="utf-8"))
    by_id_override = {o["id"]: o for o in overrides}

    raw = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    raw_by_id = {v["id"]: v for v in raw}

    existing: dict[str, dict] = {}
    if OUT_PATH.exists():
        for v in json.loads(OUT_PATH.read_text(encoding="utf-8")):
            existing[v["id"]] = v

    applied = 0
    for vid, ov in by_id_override.items():
        base = raw_by_id.get(vid)
        if base is None:
            print(f"경고: raw_parsed에 없는 id 무시됨: {vid}")
            continue
        merged = {
            "id": base["id"],
            "book": base["book"],
            "chapter": base["chapter"],
            "verse": base["verse"],
            "text": base["text"],
            "length_type": base["length_type"],
            "form": base["form"],
            "era": ov.get("era", base["era"]),
            "speaker": ov.get("speaker", base.get("speaker", "없음")),
            "theme_tag": ov["theme_tag"],
            "meditation": ov["meditation"],
            "prayer": ov["prayer"],
        }
        existing[vid] = merged
        applied += 1

    merged_list = sorted(
        existing.values(),
        key=lambda v: (BOOK_RANK[v["book"]], v["chapter"], v["verse"]),
    )
    OUT_PATH.write_text(
        json.dumps(merged_list, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"{applied}건 병합, 누적 {len(merged_list)}절 -> {OUT_PATH}")


if __name__ == "__main__":
    main()
