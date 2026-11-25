"""
RAG 답변의 질문 적합성(Relevance)과 정답성(Correctness) 분리 기록 모듈.
정해진 평가 루브릭(Rubric) 외 값 유입을 차단하고 두 평가 축을 독립 필드로 보존하는 역할.
"""


def label_answer_quality(relevance: str, correctness: str) -> dict:
    """질문 적합성과 정답성 레이블을 루브릭 검증 후 별도 딕셔너리 필드로 반환하는 함수."""
    # 오타나 비표준 레이블 유입으로 후속 집계·필터링이 깨지는 것을 막기 위한 허용 집합 정의
    valid_r = {"높음", "보통", "낮음", "평가 보류"}
    valid_c = {"정답", "부분정답", "오답", "판정 불가"}
    # 정해진 루브릭 범위를 벗어난 판정 값을 조기에 예외 처리해 데이터 일관성 보장
    if relevance not in valid_r or correctness not in valid_c:
        raise ValueError("판정 값이 정해진 Rubric 밖입니다.")
    # 근거와 일치해 정답성이 높아도 질문 의도에 어긋날 수 있으므로 단일 점수 통합 대신 두 축을 분리 보존
    return {"answer_relevance": relevance, "answer_correctness": correctness}


"""
설계 평가:
- 화이트리스트 루브릭 검증을 통해 평가 데이터셋의 범주형 값 무결성을 강제한 구조.
- 적합성과 정답성을 별도 필드로 유지해 답변 품질 실패 원인을 다각도로 진단할 수 있는 설계.
"""
