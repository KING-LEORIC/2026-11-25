"""
RAG Target 실행 결과와 Gold 레이블을 외부에서 결합·평가하는 모듈.
Target 추론 단계와 정답 채점 단계를 물리적으로 격리해 정답 유출을 방지하는 역할.
"""


def evaluate_target_run(
    example: dict, run: dict, gold: list[str], grades: dict
) -> dict:
    """Target 출력(run)과 Gold·등급을 외부 평가기에 전달해 Retrieval 점수·출처 상태를 계산하는 함수."""
    # Target 출력과 Gold를 사후 결합해 검색 지표를 계산하는 공통 평가 유틸리티 임포트
    # - evaluate_record : Top-k(k=3) 기준 Retrieval 점수 및 출처 포함 상태 산출
    from coursekit.eval_report import evaluate_record

    # Gold를 Target 입력에 넣지 않고 Evaluator 단계에서만 결합해 공정한 평가 계약 유지
    return evaluate_record(example, run, gold, grades, k=3)


"""
설계 평가:
- 추론(Target)과 채점(Evaluator)의 경계를 함수 시그니처 수준에서 분리해 데이터 누수를 막은 구조.
- 공통 평가기(evaluate_record)에 위임해 실습 간 채점 기준(k=3) 일관성을 확보한 설계.
"""
