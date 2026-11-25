# 평가 요약 및 실패·결과 JSON 직렬화 저장을 위한 표준 라이브러리 임포트
# - json : allow_nan=False 등 엄격한 JSON 포맷 변환
import json

# OS 독립적인 출력 파일 경로 생성 및 상위 디렉터리 보장을 위한 임포트
# - Path : 디렉터리 자동 생성 및 UTF-8 파일 쓰기
from pathlib import Path

# 코퍼스 원본 데이터 로드를 위한 데이터셋 유틸리티 임포트
# - read_json : corpus.json을 읽어 출처 무결성 대조 기준 구성
from coursekit.eval_dataset import read_json

# 개별 실행의 검색·순위 지표 산출 및 전체 집계를 위한 임포트
# - evaluate_retrieval : 단건 ranked_ids 기준 Recall·Precision·RR·DCG·nDCG 계산
# - summarize_retrieval : 다건 평가 지표의 평균 및 모수 통계 집계
from coursekit.eval_metrics import evaluate_retrieval, summarize_retrieval

"""
Target 실행 결과(Run)와 Gold·등급을 결합해 단건 평가·집계 보고서·JSON 저장·1차 Quality Gate를 수행하는 모듈.
출처 위조 및 비공개 문서 인용 차단, 모드/버전 혼합 방지, Agent 연결 전 최소 통과 기준 검증을 담당하는 역할.
"""


def source_integrity(run):
    """실행 결과의 인용 출처(sources)가 실제 색인 코퍼스와 일치하고 공개·최신 상태인지 검증하는 함수."""
    # 허위 출처 ID나 비공개·구버전 문서 인용을 적발하기 위해 원본 코퍼스를 chunk_id 기준으로 색인화
    corpus = {d["chunk_id"]: d for d in read_json("corpus.json")}
    included = set(run.get("included_ids", []))
    for s in run.get("sources", []):
        # LLM Context(included_ids)에 포함되지 않은 문서를 출처로 허위 기재하는 것 방지
        if s.get("chunk_id") not in included:
            return False
        doc = corpus.get(s.get("chunk_id"))
        # 코퍼스에 없거나 미준비·구버전·비공개(non-public) 문서가 노출되는 보안·품질 사고 차단
        if (
            doc is None
            or not doc["ready"]
            or not doc["is_current"]
            or doc["access_level"] != "public"
        ):
            return False
        # 출처 위치(source_locator) 변조 및 bool 등 비정수 인용 ID 유입 차단
        if (
            s.get("source_locator") != doc["source_locator"]
            or type(s.get("citation_id")) is not int
        ):
            return False
        # 라이브 DB 마이그레이션 이후에는 citation_id가 달라질 수 있으므로 offline_fixture 모드에서만 고정 ID 대조
        if (
            run.get("mode") == "offline_fixture"
            and s["citation_id"] != doc["fixture_citation_id"]
        ):
            return False
    # 정상 답변(answered) 상태인데 출처 목록이 비어 있는 무근거 응답 차단
    if run.get("status") == "answered" and not run.get("sources"):
        return False
    return True


def evaluate_record(example, run, gold, grades, k=3):
    """단건 질문 입력(example)과 실행 결과(run)를 Gold·등급과 결합해 상세 평가 레코드를 생성하는 함수."""
    # 다른 질문의 실행 결과가 잘못 매칭되어 오채점되는 사고 방지
    if run["question_id"] != example["question_id"]:
        raise ValueError("question_id 일치 필요")
    # 허용된 실행 모드 외의 비정상 문자열 유입 차단
    if run["mode"] not in ("offline_fixture", "live"):
        raise ValueError("실행 모드를 확인하세요")
    # 평가에 필요한 Target Trace 핵심 필드가 하나라도 누락되면 불완전 평가 대신 즉시 실패 처리
    if not all(
        field in run
        for field in (
            "ranked_ids",
            "candidate_ids",
            "included_ids",
            "answer",
            "status",
            "sources",
        )
    ):
        raise ValueError("Target Trace 필수 항목 누락 - 평가 불가능")
    metrics = evaluate_retrieval(run["ranked_ids"], gold, grades, k)
    # 검색 지표, 출처 무결성, No-answer 거절 정확도, 단계별 지연 시간, 답변 미리보기(120자 제한) 통합 반환
    return {
        "question_id": example["question_id"],
        "variant": run["variant"],
        "mode": run["mode"],
        "data_version": run["data_version"],
        "metrics": metrics,
        "ranked_ids": run["ranked_ids"],
        "included_ids": run["included_ids"],
        "status": run["status"],
        "sources_valid": source_integrity(run),
        "no_answer_result": (
            "correct_abstention"
            if run["status"] == "insufficient_context"
            else "unsupported_answer"
        )
        if not example["answerable"]
        else "not_no_answer",
        "latency_ms": run.get("total_elapsed_ms"),
        "timing_ms": run.get("timing_ms", {}),
        "answer_preview": run["answer"][:120],
    }


