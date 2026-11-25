"""
RAG 평가 결과의 사람 검수(Human Review) 메타데이터 생성 모듈.
자동 판정 기반의 성급한 배포를 차단하고 추가 사람 검토 필요 상태를 명시하는 역할.
"""


def prepare_human_review(case_id: str, score: float | None, reviewer: str) -> dict:
    """사람 검수 레이블 여부와 이견 검토·배포 불가 상태를 포함한 기록 딕셔너리를 반환하는 함수."""
    # LLM Judge 자동 판정만으로 규정·의료·금융 등 고위험 답변을 확정·배포하는 사고를 방지하기 위해
    # judge='human_fixture' 및 publishable=False를 고정하고 이견 검토 상태를 명시적으로 기록
    return {
        "case_id": case_id,
        "faithfulness": score,
        "judge": "human_fixture",
        "reviewer": reviewer,
        "disagreement": "추가 사람 검토 필요",
        "publishable": False,
    }


"""
설계 평가:
- publishable=False 기본값과 검수자·이견 필드를 강제해 Human-in-the-loop 안전장치를 구현한 구조.
- 자동 평가 점수와 별개로 사람 검수 출처를 명시해 결과 신뢰 범위 오용을 방지한 설계.
"""
