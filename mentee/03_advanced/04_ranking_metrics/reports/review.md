# 수행 기록 · Day28 실습 04

**실행한 모드:** `offline_fixture` (`level: 03_advanced`, `dataset_version: d28-eval-v1`)

**작성 TODO:** `first_relevant_rank`, `calculate_rr`, `calculate_dcg`, `calculate_ndcg`

## 1. 질문·입력
- **어떤 `question_id`를 사용했는가?**
  - `ranking`에 포함된 `Q01`, `Q07`, `Q06` 총 3개 질문을 평가 대상으로 사용함.
- **Gold Label을 Target 입력에 전달하지 않았는가?**
  - 검색 순위(`ranked`)는 Gold 및 등급 정보와 분리되어 산출된 결과이며, 정답 목록(`gold`)과 관련도 등급(`grades`)은 검색 입력이 아니라 `first_relevant_rank`, `calculate_dcg`, `calculate_ndcg`의 사후 순위·이득 평가 단계에서만 참조됨.

## 2. 실제 확인한 출력
- **결과 JSON과 핵심 점수·출처 ID:**
  - 별도의 출처 문서 ID는 `result.json`에 출력되지 않았고, 질문별 순위·이득 지표와 전체 `mrr_at_3`가 기록됨.
  - **`Q01`**: `first_rank: 3`, `rr_at_3: 0.3333...`, `dcg_at_3: 3.5`, `ndcg_at_3: 0.5`
  - **`Q07`**: `first_rank: 2`, `rr_at_3: 0.5`, `dcg_at_3: 1.8927...`, `ndcg_at_3: 0.2128...`
  - **`Q06`**: `first_rank: null`, `rr_at_3: null`, `dcg_at_3: 0`, `ndcg_at_3: null`
  - **전체 집계**: `mrr_at_3: 0.4166...` (`Q01`의 `0.3333...`과 `Q07`의 `0.5` 평균)
- **No-answer / 실패 / 정상의 차이:**
  - **No-answer (`Q06`)**: 정답이 없는 질문이므로 `first_rank`, `rr_at_3`, `ndcg_at_3`가 모두 `null`(`dcg_at_3: 0`)로 처리되어 `mrr_at_3` 평균 산출에서 제외됨.
  - **실패 (순위 저하·미판정 예외)**: `Q01`은 첫 정답이 3위로 밀려 `rr_at_3: 0.3333...`에 그쳤고, `Q07`은 2위 적중(`rr_at_3: 0.5`)에도 고등급 문서 배치가 밀려 `ndcg_at_3: 0.2128...`로 낮게 나온 순위 품질 저하 사례, 또는 `ranked[:k]`에 미판정 문서가 섞여 `ValueError`가 발생하고 `outputs/failure.json`이 기록되는 상태(이번 실행에서는 예외 없음).
  - **정상 (유효 평가 완료)**: 모든 후보 등급이 확인되어 `first_rank`, `rr_at_3`, `dcg_at_3`, `ndcg_at_3`가 예외 없이 산출되고 유효 질문 기준으로 `mrr_at_3: 0.4166...`이 정상 집계된 상태.

## 3. 해설
- **왜 이 공식 또는 분기 조건이 필요한가?**
  - `first_relevant_rank`의 1-based 순위(`enumerate(ranked[:k], 1)`)와 `calculate_rr`의 `None` 가드는 `1/0` 나눗셈 오류와 `TypeError`를 막고, 첫 정답이 상위에 올수록 높은 역수 점수(`1/rank`)를 부여하기 위해 필요함.
  - `calculate_dcg`의 `(2**grade - 1) / log2(pos + 1)` 공식은 단순 이진 적중을 넘어 고등급 문서의 최상위 배치에 지수적 가중치를 주고 하위 순위는 로그 감쇠를 적용하며, `calculate_ndcg`는 이를 이상적 순위(`IDCG`)로 나누어 질문 간 비교 가능한 `0~1` 정규화 점수를 만듦.
  - `any(cid not in grades for cid in ranked[:k])` 예외 분기는 미판정 문서를 임의로 0등급 처리해 DCG/nDCG가 과소평가되는 왜곡을 차단하며, `not grades` 및 `optimal > 0` 가드는 No-answer·0등급 전용 케이스의 `ZeroDivisionError`와 평균 왜곡을 방지함.
- **평가 결과가 좋지 않다면 다음에 수정할 모듈은 어디인가?**
  - `Q01`(`first_rank: 3`, `ndcg_at_3: 0.5`)이나 `Q07`(`ndcg_at_3: 0.2128...`)처럼 정답 문서를 찾았음에도 최상단 1~2위에 올리지 못해 RR·nDCG가 낮다면 **Reranker·정렬 스코어링·Hybrid 검색 가중치** 모듈을 우선 수정해야 함.
  - `first_rank` 자체가 `None`으로 떨어지면 **초기 Retriever(Query·Embedding·Indexing·Candidate-k)**를 점검하고, 미판정 `ValueError`가 발생하면 **평가용 `grades` 등급 판정 데이터**를 보완해야 함.

## 4. 11월 26일 Agent와 연결
- **Agent가 이 RAG 검색 Tool을 사용하기 전에 추가로 확인해야 할 것은 무엇인가?**
  1. **Reranker 기반 최상위 정렬 품질**: `Q07`처럼 `first_rank: 2`여도 `ndcg_at_3`가 낮을 수 있으므로, Agent가 컨텍스트 예산상 상위 1~3개 청크만 사용할 때 핵심 고등급 근거가 최상단에 배치되는지 확인할 것.
  2. **관련도 점수 임계치(Threshold) 설정**: `Q06` 같은 No-answer 질의에서 관련 없는 문서를 억지로 상위에 반환하지 않도록 검색 Tool의 최소 유사도/점수 컷오프가 설정되어 있는지 확인할 것.
  3. **코퍼스·등급 판정 버전 동기화**: 검색 인덱스 갱신 시 미판정 청크가 유입되어 평가가 중단되지 않도록 데이터셋·인덱스 버전 관리 체계를 확인할 것.