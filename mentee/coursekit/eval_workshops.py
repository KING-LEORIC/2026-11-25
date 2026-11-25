# 평가 질문·정답·등급 로드 및 Gold 유출 차단을 위한 데이터셋 계약 유틸리티 임포트
# - read_gold : Gold 청크 ID, 관련성 등급, 데이터셋 버전 로드
# - read_json : 실습별 픽스처(failure_cases, corpus, generation_claims) 로드
# - read_questions : 평가 질문 목록 로드 및 중복 검증
# - target_inputs : Gold를 제거한 안전 Target 입력 딕셔너리 생성
from coursekit.eval_dataset import read_gold, read_json, read_questions, target_inputs

# None(No-answer)을 제외한 유효 지표 평균 계산 유틸리티 임포트
# - mean_valid : 실습 04 MRR@3 집계 시 No-answer 제외 평균 산출
from coursekit.eval_metrics import mean_valid

# Target 실행 래퍼 및 오프라인/라이브 실행기 임포트
# - as_runnable : 일반 함수를 LangChain Runnable 호환 객체로 래핑
# - target_fixture : 과금 없는 고정 학습 데이터 기반 Target 실행
# - target_live : 실제 CUDA E5·pgvector·CrossEncoder·ChatOpenAI 기반 실행
from coursekit.eval_target import as_runnable, target_fixture, target_live

"""
Day28 실습 01~08 공통 실행 디스패처(Dispatcher) 모듈.
학생이 구현한 hooks를 받아 레벨과 관계없이 동일한 입출력 계약으로 오프라인·라이브 평가를 구동하는 역할.
"""


def _base():
    """실습 전반에서 공통으로 사용하는 질문·Gold·등급·버전 데이터를 일괄 로드하는 내부 헬퍼 함수."""
    q = read_questions()
    gold, grades, version = read_gold()
    return q, gold, grades, version


