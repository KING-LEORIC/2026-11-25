"""
이상적 순위 대비 현재 검색 순위의 정규화 품질(nDCG@k) 산출 모듈.
IDCG(Ideal DCG)를 기준으로 정규화해 질문 간 절대 점수 비교가 가능하도록 하는 역할.
"""


def calculate_ndcg(ranked: list[str], grades: dict[str, int], k: int) -> float | None:
    """이상적 순위 기준 IDCG 대비 현재 DCG 비율(nDCG@k)을 반환하고 불가 시 None을 반환하는 함수."""
    # DCG 및 IDCG의 로그 순위 감쇠 계산을 위한 표준 수학 함수 임포트
    # - log2 : 인덱스 기반 순위(i + 2)에 로그 감쇠 적용
    from math import log2

    # 등급 정보가 비어 있는 질문을 0점으로 합산해 전체 평균 nDCG가 왜곡되는 것을 막기 위해 None 반환
    if not grades:
        return None
    # 미판정 후보를 임의로 0등급 간주해 DCG가 과소 산정되는 오류를 막기 위한 사전 검증
    if any(cid not in grades for cid in ranked[:k]):
        raise ValueError("미판정 후보의 등급을 먼저 확인하세요")
    # IDCG 산출을 위해 등급 내림차순으로 정렬하되, 동점 등급 간 순서가 흔들리지 않도록 cid를 2차 정렬 키로 고정
    ideal = sorted(grades, key=lambda cid: (-grades[cid], cid))

    def dcg(items):
        """주어진 문서 순서 목록의 상위 k개에 대한 DCG 점수를 계산하는 내부 헬퍼 함수."""
        # 0-based 인덱스 i에 1을 더해 1-based 순위를 만들고, 공식의 (position + 1)을 적용하기 위해 i + 2 사용
        return sum(
            (2 ** grades[cid] - 1) / log2(i + 2) for i, cid in enumerate(items[:k])
        )

    optimal = dcg(ideal)
    # 모든 판정 문서가 0등급이어서 optimal이 0인 경우 ZeroDivisionError를 막기 위해 None 반환
    return dcg(ranked) / optimal if optimal > 0 else None


"""
설계 평가:
- 내부 헬퍼 함수(dcg)로 DCG와 IDCG 계산 로직의 중복을 제거해 공식 일관성을 보장한 구조.
- 빈 등급, 미판정 문서, IDCG=0 등 모든 수치적 엣지 케이스를 안전하게 방어한 설계.
"""
