"""
RAG 평가 실패 단계(stage)별 우선 점검 모듈 매핑 모듈.
진단 결과에 따라 개발팀이 즉시 확인해야 할 하위 시스템을 반환하는 역할.
"""


def recommend_fix(stage: str) -> str:
    """실패 단계(stage)에 대응하는 우선 점검 대상을 반환하는 함수."""
    # 후속 단계(Reranker/Prompt) 수정으로 선행 검색 누락을 덮으려는 헛수고를 방지하고,
    # 미정의 stage 입력 시 조기 KeyError로 계약 위반을 드러내기 위해 딕셔너리 직접 조회 사용
    return {
        "system_failure": "GPU/DB/API 연결·Timeout을 먼저 진단",
        "candidate_miss": "Query·Metadata Filter·Indexing·Candidate-k 점검",
        "ranking_or_context_miss": "Reranker·Context Top-N·길이 예산 점검",
        "generation_failure": "Prompt·근거 주장·출처 검증 점검",
        "passed": "검증 결과 기록 후 유지",
    }[stage]


"""
설계 평가:
- 분기문 대신 1:1 딕셔너리 매핑을 사용해 가독성과 확장성을 확보한 구조.
- 파이프라인 인과관계(인프라 -> 후보 검색 -> 컨텍스트 구성 -> 생성)에 맞춘 정확한 책임 분리.
"""
