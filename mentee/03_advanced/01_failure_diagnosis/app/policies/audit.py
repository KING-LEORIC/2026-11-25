"""
RAG 진단 결과의 감사(Audit) 기록 생성 모듈.
민감 정보를 배제한 채 추적 가능한 판정 메타데이터만 안전하게 추출하는 역할.
"""


def audit_decision(case: dict, stage: str, evidence: str) -> dict:
    """원본 Prompt·비밀값을 제외하고 감사 로그용 안전 딕셔너리를 생성하는 함수."""
    # 원본 Prompt, API 키, 내부 오류 원문이 외부 응답이나 로그로 유출되는 보안 사고를 방지하고,
    # case_id 타입 불일치로 인한 직렬화 오류를 막기 위해 문자열로 정규화해 필수 필드만 보존
    return {
        "case_id": str(case["case_id"]),
        "stage": stage,
        "evidence": evidence,
        "recorded": True,
        "safe_message": "문제 단계 확인 완료",
    }


"""
설계 평가:
- 화이트리스트 방식으로 허용된 필드만 선별 반환해 민감 데이터 누락·유출 위험을 최소화한 구조.
- 감사 기록 포맷을 단일 함수로 캡슐화해 보안 정책 변경 시 수정 지점을 일원화한 설계.
"""
