"""
RAG 실험 변경안의 회귀(Regression) 탐지 및 배포 보류 게이트(Gate) 모듈.
Baseline 대비 성능 하락이나 실행 오류 발생 시 자동 릴리스를 차단하는 역할.
"""


def regression_decision(
    before: float | None, after: float | None, error_count: int
) -> dict:
    """Baseline 대비 Recall 감소 또는 오류 발생 시 배포 보류 판정과 사유를 반환하는 함수."""
    # 둘 중 하나라도 No-answer(None)인 경우 비교 불능 상태를 회귀로 오인하지 않도록 유효 수치일 때만 하락 판정
    regression = before is not None and after is not None and after < before
    # 성능 회귀나 오류가 1건이라도 있으면 배포를 즉시 보류하고,
    # 자동 게이트를 통과하더라도 단독 배포 승인 대신 '추가 사람 평가 필요' 상태를 남겨 안전장치 유지
    return {
        "regression": regression,
        "error_count": error_count,
        "hold_release": regression or error_count > 0,
        "reason": "회귀/오류 발견"
        if regression or error_count > 0
        else "추가 사람 평가 필요",
    }


"""
설계 평가:
- 성능 회귀와 시스템 오류를 통합 조건으로 묶어 불완전한 변경안의 운영 반영을 차단하는 구조.
- 게이트 통과를 곧바로 배포 승인으로 간주하지 않고 사람 검증 단계를 명시해 운영 안전성을 확보한 설계.
"""
