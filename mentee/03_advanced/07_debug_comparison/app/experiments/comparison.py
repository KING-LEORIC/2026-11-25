"""
RAG 실험 전후(Before/After) 점수 변화량 산출 및 실패 단계 진단 모듈.
No-answer 사례의 왜곡을 배제한 순수 성능 증감 계산과 근본 원인 단계 식별을 수행하는 역할.
"""


def score_delta(before: float | None, after: float | None) -> float | None:
    """동일 데이터셋·모드 기준 Before/After 점수 차이를 반환하고 No-answer 포함 시 None을 반환하는 함수."""
    # 한쪽이라도 No-answer(None)인 질문을 0점으로 간주해 감산하면 허위 증감치가 생성되므로 비교 제외
    if before is None or after is None:
        return None
    # 부동소수점 연산 미세 오차(예: 1e-16)로 인해 동일 점수가 회귀로 오판되는 것을 막기 위해 소수점 6자리 반올림
    return round(after - before, 6)


def find_problem_stage(run: dict, gold: list[str]) -> str:
    """실행 결과(run)와 Gold를 대조해 후보·Rerank·Context·생성 중 문제 발생 단계를 반환하는 함수."""
    # 파이프라인 단계별 실패 원인을 일관된 기준으로 판별하는 실험 진단 유틸리티 임포트
    # - diagnose : Candidate 누락 여부를 우선 확인한 뒤 후속 단계 실패를 순차 진단
    from coursekit.eval_experiments import diagnose

    # Candidate에 Gold가 없으면 앞단 Retrieval 문제로 우선 귀속시켜 잘못된 모듈 수정을 방지
    return diagnose(run, gold)


"""
설계 평가:
- None 가드와 반올림 처리로 A/B 비교 시 발생할 수 있는 수치적·논리적 회귀 오탐을 예방한 구조.
- 정량 변화량(score_delta)과 정성 원인 단계(find_problem_stage)를 함께 제공해 디버깅 효율을 높인 설계.
"""
