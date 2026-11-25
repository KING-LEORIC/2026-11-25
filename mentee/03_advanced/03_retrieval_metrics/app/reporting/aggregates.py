"""
개별 질문의 Recall@k 결과를 유효 질문 기준으로 집계·요약하는 모듈.
No-answer(None) 제외 건수와 유효 평가 건수를 함께 보고해 지표 왜곡을 방지하는 역할.
"""


def summarize_valid_recall(values: list[float | None]) -> dict:
    """None을 제외한 유효 Recall 평균과 포함·제외 질문 수를 반환하는 함수."""
    # No-answer로 분리된 None 값을 평균 계산에서 제외해 실제 검색 가능 질문만의 성능을 측정하기 위한 필터링
    valid = [v for v in values if v is not None]
    # 유효 질문이 0건일 때 ZeroDivisionError가 발생하는 것을 막기 위해 mean_recall을 None으로 안전 처리하고,
    # 모수 크기 착시를 방지하기 위해 평가 포함 건수와 제외 건수를 함께 노출
    return {
        "mean_recall": sum(valid) / len(valid) if valid else None,
        "evaluated_count": len(valid),
        "excluded_no_answer": len(values) - len(valid),
    }


"""
설계 평가:
- 빈 목록 엣지 케이스를 안전하게 처리하면서 평균과 모수 메타데이터를 동시에 제공하는 구조.
- 평가 제외 건수(excluded_no_answer)를 명시해 리포트 해석 시 표본 편향 여부를 즉시 파악할 수 있는 설계.
"""
