"""
RAG 검색 결과의 Recall@k 및 고유 적중 수(Hit Count) 산출 모듈.
Top-k 내 중복 ID로 인한 점수 부풀림과 No-answer 질문의 0점 왜곡을 방지하는 역할.
"""


def calculate_recall(ranked: list[str], gold: list[str], k: int) -> float | None:
    """Top-k 검색 결과에서 Gold 청크를 찾아낸 비율(Recall@k)을 반환하는 함수."""
    # bool이 int의 하위 클래스인 점을 고려해 type(k) is not int로 True/False 유입을 엄격히 차단하고,
    # k < 1 입력으로 인한 음수 슬라이싱·비정상 계산을 막기 위한 입력 계약 검증
    if type(k) is not int or k < 1:
        raise ValueError("k는 1 이상의 정수")
    # 정답이 없는 No-answer 질문을 0점으로 처리해 전체 평균 Recall이 왜곡되는 것을 방지하기 위해 None 반환
    if not gold:
        return None
    # ranked[:k]와 gold 양쪽의 중복 ID가 Recall을 1.0 초과로 왜곡하는 문제를 막기 위해 집합 교집합 비율 계산
    return len(set(ranked[:k]) & set(gold)) / len(set(gold))


def count_gold_hits(ranked: list[str], gold: list[str], k: int) -> int:
    """Top-k 결과와 Gold 목록 간 중복 없는 고유 적중 개수를 반환하는 함수."""
    # 동일 청크 ID가 상위 k개에 중복 노출되더라도 적중 횟수는 1회만 집계하기 위해 집합 교집합 크기 반환
    return len(set(ranked[:k]) & set(gold))


"""
설계 평가:
- bool 타입까지 걸러내는 엄격한 k 검증과 집합 연산으로 지표 산출의 수학적 일관성을 확보한 구조.
- No-answer 케이스를 None으로 분리해 평가 집계 단계의 평균 왜곡을 원천 차단한 설계.
"""
