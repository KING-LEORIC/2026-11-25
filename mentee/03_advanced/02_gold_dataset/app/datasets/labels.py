"""
RAG 평가용 Gold 청크 ID 추출 및 무결성 검증 모듈.
정답 레이블에서 중복을 제거하고 실제 코퍼스 존재 여부를 사전 검증하는 역할.
"""


def select_gold(question_id: str, gold: dict) -> list[str]:
    """gold[question_id]에서 모델 검색 결과를 배제한 순수 정답 청크 ID 목록을 반환하는 함수."""
    # 모델 검색 결과가 아닌 평가용 정답 레이블만 격리 추출하고 원본 시퀀스 변경을 막기 위해 리스트 복사
    ids = list(gold[question_id])
    # set() 변환 시 원래 순서가 깨지는 문제를 방지하면서 중복 ID만 제거하기 위해 삽입 순서 보존 딕셔너리 활용
    return list(dict.fromkeys(ids))


def validate_gold_ids(ids: list[str], corpus: dict) -> bool:
    """청크 ID 중복 여부와 모든 ID의 코퍼스 내 실존 여부를 동시 검증하는 함수."""
    # 중복 ID로 인한 Recall 과대 산정을 막고, 코퍼스에 없는 유령 ID가 평가에 섞이는 오류를 차단하기 위한 이중 검사
    return len(ids) == len(set(ids)) and all(cid in corpus for cid in ids)


"""
설계 평가:
- 추출(select_gold)과 검증(validate_gold_ids)을 분리해 평가 전 데이터 품질 게이트를 명확히 구성한 구조.
- 순서 보존 중복 제거와 집합 길이 비교를 활용해 간결하면서도 정확한 무결성 검사를 구현한 설계.
"""
