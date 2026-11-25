"""
RAG 검색 결과의 첫 정답 등장 순위 탐색 및 RR(Reciprocal Rank) 산출 모듈.
MRR(Mean Reciprocal Rank) 계산의 기초가 되는 첫 적중 순위와 역수 점수를 구하는 역할.
"""


def first_relevant_rank(ranked: list[str], gold: list[str], k: int) -> int | None:
    """Top-k에서 첫 Gold 문서가 나타나는 1-based 순위를 반환하고 미발견 시 None을 반환하는 함수."""
    # 0-based 인덱스로 인한 1/0 나눗셈 오류를 막기 위해 1부터 순위를 매기고,
    # 첫 정답을 찾은 즉시 조기 반환해 불필요한 후속 순회 생략
    for pos, cid in enumerate(ranked[:k], 1):
        if cid in gold:
            return pos
    # Top-k 내 정답 부재를 0이나 음수 대신 None으로 명확히 구분 반환
    return None


def calculate_rr(position: int | None) -> float:
    """첫 관련 문서 순위의 역수(1/rank)를 계산하고 미발견(None) 시 0.0을 반환하는 함수."""
    # None 입력 시 ZeroDivisionError·TypeError를 방지하고 미적중 케이스를 0.0점으로 안전 처리
    return 1.0 / position if position is not None else 0.0


"""
설계 평가:
- 순위 탐색(first_relevant_rank)과 역수 변환(calculate_rr)을 분리해 단위 검증과 재사용성을 높인 구조.
- 1-based 순위 계약과 None 가드를 통해 MRR 집계 단계의 예외 발생 가능성을 차단한 설계.
"""
