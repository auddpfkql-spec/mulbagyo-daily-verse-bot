"""물바교_정전.md 를 읽어 366절 raw JSON으로 변환한다.

이 스크립트가 자동으로 채우는 필드: id/book/chapter/verse/text, length_type, form.
자동으로 못 채우는 필드(era 일부/speaker/theme_tag/meditation/prayer)는 null이나
힌트만 남기고, 저작 단계에서 사람이 직접 채운다 (계획 문서 참고).

재실행 가능: 원본 정전.md 오탈자를 고치면 이 스크립트만 다시 돌리면 된다.
단, data/verses.json(저작 완료본)은 건드리지 않는다 — 출력은 항상 raw_parsed.json으로만.
"""
import json
import re
from pathlib import Path

CANON_PATH = Path(r"C:\Users\auddu\Desktop\물바교_정전.md")
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "raw_parsed.json"
NOTES_PATH = Path(__file__).resolve().parent.parent / "docs" / "parsing_notes.md"

BOOK_RE = re.compile(r"^#\s+제(\d+)권\s+(.+)$")
CHAP_RE = re.compile(r"^##\s+제(\d+)[장부]\s+(.+)$")
SUB_RE = re.compile(r"^\*(.+)\*$")
VERSE_RE = re.compile(r"^\*\*(\d+)\*\*\s*(.*)$")
QUOTE_RE = re.compile(r"^>\s?(.*)$")

# 권 -> (form, era). 파문서는 절 내용에 따라 era가 바뀌므로 None(저작 단계에서 채움).
BOOK_META = {
    "파생기": ("서사", "잠류"),
    "파현기": ("서사", "결"),
    "청류의 말": ("문답", "결"),
    "파문서": ("교리", None),
    "파언집": ("잠언", "산류"),
    "미류지언": ("예언", "미류"),
}

DOCTRINE_SUB_RE = re.compile(r"(교리|훈계)\s*(?:·\s*(기존|신규)\s*([^·]*))?")
SPEAKER_HINT_RES = [
    ("청류", re.compile(r"청류(?:가|는)\s*(?:말했다|되물었다|웃으며)")),
    ("물바", re.compile(r"^물바는 말하지 않는다")),
]
WITNESS_HINT_RE = re.compile(r"^내가 그 곁에 있었다")


def parse_lines(lines: list[str]) -> list[dict]:
    verses: list[dict] = []
    book = book_no = chapter = chap_no = None
    verse_no_in_chapter = 0
    doctrine_origin = None
    notes = {"verse_form": [], "doctrine_tags": [], "speaker_hints": []}

    i = 0
    n = len(lines)
    while i < n:
        line = lines[i].rstrip("\n")

        m = BOOK_RE.match(line)
        if m:
            book_no, book = int(m.group(1)), m.group(2).strip()
            chap_no = None
            i += 1
            continue

        m = CHAP_RE.match(line)
        if m:
            chap_no, chapter = int(m.group(1)), m.group(2).strip()
            verse_no_in_chapter = 0
            doctrine_origin = None
            i += 1
            # 부제 줄은 헤더 바로 다음 줄에 블랭크 없이 온다 (있을 때만)
            if i < n:
                sm = SUB_RE.match(lines[i].rstrip("\n"))
                if sm:
                    sub = sm.group(1)
                    dm = DOCTRINE_SUB_RE.search(sub)
                    if dm:
                        doctrine_origin = sub
                        notes["doctrine_tags"].append(
                            {"book": book, "chapter": chap_no, "tag": sub}
                        )
                    i += 1
            continue

        m = VERSE_RE.match(line)
        if m:
            verse_no_in_chapter += 1
            verse_no = verse_no_in_chapter
            first = m.group(2).strip()
            i += 1
            frags: list[str] = []
            is_verse_form = False
            if first:
                frags.append(first)
            while i < n and lines[i].strip() != "":
                raw = lines[i].rstrip("\n")
                qm = QUOTE_RE.match(raw)
                if qm:
                    is_verse_form = True
                    frags.append(qm.group(1))
                else:
                    frags.append(raw.strip())
                i += 1
            text = "\n".join(frags) if is_verse_form else " ".join(frags)

            form, era = BOOK_META[book]
            length_type = (
                "단문형" if book == "파언집" else "운문형" if is_verse_form else "표준형"
            )

            speaker_hint = None
            for name, rx in SPEAKER_HINT_RES:
                if rx.search(text):
                    speaker_hint = name
                    break
            if speaker_hint is None and WITNESS_HINT_RE.match(text):
                speaker_hint = "목격자서술(없음)"

            verse = {
                "id": f"{book} {chap_no}:{verse_no}",
                "book": book,
                "chapter": chap_no,
                "verse": verse_no,
                "text": text,
                "length_type": length_type,
                "form": form,
                "era": era,
                "speaker": "없음",
                "theme_tag": None,
                "meditation": None,
                "prayer": None,
                "_doctrine_origin": doctrine_origin,
                "_speaker_hint": speaker_hint,
            }
            verses.append(verse)

            if is_verse_form:
                notes["verse_form"].append(verse["id"])
            if speaker_hint:
                notes["speaker_hints"].append({"id": verse["id"], "hint": speaker_hint})
            continue

        i += 1

    return verses, notes


def write_notes(notes: dict, total: int) -> None:
    lines = [
        "# 파서 예외/힌트 목록 (저작 단계 체크리스트)\n",
        f"\n전체 파싱된 절 수: {total}\n",
        "\n## 운문형(블록쿼트) 절\n",
    ]
    for vid in notes["verse_form"]:
        lines.append(f"- {vid}\n")
    lines.append("\n## 파문서 부제 태그 (교리/훈계, 기존/신규)\n")
    for t in notes["doctrine_tags"]:
        lines.append(f"- {t['book']} {t['chapter']}장: {t['tag']}\n")
    lines.append("\n## speaker 힌트 (최종 확정은 저작 단계에서)\n")
    for h in notes["speaker_hints"]:
        lines.append(f"- {h['id']}: {h['hint']}\n")
    NOTES_PATH.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    text = CANON_PATH.read_text(encoding="utf-8")
    lines = text.split("\n")
    verses, notes = parse_lines(lines)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        json.dumps(verses, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_notes(notes, len(verses))

    print(f"파싱 완료: {len(verses)}절 -> {OUT_PATH}")
    by_book: dict[str, int] = {}
    for v in verses:
        by_book[v["book"]] = by_book.get(v["book"], 0) + 1
    for b, c in by_book.items():
        print(f"  {b}: {c}절")
    print(f"예외 노트 -> {NOTES_PATH}")


if __name__ == "__main__":
    main()
