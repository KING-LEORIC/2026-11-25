"""
RAG 파이프라인 케이스별 실패 단계 분류 및 근거 문구 생성 모듈.
시스템 장애와 검색·컨텍스트·생성 단계의 실패를 순차적으로 분리 판별하는 역할.
"""


def classify_case(case: dict) -> str:
    """케이스 상태 지표를 선행 조건 순으로 검사해 실패 stage 문자열을 반환하는 함수."""
    # 인프라 장애를 검색·생성 품질 저하로 오분류하는 것을 막기 위해 시스템 오류 최우선 판별
    if case.get("system_error"):
        return "system_failure"
    # 최초 후보군에 정답 문서가 없으면 이후 랭킹·생성 검증이 무의미하므로 검색 누락 조기 반환
    if not case.get("candidate_has_gold"):
        return "candidate_miss"
    # 후보군에는 있으나 LLM 입력 컨텍스트에서 탈락한 경우 Reranker·길이 제한 문제로 분리
    if not case.get("context_has_gold"):
        return "ranking_or_context_miss"
    # 근거가 전달됐음에도 답변이 지지되지 않으면 프롬프트·환각 등 생성 단계 실패로 판별
    if not case.get("answer_grounded"):
        return "generation_failure"
    return "passed"


def describe_evidence(case: dict, stage: str) -> str:
    """판별된 stage에 대응하는 구체적인 진단 근거 문구를 반환하는 함수."""
    # 후보 누락과 컨텍스트 누락을 명확히 구분해 보고서 내 혼선을 방지하기 위한 고정 근거 매핑
    evidence = {
        "system_failure": "서비스 실행이 실패해 지표를 계산할 수 없음",
        "candidate_miss": "Gold 문서 ID가 최초 검색 후보에 존재하지 않음",
        "ranking_or_context_miss": "Gold는 후보에 있으나 LLM Context에 포함되지 않음",
        "generation_failure": "근거가 Context에 있는데 답변 주장이 지지되지 않음",
        "passed": "검색 후보·Context·답변 검토 조건 충족",
    }
    # 빈 문자열 반환을 원천 차단하고 미정의 stage에 대해 즉시 예외를 발생시키기 위한 직접 인덱싱
    return evidence[stage]


"""
설계 평가:
- Early Return 가드 절을 통해 파이프라인 선후 의존성을 코드 흐름 자체로 명확히 표현한 구조.
- 분류(classify_case)와 설명(describe_evidence)을 분리해 각 함수의 단일 책임을 유지한 설계.
"""
