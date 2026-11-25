"""
RAG 검색 순위의 등급 기반 DCG@k(Discounted Cumulative Gain) 산출 모듈.
문서별 관련도 등급과 순위 감쇠를 반영하되 미판정 문서의 임의 0점 처리를 차단하는 역할.
"""


def calculate_dcg(ranked: list[str], grades: dict[str, int], k: int) -> float:
    """Top-k 검색 결과의 등급과 순위 위치를 반영한 DCG@k 점수를 계산하는 함수."""
    # DCG 순위 감쇠(discount) 분모 계산을 위한 표준 수학 함수 임포트
    # - log2 : 순위(position + 1)에 로그 감쇠를 적용해 상위 순위 가중치 부여
    from math import log2

    # 판정되지 않은 문서를 임의로 0등급 처리하면 실제 관련 문서가 0점으로 왜곡되므로 예외로 차단
    if any(cid not in grades for cid in ranked[:k]):
        raise ValueError("미판정 후보의 등급을 먼저 확인하세요")
    # 고등급 문서의 가치를 지수적으로 키우고(2**grade - 1), 하위 순위 기여도를 로그로 감쇠해 합산 반환
    return sum(
        (2 ** grades[cid] - 1) / log2(position + 1)
        for position, cid in enumerate(ranked[:k], 1)
    )


"""
설계 평가:
- 미판정 후보에 대한 엄격한 사전 검증으로 불완전한 레이블에 의한 지표 왜곡을 방지한 구조.
- 1-based 순위 기반 로그 감쇠 공식을 한 줄 제너레이터 합산으로 간결하게 구현한 설계.
"""
