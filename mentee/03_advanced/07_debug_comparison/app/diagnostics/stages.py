"""
RAG 4종 실험군(Baseline, Rewrite Only, Rerank Only, Both) 동일 조건 비교 모듈.
한 번에 하나의 구성 요소만 변경한 실험군을 같은 Gold·k 기준으로 평가해 모듈별 기여도를 분리하는 역할.
"""


def compare_four_variants(runs: dict, gold: list[str], grades: dict) -> dict:
    """4가지 실험 변형(runs)을 동일한 Gold·등급·k=3 조건으로 일괄 평가해 반환하는 함수."""
    # 검색 순위 목록을 표준 Retrieval 지표로 환산하는 공통 평가 유틸리티 임포트
    # - evaluate_retrieval : 동일 k=3 기준 Recall·Precision·RR·DCG·nDCG 산출
    from coursekit.eval_metrics import evaluate_retrieval

    # 여러 변수를 동시에 바꾸면 성능 변화의 원인을 특정할 수 없으므로,
    # 단일 기능 변경 비교군마다 완전히 동일한 gold·grades·k=3 조건을 적용해 공정한 제어 실험 수행
    return {
        name: evaluate_retrieval(item["ranked_ids"], gold, grades, k=3)
        for name, item in runs.items()
    }


"""
설계 평가:
- 통제 변인(동일 Gold·등급·k=3)을 강제해 Rewrite와 Rerank 각각의 독립 효과 및 결합 효과를 명확히 분리하는 구조.
- 공통 평가 함수에 위임해 변형 간 채점 로직 불일치 가능성을 제거한 설계.
"""