def execute(number, hooks, *, live=False, level="01_basic"):
    """실습 번호(1~8)에 맞는 평가 시나리오를 실행하고 표준 결과 딕셔너리를 반환하는 함수."""
    # 실습 01~05는 제공 레이블·Fixture 계산 전용이므로 불필요한 API 과금 및 오용을 막기 위해 --live 차단
    if live and number < 6:
        raise ValueError(
            "실습 01~05는 제공 레이블/Fixture 기반 계산입니다. 06~08에서 --live로 실제 RAG 평가를 수행하세요."
        )
    questions, gold, grades, version = _base()
    qby = {q["question_id"]: q for q in questions}
    cases = read_json("failure_cases.json")
    result = {
        "exercise": number,
        "level": level,
        "dataset_version": version,
        "mode": "live" if live else "offline_fixture",
    }

    # 실습 01: 실패 단계 분류·근거 서술·권고안·보안 감사 훅 순차 실행
    if number == 1:
        rows = []
        for case in cases:
            stage = hooks["classify_case"](case)
            evidence = hooks["describe_evidence"](case, stage)
            row = {"case_id": case["case_id"], "stage": stage, "evidence": evidence}
            if "recommend_fix" in hooks:
                row["recommendation"] = hooks["recommend_fix"](stage)
            if "audit_decision" in hooks:
                row["audit"] = hooks["audit_decision"](case, stage, evidence)
            rows.append(row)
        result["cases"] = rows

    # 실습 02: Gold 청크 추출·코퍼스 유효성 검사·No-answer 분리·감사 기록 및 Gold 비유출 예시 첨부
    elif number == 2:
        corpus = {c["chunk_id"]: c for c in read_json("corpus.json")}
        rows = []
        for qid in ("Q01", "Q05", "Q06", "Q07"):
            ids = hooks["select_gold"](qid, gold)
            ok = hooks["validate_gold_ids"](ids, corpus)
            row = {"question_id": qid, "gold_chunk_ids": ids, "valid_ids": ok}
            if "label_no_answer" in hooks:
                row["no_answer"] = hooks["label_no_answer"](qid, gold)
            if "audit_gold" in hooks:
                row["audit"] = hooks["audit_gold"](qid, ids, version)
            rows.append(row)
        result["annotations"] = rows
        # Target 입력 계약에 Gold가 포함되지 않음을 확인시키기 위한 예시 첨부
        result["target_example"] = target_inputs(qby["Q01"])

    # 실습 03: Recall@3·적중 수·Precision@k·Hit@k 계산 및 유효 Recall 평균 집계
    elif number == 3:
        rows = []
        values = []
        for qid in ("Q01", "Q07", "Q06"):
            run = target_fixture(target_inputs(qby[qid]), "baseline")
            ids = run["ranked_ids"]
            g = gold[qid]
            k = 3
            recall = hooks["calculate_recall"](ids, g, k)
            hits = hooks["count_gold_hits"](ids, g, k)
            row = {
                "question_id": qid,
                "ranked_ids": ids,
                "gold_count": len(g),
                "hits_at_3": hits,
                "recall_at_3": recall,
            }
            if "precision_and_hit" in hooks:
                row.update(hooks["precision_and_hit"](ids, g, k))
            rows.append(row)
            values.append(recall)
        result["metrics"] = rows
        if "summarize_valid_recall" in hooks:
            result["aggregation"] = hooks["summarize_valid_recall"](values)

    # 실습 04: 첫 적중 순위·RR@3·DCG@3·nDCG@3 계산 및 MRR@3 산출
    elif number == 4:
        rows = []
        rr_vals = []
        for qid in ("Q01", "Q07", "Q06"):
            run = target_fixture(target_inputs(qby[qid]), "baseline")
            ids = run["ranked_ids"]
            g = gold[qid]
            rank = hooks["first_relevant_rank"](ids, g, 3)
            # 정답 가능한 질문의 미적중은 0점이지만, No-answer 질문의 RR은 MRR 평균에서 제외하기 위해 None 유지
            rr = hooks["calculate_rr"](rank) if g else None
            row = {"question_id": qid, "first_rank": rank, "rr_at_3": rr}
            if "calculate_dcg" in hooks:
                row["dcg_at_3"] = hooks["calculate_dcg"](ids, grades[qid], 3)
            if "calculate_ndcg" in hooks:
                row["ndcg_at_3"] = hooks["calculate_ndcg"](ids, grades[qid], 3)
            rows.append(row)
            rr_vals.append(rr)
        result["ranking"] = rows
        result["mrr_at_3"] = mean_valid(rr_vals)

    # 실습 05: Claim 단위 근거 충실도·루브릭 분리·사람 검수 메타데이터 생성
    elif number == 5:
        cases = read_json("generation_claims.json")
        rows = []
        for case in cases:
            f = hooks["claim_faithfulness"](case["claims"])
            notes = hooks["describe_claim_result"](case["claims"])
            row = {
                "case_id": case["case_id"],
                "faithfulness": f,
                "reason": notes,
                "label_source": "human_fixture",
            }
            if "label_answer_quality" in hooks:
                row.update(
                    hooks["label_answer_quality"](
                        case["relevance"], case["correctness"]
                    )
                )
            if "prepare_human_review" in hooks:
                row["human_review"] = hooks["prepare_human_review"](
                    case["case_id"], f, "교육용 검수자"
                )
            rows.append(row)
        result["generation_reviews"] = rows

    # 실습 06: Runnable 래핑 Target의 안전 입력 추출·실행·외부 채점·감사 로그 기록
    elif number == 6:
        target = as_runnable(
            lambda req: (
                target_live(req, "both") if live else target_fixture(req, "both")
            )
        )
        rows = []
        for example in questions[:3]:
            req = hooks["safe_target_input"](example)
            run = hooks["invoke_target"](target, req)
            row = {
                "question_id": example["question_id"],
                "source_mode": run["mode"],
                "ranked_ids": run["ranked_ids"],
                "included_ids": run["included_ids"],
            }
            if "evaluate_target_run" in hooks:
                row["evaluation"] = hooks["evaluate_target_run"](
                    example,
                    run,
                    gold[example["question_id"]],
                    grades[example["question_id"]],
                )
            if "audit_runner" in hooks:
                row["audit"] = hooks["audit_runner"](req, run, version)
            rows.append(row)
        result["runner_results"] = rows
        result["langchain_runnable"] = True

    # 실습 07: Baseline 대비 변형 실험군 비교·변화량 산출·회귀 게이트 판정
    elif number == 7:
        # live 모드에서 전체 질문·변형을 모두 돌리면 실제 토큰 비용이 급증하므로 대표 질문 Q01로 제한
        qids = ("Q01", "Q07", "Q06") if not live else ("Q01",)
        rows = []
        for qid in qids:
            req = target_inputs(qby[qid])
            g = gold[qid]
            gr = grades[qid]
            load = lambda v: target_live(req, v) if live else target_fixture(req, v)
            a = load("baseline")
            b = load("rerank_only")
            # 변형별 기본 검색 지표 계산을 위한 평가 함수 임포트
            # - evaluate_retrieval : k=3 기준 Recall@k 등 검색 지표 산출
            from coursekit.eval_metrics import evaluate_retrieval

            m1 = evaluate_retrieval(a["ranked_ids"], g, gr, 3)
            m2 = evaluate_retrieval(b["ranked_ids"], g, gr, 3)
            row = {
                "question_id": qid,
                "baseline_recall": m1["recall_at_k"],
                "rerank_recall": m2["recall_at_k"],
                "delta_recall": hooks["score_delta"](
                    m1["recall_at_k"], m2["recall_at_k"]
                ),
                "diagnosis": hooks["find_problem_stage"](a, g),
            }
            if "compare_four_variants" in hooks:
                # live 실행 시 API 비용 절감을 위해 baseline·rerank_only 2종만 비교하고 오프라인에서는 4종 전체 비교
                variants = (
                    ["baseline", "rerank_only"]
                    if live
                    else ["baseline", "rewrite_only", "rerank_only", "both"]
                )
                runs = {
                    v: (a if v == "baseline" else b if v == "rerank_only" else load(v))
                    for v in variants
                }
                row["matrix"] = hooks["compare_four_variants"](runs, g, gr)
            if "regression_decision" in hooks:
                row["regression"] = hooks["regression_decision"](
                    m1["recall_at_k"], m2["recall_at_k"], 0
                )
            rows.append(row)
        result["comparisons"] = rows
        result["comparison_kind"] = "offline_version_comparison_not_online_AB"

    # 실습 08: 전체 질문 단건 평가·요약 집계·Markdown 보고서 생성·Agent 1차 Gate 판정
    elif number == 8:
        rows = []
        # live 실행 시 비용·시간 제약을 고려해 상위 3개 질문만 평가
        for example in questions[:3] if live else questions:
            qid = example["question_id"]
            req = target_inputs(example)
            run = target_live(req, "both") if live else target_fixture(req, "both")
            rows.append(hooks["evaluate_one"](example, run, gold[qid], grades[qid]))
        summary = hooks["summarize_all"](rows)
        result["summary"] = summary
        result["questions"] = rows
        if "write_summary_report" in hooks:
            result["markdown_report"] = hooks["write_summary_report"](summary, rows)
        if "agent_release_gate" in hooks:
            # 사람 검수·접근 제어 테스트 통과 여부는 자동 확정할 수 없으므로 기본 False로 전달
            result["agent_gate"] = hooks["agent_release_gate"](summary, False, False)
    else:
        raise ValueError("unknown Day28 task index")
    return result


"""
설계 평가:
- 단일 디스패처(execute)와 hooks 계약을 통해 01_basic~03_advanced 전 레벨이 동일한 데이터 파이프라인을 공유하는 구조.
- live 실행 시 과금·지연을 제어하는 문항·변형 제한과 실습 01~05 가드를 내장해 안전하고 일관된 학습 환경을 제공한 설계.
"""
