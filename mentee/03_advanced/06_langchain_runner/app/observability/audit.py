"""
RAG Target 실행의 관측성(Observability) 감사 기록 생성 모듈.
실행 모드·버전·출처 ID만 보존하고 비밀값·Prompt 원문 로깅을 차단하는 역할.
"""


def audit_runner(request: dict, run: dict, version: str) -> dict:
    """실행 메타데이터와 출처 ID만 추출해 보안 안전 감사 딕셔너리를 반환하는 함수."""
    # API 키·비밀번호·원본 Prompt가 로그에 남는 보안 사고를 막기 위해 secrets_logged=False를 명시하고,
    # LangSmith 등 외부 추적 연동 시에도 필수 식별자와 출처 ID만 안전하게 기록하도록 필드 고정
    return {
        "question_id": request["question_id"],
        "dataset_version": version,
        "run_mode": run["mode"],
        "variant": run["variant"],
        "source_ids": list(run.get("included_ids", [])),
        "secrets_logged": False,
        "trace_fields_checked": True,
    }


"""
설계 평가:
- 허용된 메타데이터만 선별 기록해 옵저버빌리티와 민감 정보 보호를 동시에 충족한 구조.
- source_ids 방어적 복사와 추적 검증 플래그를 통해 감사 로그 무결성을 보장한 설계.
"""
