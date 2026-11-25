"""
RAG 평가 단건 레코드 채점 및 전체 결과 요약 위임 모듈.
Target Trace 무결성을 검증하며 개별 평가와 No-answer 제외 집계를 수행하는 역할.
"""


def evaluate_one(example: dict, run: dict, gold: list[str], grades: dict) -> dict:
    """질문 입력(example)과 Target 출력(run)을 Gold·등급과 결합해 단건 평가 레코드를 반환하는 함수."""
    # 단건 Target Trace 검증 및 k=3 검색 지표 산출을 위한 공통 평가기 임포트
    # - evaluate_record : 필수 필드 누락 차단 및 출처 무결성·No-answer 상태 판정
    from coursekit.eval_report import evaluate_record

    # Trace 필드가 빠졌을 때 빈 리스트로 임의 보정해 오류를 은폐하는 것을 막고,
    # evaluate_record의 엄격한 계약 검증과 k=3 기준을 그대로 적용
    return evaluate_record(example, run, gold, grades, k=3)


def summarize_all(rows: list[dict]) -> dict:
    """개별 평가 결과 목록을 집계해 유효 평균과 오류·출처 상태 요약을 반환하는 함수."""
    # 단일 모드·버전·변형 조건 하에서 평균과 실패 건수를 집계하는 유틸리티 임포트
    # - report_summary : No-answer 제외 평균 산출 및 출처·상태 실패 횟수 합산
    from coursekit.eval_report import report_summary

    # No-answer 질문을 Retrieval 평균에서 분리하고 모드/버전 혼합을 차단하기 위해 공통 요약기에 위임
    return report_summary(rows)


"""
설계 평가:
- 단건 채점(evaluate_one)과 다건 집계(summarize_all)를 공통 리포트 엔진에 위임해 계약 일관성을 유지한 구조.
- 누락 데이터 임의 보정 금지와 No-answer 분리 집계를 통해 평가 지표 신뢰도를 확보한 설계.
"""
