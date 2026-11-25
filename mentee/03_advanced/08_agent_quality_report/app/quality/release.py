"""
Agent Tool 연결 전 1차 품질·보안 Gate 판정 모듈.
정량 검색 임계치(Recall·MRR)와 출처·상태·사람 검수·접근 제어 통과 여부를 종합 검사하는 역할.
"""


def agent_release_gate(summary: dict, human_ok: bool, access_ok: bool) -> dict:
    """요약 지표와 사람 검토·접근제어 여부를 결합해 1차 Agent 준비 Gate 결과를 반환하는 함수."""
    # 정량 임계치 및 보안·검수 플래그를 종합 평가하는 공통 Gate 유틸리티 임포트
    # - release_gate : Recall/MRR 임계치 및 출처·실행 상태·사람·접근제어 통과 여부 판정
    from coursekit.eval_report import release_gate

    # 원본 summary 딕셔너리 변조를 막기 위해 언패킹 복사 후 bool 정규화된 검수·접근제어 플래그 주입,
    # 이 1차 Gate 통과만으로 실서비스 보안·운영 배포 승인이 완료된 것으로 오인하지 않도록 기준 임계치 적용
    return release_gate(
        {
            **summary,
            "human_review_passed": bool(human_ok),
            "access_control_passed": bool(access_ok),
        },
        min_recall=0.70,
        min_mrr=0.60,
    )


"""
설계 평가:
- 원본 요약 객체 불변성을 지키면서 외부 검수(human_ok, access_ok) 상태를 안전하게 결합한 구조.
- 정량 지표와 비정량 안전성 게이트를 통합해 Agent Tool 연결 전 최소 방어선을 구축한 설계.
"""
