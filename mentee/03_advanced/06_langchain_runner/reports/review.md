# 수행 기록 · Day28 실습 06

**실행한 모드:** `live` (`level: 03_advanced`, `dataset_version: d28-eval-v1`, `langchain_runnable: true` / 이전 실패 이력인 `outputs/failure.json` 역시 `mode: live`로 기록됨)

**작성 TODO:** `safe_target_input`, `invoke_target`, `evaluate_target_run`, `audit_runner`

## 1. 질문·입력
- **어떤 `question_id`를 사용했는가?**
  - `runner_results`에 포함된 `Q01`, `Q02`, `Q03` 총 3개 질문을 사용함.
- **Gold Label을 Target 입력에 전달하지 않았는가?**
  - `safe_target_input`이 `question_id`, `question`, `category`, `history` 4개 키만 새 `dict`로 복사해 Gold·Reference 필드를 제거함.
  - `invoke_target` 내부에서도 `target.invoke(request)` 호출 직전 `assert_no_gold_leakage(request)`로 금지 키(`FORBIDDEN_TARGET_KEYS`) 유입 여부를 재검증하고, Gold·등급(`grades`)은 Target 외부의 `evaluate_target_run`에서만 사후 결합함.

## 2. 실제 확인한 출력
- **결과 JSON과 핵심 점수·출처 ID:**
  - `Q01`, `Q02`, `Q03` 모두 `variant: "both"`, `status: "answered"`, `sources_valid: true`, `no_answer_result: "not_no_answer"`로 완료됨.
  - **공통 검색·순위 점수 (`k=3`, `gold_count=1`, `retrieved_count=3`)**: `recall_at_k: 1.0`, `precision_at_k: 0.3333...`, `hit_at_k: 1`, `rr_at_k: 1.0`, `dcg_at_k: 7.0`, `ndcg_at_k: 1.0`.
  - **공통 출처 ID**: `ranked_ids`는 `["FAC-102-C1", "FAC-109-C1", "FAC-107-C1", "FAC-103-C1", "FAC-101-C1"]`이며, 실제 컨텍스트에 포함된 출처(`included_ids` / `audit.source_ids`)는 `["FAC-102-C1", "FAC-109-C1"]`(1위 `FAC-102-C1` 적중)로 기록됨.
  - **지연 시간 (`latency_ms`)**: `Q01` `15419.738ms`(rerank `5215.696ms` 포함 초기 지연), `Q02` `2872.16ms`(rewrite `1482.62ms`, generation `1026.527ms`), `Q03` `3327.386ms`(rewrite `1674.264ms`, generation `1191.552ms`).
  - **감사(`audit`) 및 실패 기록(`outputs/failure.json`)**: `result.json`의 모든 케이스는 `secrets_logged: false`, `trace_fields_checked: true`로 기록됨. 한편 `outputs/failure.json`에는 `status: "execution_failed"`, `stage: "evaluation"`, `error_type: "FileNotFoundError"`, `mode: "live"`가 비밀값 없이 기록됨.
- **No-answer / 실패 / 정상의 차이:**
  - **No-answer**: `no_answer_result`로 구분되며 이번 `Q01`~`Q03`은 모두 `"not_no_answer"`로 정답이 존재하는 질문임(No-answer 질문이라면 검색 점수가 `null`로 분리됨).
  - **실패 (`outputs/failure.json`)**: 필수 파일·경로 누락으로 `FileNotFoundError`가 발생한 `stage: "evaluation"` 중단 사례처럼, 실행 실패 시 API Key·Password·Prompt 원문 없이 `status`, `stage`, `error_type`, `mode`만 `failure.json`에 기록됨(`invoke_target`의 `question_id` 불일치 시에도 `ValueError`로 차단).
  - **정상 (`outputs/result.json`)**: `langchain_runnable: true` 환경에서 `Q01`~`Q03` 모두 `status: "answered"`, `sources_valid: true`, `rr_at_k: 1.0`, `ndcg_at_k: 1.0`으로 정상 답변과 최상위 출처 적중을 달성한 상태.

## 3. 해설
- **왜 이 공식 또는 분기 조건이 필요한가?**
  - `safe_target_input`의 4개 키 화이트리스트 복사와 `invoke_target`의 `assert_no_gold_leakage` 이중 검사는 Target이 정답(`gold_chunk_ids`, `reference_answer`)을 미리 보고 답을 맞히는 데이터 누수를 원천 차단하기 위해 필요함.
  - `invoke_target`에서 `not isinstance(result, dict) or result.get("question_id") != request["question_id"]`를 검사하는 것은 비정상 응답 타입이나 질문 ID 뒤섞임으로 인한 오채점을 방지하기 위함.
  - `evaluate_target_run`에서 Target 외부에서만 Gold를 결합하고 `audit_runner`에서 `secrets_logged: false`로 비밀값·Prompt 원문을 제외하는 것은 공정한 평가 계약과 옵저버빌리티 보안을 동시에 지키기 위함.
- **평가 결과가 좋지 않다면 다음에 수정할 모듈은 어디인가?**
  - `failure.json`의 `FileNotFoundError`처럼 실행 자체가 실패하면 **데이터셋·인덱스 파일 경로 설정 및 실행 환경 초기화 모듈**을 먼저 수정해야 함.
  - 이번 `result.json` 기준 검색·순위 점수(`recall_at_k: 1.0`, `ndcg_at_k: 1.0`)는 최상이지만 지연 시간 측면에서 `Q01`의 `rerank`(5215ms)와 공통 `rewrite`(1480~1760ms) 비중이 크므로, 응답 속도 개선이 필요하면 **Reranker 웜업/경량화 및 Query Rewrite 모듈**을 최적화함(검색 점수가 낮아질 경우 Retriever·Reranker 점검).

## 4. 11월 26일 Agent와 연결
- **Agent가 이 RAG 검색 Tool을 사용하기 전에 추가로 확인해야 할 것은 무엇인가?**
  1. **필수 파일·인덱스 헬스체크 (`FileNotFoundError` 예방)**: `failure.json` 사례처럼 실행 시 필요한 인덱스·데이터 파일이 누락되면 `live` 파이프라인이 중단되므로, Agent가 Tool을 호출하기 전 인덱스 로드 및 GPU/DB/API 연결 상태를 사전 확인할 것.
  2. **Cold-start 지연 및 Timeout 설정**: `Q01`에서 첫 `rerank` 포함 `15.4초`가 소요된 반면 `Q02`·`Q03`은 `2.8~3.3초`대로 안정화되었으므로, Agent의 Tool Timeout을 충분히 잡거나 초기 모델 웜업을 수행할 것.
  3. **입력 스키마 및 트레이싱 보안 (`secrets_logged: false`)**: Agent가 Tool에 `question_id`, `question`, `category`, `history` 계약만 전달하고, LangSmith 등 외부 추적 연동 시 API Key·비밀값·민감 Prompt가 로그에 남지 않는지 확인할 것.