def report_summary(rows):
    """평가 레코드 목록을 단일 모드·버전·변형 조건 하에서 집계해 요약 딕셔너리를 반환하는 함수."""
    # 빈 결과 목록으로 인한 집계 오류 및 무의미한 빈 보고서 생성 방지
    if not rows:
        raise ValueError("실행 결과 없음")
    # 서로 다른 실행 모드·데이터셋 버전·변형이 한 보고서에 섞여 지표 해석이 왜곡되는 것을 원천 차단
    combos = {(r["mode"], r["data_version"], r["variant"]) for r in rows}
    if len(combos) != 1:
        raise ValueError("한 보고서에 서로 다른 모드/버전/변형을 혼합할 수 없습니다.")
    agg = summarize_retrieval([r["metrics"] for r in rows])
    agg["source_integrity_failures"] = sum(not r["sources_valid"] for r in rows)
    agg["insufficient_context"] = sum(
        r["status"] == "insufficient_context" for r in rows
    )
    agg["status_failures"] = sum(
        r["status"] not in ("answered", "insufficient_context") for r in rows
    )
    agg["no_answer_correct_abstentions"] = sum(
        r.get("no_answer_result") == "correct_abstention" for r in rows
    )
    agg["no_answer_unsupported_answers"] = sum(
        r.get("no_answer_result") == "unsupported_answer" for r in rows
    )
    agg.update(zip(("mode", "data_version", "variant"), next(iter(combos))))
    return agg


def write_json(path, data):
    """출력 상위 디렉터리를 자동 생성한 뒤 엄격한 UTF-8 JSON 파일로 저장하는 함수."""
    p = Path(path)
    # outputs 디렉터리가 아직 없을 때 FileNotFoundError가 발생하는 것을 막기 위해 부모 폴더 선행 생성
    p.parent.mkdir(parents=True, exist_ok=True)
    # 표준 JSON 규격을 깨는 NaN/Infinity 저장을 막기 위해 allow_nan=False 강제
    p.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False, default=str)
        + "\n",
        encoding="utf-8",
    )
    return p


def release_gate(summary, *, min_recall=0.70, min_mrr=0.60):
    """검색 품질·출처 무결성·실행 상태·사람 검수·접근 제어를 종합해 1차 Quality Gate 통과 여부를 반환하는 함수."""
    # 정량 검색 임계치뿐 아니라 출처 무결성, 사람 검수, 접근 제어 테스트 통과를 모두 요구해 성급한 배포 차단
    checks = {
        "retrieval_recall": summary.get("mean_recall_at_k") is not None
        and summary["mean_recall_at_k"] >= min_recall,
        "retrieval_mrr": summary.get("mrr_at_k") is not None
        and summary["mrr_at_k"] >= min_mrr,
        "source_integrity": summary.get("source_integrity_failures", 1) == 0,
        "execution_status": summary.get("status_failures", 1) == 0,
        "human_review": summary.get("human_review_passed", False),
        "access_control_tests": summary.get("access_control_passed", False),
    }
    # 1차 교육용 게이트 통과가 곧 운영 배포 승인이 아님을 scope 필드로 명확히 고지
    return {
        "ready_for_agent_review": all(checks.values()),
        "checks": checks,
        "scope": "교육용 1차 Gate. Agent의 Tool 권한·안전성·운영 배포 승인 별도 필요",
    }


"""
설계 평가:
- 출처 무결성 검증(source_integrity)과 혼합 방지(report_summary)로 평가 보고서의 신뢰성을 구조적으로 보장한 설계.
- 1차 Quality Gate에 사람 검수와 접근 제어 테스트를 필수 항목으로 포함해 자동 지표 만능주의를 경계한 구조.
"""
