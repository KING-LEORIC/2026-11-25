"""
RAG 평가 요약 데이터를 사람이 읽을 수 있는 Markdown 보고서로 변환하는 모듈.
평균 점수 외에 실행 모드·출처 오류·No-answer 제외 건수·해석 주의사항을 함께 기록하는 역할.
"""


def write_summary_report(summary: dict, rows: list[dict]) -> str:
    """집계 요약(summary)과 개별 결과를 바탕으로 Markdown 형식의 평가 보고서 문자열을 생성하는 함수."""
    # 평균 점수가 높더라도 출처 무결성 실패나 실행 오류가 1건이라도 있으면 '점검 필요'로 경고하고,
    # 오류가 없더라도 자동 통과 확정 대신 '사람 검토 후 추가 판단'을 남겨 성급한 승인 방지
    review = (
        "점검 필요"
        if summary["source_integrity_failures"] or summary["status_failures"]
        else "사람 검토 후 추가 판단"
    )
    # 개별 오류와 근거 검토를 누락한 채 평균 점수만 제출하는 왜곡을 막기 위해
    # 모드·변형·No-answer 제외 건수·출처 실패 수 및 Fixture 한계 주의문을 명시해 반환
    return (
        "# Day28 RAG Evaluation Report\n\n"
        f"- Run mode: {summary['mode']}\n"
        f"- Variant: {summary['variant']}\n"
        f"- Mean Recall@3: {summary['mean_recall_at_k']}\n"
        f"- MRR@3: {summary['mrr_at_k']}\n"
        f"- No-answer excluded: {summary['no_answer_excluded']}\n"
        f"- Source failures: {summary['source_integrity_failures']}\n"
        f"- Quality decision: {review}\n"
        "- 주의: 교육용 Fixture 점수는 모델 품질 실측값이 아닙니다.\n"
    )


"""
설계 평가:
- 정량 평균과 정성 안전 지표(출처 실패, 판단 보류, Fixture 주의문)를 한 문서에 결합한 구조.
- 오류 유무에 따른 조건부 의사결정 문구로 보고서 오독 가능성을 줄인 설계.
"""
