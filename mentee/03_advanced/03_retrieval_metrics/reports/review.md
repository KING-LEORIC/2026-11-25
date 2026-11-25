# 수행 기록 · Day28 실습 03

**실행한 모드:** `offline_fixture` (`level: 03_advanced`, `dataset_version: d28-eval-v1`)

**작성 TODO:** `calculate_recall`, `count_gold_hits`, `precision_and_hit`, `summarize_valid_recall`

## 1. 질문·입력
- **어떤 `question_id`를 사용했는가?**
  - `metrics`에 포함된 `Q01`, `Q07`, `Q06` 총 3개 질문을 평가 대상으로 사용함.
- **Gold Label을 Target 입력에 전달하지 않았는가?**
  - 검색 결과 목록인 `ranked_ids`는 Gold와 무관하게 생성된 검색 순위이며, Gold 레이블(`gold`)은 검색 입력이 아니라 `calculate_recall`, `count_gold_hits`, `precision_and_hit`의 사후 지표 산출 비교용으로만 전달됨.

## 2. 실제 확인한 출력
- **결과 JSON과 핵심 점수·출처 ID:**
  - **`Q01`** (`gold_count: 1`): `ranked_ids`는 `["FAC-101-C1", "FAC-107-C1", "FAC-102-C1", "FAC-105-C1", "FAC-104-C1"]`이며, Top-3 내 1개 적중으로 `hits_at_3: 1`, `recall_at_3: 1.0`, `precision_at_k: 0.3333...`, `hit_at_k: 1`.
  - **`Q07`** (`gold_count: 2`): `ranked_ids`는 `["FAC-101-C1", "FAC-102-C1", "FAC-107-C1", "FAC-104-C1", "FAC-105-C1"]`이며, Top-3 내 1개 적중(`FAC-104-C1`은 4위)으로 `hits_at_3: 1`, `recall_at_3: 0.5`, `precision_at_k: 0.3333...`, `hit_at_k: 1`.
  - **`Q06`** (`gold_count: 0`): `ranked_ids: []`, `hits_at_3: 0`, `recall_at_3: null`, `precision_at_k: null`, `hit_at_k: null`.
  - **집계 (`aggregation`)**: `mean_recall: 0.75` (`(1.0 + 0.5) / 2`), `evaluated_count: 2`, `excluded_no_answer: 1`.
- **No-answer / 실패 / 정상의 차이:**
  - **No-answer (`Q06`)**: `gold_count: 0`이므로 `recall_at_3`, `precision_at_k`, `hit_at_k`가 모두 `null`로 분리되고 평균 집계에서 제외(`excluded_no_answer: 1`)됨. 만약 0점으로 포함했다면 `mean_recall`이 `0.75`에서 `0.5`로 왜곡되었을 것임.
  - **실패 (부분 누락·예외)**: `Q07`처럼 정답 2개 중 1개만 Top-3에 들어 `recall_at_3: 0.5`로 일부 누락된 경우, 또는 `k < 1`/`bool` 입력 등으로 `ValueError`가 발생해 `outputs/failure.json`이 기록되는 상태(이번 실행에서는 예외 없음).
  - **정상 (`Q01`)**: 필요한 Gold 청크를 Top-3 안에 모두 포함해 `recall_at_3: 1.0`, `hit_at_k: 1`을 달성한 상태.

## 3. 해설
- **왜 이 공식 또는 분기 조건이 필요한가?**
  - `set(ranked[:k]) & set(gold)` 교집합 연산은 `ranked[:k]`나 `gold`에 중복 ID가 포함되더라도 적중 수가 과대 계산되어 Recall이나 Precision이 `1.0`을 넘는 오류를 막기 위해 필요함.
  - `if not gold: return None` 분기와 `summarize_valid_recall`의 `None` 제외 로직은 No-answer 질문(`Q06`)을 0점으로 처리해 전체 평균 Recall이 하락·왜곡되는 것을 방지함.
  - `calculate_recall`의 `type(k) is not int or k < 1` 검사는 `bool`(`True/False`) 유입과 음수 슬라이싱을 차단하고, `precision_and_hit`의 고정 분모 `k`는 검색 결과가 `k`개 미만일 때도 동일한 기준으로 Precision@k를 비교하기 위함.
- **평가 결과가 좋지 않다면 다음에 수정할 모듈은 어디인가?**
  - `Q07`처럼 Top-5(`ranked_ids`) 안에는 문서가 있으나 `k=3` 컷오프 밖(4위)으로 밀려 `recall_at_3: 0.5`가 나온 경우는 **Reranker·정렬 스코어링·Context Top-N** 모듈을 우선 점검해 정답 순위를 끌어올려야 함.
  - 반대로 `ranked_ids` 전체에서도 Gold가 전혀 잡히지 않아 `hit_at_k: 0`이 나온다면 **Query 재작성·Metadata Filter·Indexing·Candidate-k(초기 Retriever)** 모듈을 수정해야 함.

## 4. 11월 26일 Agent와 연결
- **Agent가 이 RAG 검색 Tool을 사용하기 전에 추가로 확인해야 할 것은 무엇인가?**
  1. **`k` 값과 토큰 예산 균형 확인**: `Q07`처럼 복합 질문의 근거가 4위권으로 밀릴 수 있으므로, Agent가 RAG 검색 Tool 호출 시 사용하는 `k` 값이 멀티 청크 근거를 충분히 회수하면서도 컨텍스트 길이를 넘지 않는지 확인할 것.
  2. **Reranker 및 중복 제거 동작 확인**: 검색 Tool이 동일 청크 ID를 중복 반환해 Top-k 슬롯을 낭비하지 않는지, Reranker가 핵심 문서를 상위권으로 올리는지 확인할 것.
  3. **빈 검색 결과(`ranked_ids: []`) 및 저신뢰 대응**: 검색 결과가 비어 있거나 관련 청크가 부족할 때 Agent가 환각 답변을 생성하지 않고 쿼리를 보완해 재검색하거나 답변 보류를 반환하는지 확인할 것.