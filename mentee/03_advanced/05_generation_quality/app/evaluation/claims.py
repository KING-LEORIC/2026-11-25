"""
RAG 생성 답변의 Claim 단위 근거 충실도(Faithfulness) 산출 및 사유 요약 모듈.
제공된 Context 대비 답변 주장의 지지 비율을 계산하고 비지원 항목을 구체적으로 기록하는 역할.
"""


def claim_faithfulness(claims: list[dict]) -> float | None:
    """Claim 목록 중 근거가 지지하는 비율을 반환하고 Claim이 없으면 None을 반환하는 함수."""
    # 검토할 Claim이 0건일 때 ZeroDivisionError나 임의 0점·1점 왜곡을 막기 위해 None 반환
    if not claims:
        return None
    # supported 값에 불리언 외 타입이 섞여도 0/1로 안전하게 합산하기 위해 bool() 정규화 적용
    return sum(bool(c["supported"]) for c in claims) / len(claims)


def describe_claim_result(claims: list[dict]) -> str:
    """비지원 Claim 텍스트를 나열하고 'Claim 없음'과 '모든 Claim 지원' 상태를 구분 반환하는 함수."""
    # 검토할 주장이 아예 없는 경우를 '모든 Claim 지원'으로 오해하는 오류를 막기 위한 조기 분기
    if not claims:
        return "검토할 Claim 없음: 별도 판정 필요"
    # 어느 주장이 환각·근거 부족인지 즉시 추적할 수 있도록 미지원 Claim 본문만 선별 추출
    unsupported = [c["text"] for c in claims if not c["supported"]]
    # Reference Answer 비교가 아닌 제공된 Context 기준 일치 여부를 명확히 드러내기 위한 상태 문구 반환
    return (
        "근거 불충분: " + ", ".join(unsupported)
        if unsupported
        else "모든 Claim이 제공된 Context와 일치"
    )


"""
설계 평가:
- 수치 산출(claim_faithfulness)과 사유 서술(describe_claim_result)을 분리해 정량·정성 진단을 병행한 구조.
- 'Claim 없음'과 '전부 지원'을 엄격히 구별해 빈 응답이 만점으로 오인되는 함정을 차단한 설계.
"""
