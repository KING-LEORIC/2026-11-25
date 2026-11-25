"""
RAG 평가용 Gold 레이블 감사(Audit) 기록 생성 모듈.
질문별 정답 청크 ID와 데이터셋 버전·고정 상태를 불변 메타데이터로 보존하는 역할.
"""


def audit_gold(question_id: str, ids: list[str], version: str) -> dict:
    """질문 ID·Gold ID·버전·고정 여부를 포함한 감사 딕셔너리를 생성하는 함수."""
    # 외부 리스트 참조로 인한 사후 변조를 막기 위해 list(ids)로 방어적 복사 수행,
    # 평가 결과에 따라 정답 레이블을 임의로 수정하는 데이터 오염을 방지하기 위해 frozen=True 고정,
    # 실제 기관 전문가 판정이 아닌 교육용 예시임을 명시해 실무 지표와의 혼선 방지
    return {
        "question_id": question_id,
        "gold_chunk_ids": list(ids),
        "gold_version": version,
        "frozen": True,
        "review_status": "교육용 사전 검토 레이블",
    }


"""
설계 평가:
- 방어적 복사와 고정(frozen) 플래그를 결합해 평가 기준 데이터의 불변성과 추적성을 확보한 구조.
- 레이블 출처(review_status)를 감사 기록에 포함해 데이터셋 신뢰 범위 오인을 방지한 설계.
"""
