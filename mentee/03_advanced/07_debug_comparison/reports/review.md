# 수행 기록 · Day28 실습 07

**실행한 모드:** `live` (`level: 03_advanced`, `dataset_version: d28-eval-v1`, `comparison_kind: offline_version_comparison_not_online_AB`)

**작성 TODO:** `score_delta`, `find_problem_stage`, `compare_four_variants`, `regression_decision`

## 1. 질문·입력
- **어떤 `question_id`를 사용했는가?**
  - `comparisons`에 포함된 `Q01` 1개 질문을 사용함.
- **Gold Label을 Target 입력에 전달하지 않았는가?**
  - `baseline`과 `rerank_only` 실행은 Gold 없이 수행되었고, Gold 목록(`gold`)과 등급(`grades`)은 Target 외부의 `compare_four_variants`·`find_problem_stage` 사후 평가·진단 단계에서만 전달됨.

## 2. 실제 확인한 출력
- **결과 JSON과 핵심 점수·출처 ID:**
  - 별도 출처 문서 ID(`ranked_ids`)는 `result.json`에 출력되지 않았으며, `Q01`에 대한 `baseline` vs `rerank_only` 비교 점수와 회귀 판정만 기록됨.
  - **`baseline` / `rerank_only` 공통 점수 (`k=3`, `gold_count=1`, `retrieved_count=3`)**: `recall_at_k: 1.0`, `precision_at_k: 0.3333...`, `hit_at_k: 1`, `rr_at_k: 1.0`, `dcg_at_k: 7.0`, `ndcg_at_k: 1.0`.
  - **변화량 및 진단**: `baseline_recall: 1.0`, `rerank_recall: 1.0`, `delta_recall: 0.0`, `diagnosis: "inspect_answer_grounding"`.
  - **회귀 게이트 (`regression`)**: `regression: false`, `error_count: 0`, `hold_release: false`, `reason: "추가 사람 평가 필요"`.
- **No-answer / 실패 / 정상의 차이:**
  - **No-answer**: `score_delta`와 `regression_decision`에서 `before` 또는 `after`가 `None`이면 변화량을 `None`으로 두고 회귀로 판정하지 않음(본 `Q01`은 유효 질문이므로 해당 없음).
  - **실패 (회귀·오류 보류)**: `after < before`이거나 `error_count > 0`이면 `hold_release: true`, `reason: "회귀/오류 발견"`으로 배포를 보류함(이번 실행에서는 `delta_recall: 0.0`, `error_count: 0`으로 해당 없음).
  - **정상 (게이트 통과 및 사람 검증 대기)**: `baseline`과 `rerank_only` 모두 `recall_at_k: 1.0`, `ndcg_at_k: 1.0`으로 회귀 없이 통과했으나(`hold_release: false`), 자동 승인 대신 `reason: "추가 사람 평가 필요"`로 사람 검수 단계를 남김.

## 3. 해설
- **왜 이 공식 또는 분기 조건이 필요한가?**
  - `compare_four_variants`에서 동일한 `gold`·`grades`·`k=3` 조건을 고정하고 한 번에 하나의 구성만 변경한 변형(`baseline` vs `rerank_only` 등)을 비교하는 이유는, 여러 요소를 동시에 바꿨을 때 성능 변화의 원인을 특정할 수 없기 때문임.
  - `score_delta`의 `None` 분기와 `round(..., 6)` 처리는 No-answer 사례의 허위 증감 계산과 부동소수점 미세 오차로 인한 회귀 오탐을 막기 위함.
  - `regression_decision`에서 게이트를 통과해도 `"추가 사람 평가 필요"`를 남기는 이유는, `Q01`처럼 검색 지표가 `1.0`이고 회귀가 없더라도(`diagnosis: "inspect_answer_grounding"`) 생성 답변의 근거 충실도와 실제 온라인 환경 적합성은 자동 게이트만으로 확정할 수 없기 때문임.
- **평가 결과가 좋지 않다면 다음에 수정할 모듈은 어디인가?**
  - `diagnosis` 결과에 따라 수정 모듈을 결정함: 이번 `Q01`처럼 검색 지표는 만점(`1.0`)인데 `"inspect_answer_grounding"`이 반환되면 **생성 Prompt·출처 검증(Answer Grounding)**을 점검하고, 후보 누락이면 **초기 Retriever(Query·Indexing·Candidate-k)**, 리랭킹/컨텍스트 누락이면 **Reranker·Context Top-N**을 수정함.
  - `hold_release: true`가 발생하면 문제 변형의 변경 사항을 되돌리거나 `error_count`를 유발한 런타임 오류를 먼저 해결함.

## 4. 11월 26일 Agent와 연결
- **Agent가 이 RAG 검색 Tool을 사용하기 전에 추가로 확인해야 할 것은 무엇인가?**
  1. **오프라인 비교 통과 ≠ 실서비스 배포 승인**: `comparison_kind`가 `"offline_version_comparison_not_online_AB"`이고 `reason`이 `"추가 사람 평가 필요"`이므로, Agent 연결 전 `inspect_answer_grounding` 대상인 답변 근거 충실도와 실제 트래픽 기준 사람 평가를 반드시 거칠 것.
  2. **변경된 Tool 구간의 비용·지연 대비 효용 확인**: `Q01`에서 `baseline`과 `rerank_only`의 검색·순위 점수가 모두 `1.0`으로 동일(`delta_recall: 0.0`)하므로, 추가 지연과 연산 비용이 드는 리랭킹 적용 시 더 넓은 평가셋에서 실제 개선 폭이 있는지 확인한 뒤 Agent Tool로 채택할 것.
  3. **버전·모드 일관성 검증**: Agent가 사용하는 RAG Tool을 교체할 때마다 동일한 `dataset_version`(`d28-eval-v1`)과 `live` 모드로 회귀 게이트(`hold_release: false`)를 통과했는지 확인할 것.