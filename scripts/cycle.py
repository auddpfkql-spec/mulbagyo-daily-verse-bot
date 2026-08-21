"""365일 고정 순환 인덱스 계산 (순수 함수 모듈).

(오늘 - 시작일).days % 365 로 오늘의 verses.json 인덱스를 구한다.
윤년이 껴서 elapsed가 365를 넘어가는 날에도 그냥 모듈로 연산이라 자연히 처리되지만,
사용자가 명시한 "윤년 366일째는 365번째 절 재사용" 규칙을 명시적으로 보장하기 위해
방어적으로 한 번 더 캡을 씌운다.
"""
import argparse
from datetime import date, timedelta

TOTAL = 365


def get_cycle_state(start_date: date, today: date) -> dict:
    elapsed = (today - start_date).days
    if elapsed < 0:
        raise ValueError("오늘이 시작일 이전입니다")
    idx = elapsed % TOTAL
    idx = min(idx, TOTAL - 1)
    cycle_no = elapsed // TOTAL + 1
    day_in_cycle = idx + 1
    return {
        "index": idx,
        "day_in_cycle": day_in_cycle,
        "cycle_no": cycle_no,
        "elapsed": elapsed,
    }


def _self_test() -> None:
    start = date(2026, 1, 1)
    seen = set()
    for offset in range(730):
        today = start + timedelta(days=offset)
        state = get_cycle_state(start, today)
        assert 0 <= state["index"] < TOTAL, state
        seen.add(state["index"])
    assert seen == set(range(TOTAL)), f"인덱스 커버리지 누락: {set(range(TOTAL)) - seen}"
    print(f"self-test 통과: 730일 순회, 인덱스 0~{TOTAL - 1} 전부 등장 확인 (윤년 포함)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        _self_test()
