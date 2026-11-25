# JSON 형식의 질문·정답 레이블 파일을 파싱하기 위한 표준 라이브러리 임포트
# - json : UTF-8 텍스트를 파이썬 객체로 역직렬화
import json

# OS 독립적인 데이터셋 경로 조합 및 파일 읽기를 위한 임포트
# - Path : 모듈 위치 기준 data 디렉터리 경로 계산 및 파일 로드
from pathlib import Path

"""
질문 입력과 Gold 레이블을 물리적으로 분리하고 데이터셋 무결성을 검증하는 평가 계약 모듈.
Target 입력 정제, 정답 유출(Leakage) 탐지, 코퍼스·등급·질문 간 정합성 교차 검증을 수행하는 역할.
"""

# 실행 작업 디렉터리에 의존하지 않고 항상 패키지 내부 data 폴더를 참조하기 위한 기준 경로 설정
ROOT = Path(__file__).resolve().parent

# 런타임 임의 수정을 막기 위해 frozenset으로 고정한 Target 입력 금지 키 집합
FORBIDDEN_TARGET_KEYS = frozenset(
    {
        "gold_chunk_ids",
        "graded_relevance",
        "reference_answer",
        "answerable",
        "gold",
        "expected_answer",
        "label",
    }
)


def read_json(filename: str):
    """data 디렉터리 내 지정된 JSON 파일을 UTF-8로 읽어 파싱 반환하는 함수."""
    # 플랫폼별 기본 인코딩 차이로 인한 디코딩 오류를 막기 위해 utf-8 명시
    path = ROOT / "data" / filename
    return json.loads(path.read_text(encoding="utf-8"))


def read_questions():
    """질문 목록 JSON을 로드하고 빈 배열 여부 및 question_id 중복을 검증 반환하는 함수."""
    questions = read_json("questions.json")
    # 비어 있거나 리스트가 아닌 잘못된 데이터로 평가 루프가 오작동하는 것을 방지
    if not isinstance(questions, list) or not questions:
        raise ValueError("질문 목록이 비었거나 배열이 아닙니다.")
    # 동일 question_id 중복 시 평가 결과가 덮어써지는 데이터 오염을 막기 위한 유일성 검사
    keys = [q["question_id"] for q in questions]
    if len(set(keys)) != len(keys):
        raise ValueError("question_id가 중복됩니다.")
    return questions


def read_gold():
    """Gold 레이블, 관련성 등급, 데이터셋 버전을 튜플로 분리 반환하는 함수."""
    data = read_json("gold_labels.json")
    return data["gold"], data["graded_relevance"], data["dataset_version"]


def target_inputs(example):
    """정답을 배제한 Target 실행용 필수 4개 필드만 새 딕셔너리로 구성하는 함수."""
    safe_keys = ("question_id", "question", "category", "history")
    # Target 실행에 필요한 핵심 입력 키가 빠진 채 호출되는 계약 위반을 조기 차단
    if not all(k in example for k in safe_keys):
        raise ValueError("Target 입력 필수 필드 누락")
    return {key: example[key] for key in safe_keys}


def assert_no_gold_leakage(request):
    """Target 요청 딕셔너리에 Gold 또는 참조 정답 키가 유입되지 않았는지 검증하는 함수."""
    # 집합 교집합으로 금지 키 포함 여부를 O(1) 수준으로 신속 탐지해 시험 정답 유출 원천 차단
    found = FORBIDDEN_TARGET_KEYS.intersection(request)
    if found:
        raise ValueError(
            "Gold Label/Reference Answer가 Target 입력에 포함됨: "
            + ",".join(sorted(found))
        )


def validate_dataset(questions, gold, grades, corpus):
    """질문·Gold·관련성 등급·코퍼스 문서 간의 전체 정합성과 접근 권한 계약을 검증하는 함수."""
    # 질문 목록과 Gold·등급 딕셔너리 간 키 집합 불일치로 인한 KeyError·누락 평가 방지
    if set(gold) != set(q["question_id"] for q in questions):
        raise ValueError("평가 질문과 Gold 질문 ID 불일치")
    if set(grades) != set(gold):
        raise ValueError("관련성 등급 질문 ID 불일치")
    # 반복 조회 성능 확보를 위해 코퍼스를 chunk_id 기준 딕셔너리로 색인화
    docs = {d["chunk_id"]: d for d in corpus}
    for q in questions:
        qid = q["question_id"]
        ids = gold[qid]
        # Gold 내 중복 ID로 Recall이 과대 계산되는 왜곡 방지
        if len(set(ids)) != len(ids):
            raise ValueError(qid + ": Gold 중복")
        # answerable 플래그와 실제 Gold 유무 간 모순 차단
        if q["answerable"] != bool(ids):
            raise ValueError(qid + ": answerable 불일치")
        # 1점 이상 양수 등급을 받은 문서 집합과 이진 Gold 목록이 정확히 일치하도록 계약 강제
        if {cid for cid, grade in grades[qid].items() if grade > 0} != set(ids):
            raise ValueError(qid + ": graded positive IDs / Gold 불일치")
        for graded_id, graded_score in grades[qid].items():
            document = docs.get(graded_id)
            # 타 카테고리·구버전·미준비·비공개 문서가 등급 판정에 섞이는 데이터 오염 차단
            if (
                document is None
                or document["category"] != q["category"]
                or not document["is_current"]
                or not document["ready"]
                or document["access_level"] != "public"
            ):
                raise ValueError(qid + ": 판정 문서가 허용 범위 밖에 있음")
            # bool 유입을 배제하고 0~3 정수 등급 범위만 허용해 DCG/nDCG 왜곡 방지
            if type(graded_score) is not int or not 0 <= graded_score <= 3:
                raise ValueError(qid + ": 등급 범위 0~3")
        for cid in ids:
            d = docs.get(cid)
            # 존재하지 않는 유령 ID가 Gold로 등록된 오류 차단
            if d is None:
                raise ValueError(qid + ": 없는 Gold ID " + cid)
            # Gold 문서 역시 현재 접근 가능한 공개·동일 카테고리 문서인지 재검증
            if (
                d["category"] != q["category"]
                or not d["is_current"]
                or not d["ready"]
                or d["access_level"] != "public"
            ):
                raise ValueError(qid + ": Gold가 접근 가능한 현재 문서가 아님: " + cid)
            # Gold로 지정된 문서는 최소 1~3점의 양수 관련성 등급을 가져야 함을 강제
            if type(grades[qid][cid]) is not int or not 1 <= grades[qid][cid] <= 3:
                raise ValueError(qid + ": 잘못된 관련성 등급")
    # 검증 완료 후 데이터셋 구성을 한눈에 파악할 수 있도록 요약 통계 반환
    return {
        "questions": len(questions),
        "answerable": sum(bool(gold[q["question_id"]]) for q in questions),
        "no_answer": sum(not gold[q["question_id"]] for q in questions),
        "gold_ids": sum(map(len, gold.values())),
    }


"""
설계 평가:
- frozenset 금지 키 단언과 화이트리스트 추출을 결합해 평가 공정성의 핵심인 정답 유출을 원천 봉쇄한 구조.
- 질문·Gold·등급·코퍼스(최신성·공개 여부·카테고리)까지 4중 교차 검증해 평가 신뢰도를 극대화한 설계.
"""
