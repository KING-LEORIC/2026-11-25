"""
RAG 검색 결과의 Precision@k 및 Hit@k(성공 여부) 동시 산출 모듈.
No-answer 질문을 분리하고 교안의 고정 분모(k) 계약을 준수해 지표를 계산하는 역할.
"""


def precision_and_hit(ranked: list[str], gold: list[str], k: int) -> dict:
    """Precision@k(적중 수/k)와 Hit@k(0 또는 1)를 딕셔너리로 반환하는 함수."""
    # 정답이 없는 No-answer 질문을 일반 질문 지표에 섞어 평균을 깎는 문제를 막기 위해 None으로 분리 반환
    if not gold:
        return {"precision_at_k": None, "hit_at_k": None}
    # Top-k 내 중복 ID로 Precision@k가 과대 산정되는 것을 방지하기 위해 집합 교집합으로 고유 적중 수 산출
    hits = len(set(ranked[:k]) & set(gold))
    # 검색 결과가 k개보다 적더라도 교안 정의에 따라 분모를 k로 고정하고,
    # Hit 여부를 불리언 대신 0/1 정수로 변환해 후속 수치 집계·JSON 직렬화 일관성 확보
    return {"precision_at_k": hits / k, "hit_at_k": int(hits > 0)}


"""
설계 평가:
- 단일 순회·교집합 계산으로 Precision@k와 Hit@k를 함께 산출해 중복 연산을 줄인 구조.
- No-answer에 대한 명시적 None 반환과 고정 분모(k) 적용으로 평가 기준의 모호성을 제거한 설계.
"""
