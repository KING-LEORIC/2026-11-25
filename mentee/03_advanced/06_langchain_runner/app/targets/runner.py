"""
RAG Target 입력 정제 및 Runnable 표준 호출 래퍼 모듈.
정답·참조 필드를 제거한 입력만 구성하고 Target 응답의 스키마·질문 ID 일관성을 검증하는 역할.
"""


def safe_target_input(example: dict) -> dict:
    """질문 실행에 필요한 4개 허용 키만 새 딕셔너리로 복사해 Gold 유출을 차단하는 함수."""
    # 화이트리스트 키만 선별 복사해 gold·reference_answer 등 정답 필드가 Target 입력에 섞이는 누수 원천 차단
    return {
        key: example[key] for key in ("question_id", "question", "category", "history")
    }


def invoke_target(target, request: dict) -> dict:
    """Target 입력의 정답 유출 여부를 재검증한 뒤 Runnable.invoke()를 호출해 결과를 검증 반환하는 함수."""
    # Target 호출 직전 금지 키 포함 여부를 단언하기 위한 데이터 계약 검증 유틸리티 임포트
    # - assert_no_gold_leakage : Gold·Reference 키 유입 시 즉시 ValueError 발생
    from coursekit.eval_dataset import assert_no_gold_leakage

    # 우회 경로로 정답 필드가 주입된 경우에도 실행 직전에 차단하기 위한 이중 방어
    assert_no_gold_leakage(request)
    # 단순 함수 호출이 아닌 RunnableLambda 래핑 객체의 표준 invoke 인터페이스 실행
    result = target.invoke(request)
    # 비정상 반환 타입이나 다른 질문 ID 응답이 섞여 오채점되는 치명적 오류를 막기 위한 응답 계약 검증
    if (
        not isinstance(result, dict)
        or result.get("question_id") != request["question_id"]
    ):
        raise ValueError("Target 출력의 질문 ID 불일치")
    return result


"""
설계 평가:
- 입력 정제(safe_target_input)와 호출 전후 검증(invoke_target)의 이중 가드로 평가 공정성을 확보한 구조.
- LangChain Runnable 인터페이스 계약을 준수해 오프라인 픽스처와 라이브 체인을 동일하게 구동할 수 있는 설계.
"""
