# 수행 기록 · Day28 실습 01

**실행한 모드:** `offline_fixture` (`level: 03_advanced`, `dataset_version: d28-eval-v1`)

**작성 TODO:** `classify_case`, `describe_evidence`, `recommend_fix`, `audit_decision`

## 1. 질문·입력
- **어떤 `question_id`를 사용했는가?**
  - `outputs/result.json`에는 별도의 `question_id` 대신 `d28-eval-v1` 오프라인 픽스처의 `case_id`인 `F01`, `F02`, `F03`, `F04`, `F05`(총 5개 케이스)가 식별자로 기록됨.
- **Gold Label을 Target 입력에 전달하지 않았는가?**
  - `classify_case`는 모델 생성 입력(Target)이 아니라 사후 평가용 불리언 플래그(`system_error`, `candidate_has_gold`, `context_has_gold`, `answer_grounded`)만 참조하며, `audit_decision` 역시 `case_id`, `stage`, `evidence`, `recorded`, `safe_message`만 남겨 원본 Prompt나 정답·비밀값이 출력에 노출되지 않도록 분리함.

## 2. 실제 확인한 출력
- **결과 JSON과 핵심 점수·출처 ID:**
  - 별도의 수치 점수나 원문 출처 문서 ID 대신 케이스별 `stage`, `evidence`, `recommendation`, `audit` 구조가 출력되었고, 5개 케이스 모두 `audit.recorded: true`, `audit.safe_message: "문제 단계 확인 완료"`로 기록됨.
  - `F01` (`candidate_miss`): Gold 문서 ID가 최초 검색 후보에 존재하지 않음 → `Query·Metadata Filter·Indexing·Candidate-k 점검`
  - `F02` (`ranking_or_context_miss`): Gold는 후보에 있으나 LLM Context에 포함되지 않음 → `Reranker·Context Top-N·길이 예산 점검`
  - `F03` (`generation_failure`): 근거가 Context에 있는데 답변 주장이 지지되지 않음 → `Prompt·근거 주장·출처 검증 점검`
  - `F04` (`system_failure`): 서비스 실행이 실패해 지표를 계산할 수 없음 → `GPU/DB/API 연결·Timeout을 먼저 진단`
  - `F05` (`passed`): 검색 후보·Context·답변 검토 조건 충족 → `검증 결과 기록 후 유지`
- **No-answer / 실패 / 정상의 차이:**
  - **시스템 실패 (`F04: system_failure`)**: GPU/DB/API 연결·Timeout 등 인프라 실행 자체가 실패해 평가 지표를 계산할 수 없는 상태.
  - **단계별 검색·생성 실패 (`F01`~`F03`)**: 실행은 정상 완료되었으나 `초기 후보 누락(F01)` → `리랭킹/컨텍스트 누락(F02)` → `근거 기반 답변 생성 실패(F03)` 중 어느 구간에서 오류가 발생했는지 분리된 상태(근거 누락 시 잘못된 답변이나 No-answer로 이어짐).
  - **정상 (`F05: passed`)**: 검색 후보, LLM Context, 답변 근거 검증 조건을 모두 충족한 상태.

## 3. 해설
- **왜 이 공식 또는 분기 조건이 필요한가?**
  - `classify_case`는 `system_error` → `candidate_has_gold` → `context_has_gold` → `answer_grounded` 순의 Early Return 분기를 사용함. 인프라 장애를 검색 품질 문제로 오분류하거나, 최초 후보(`candidate_has_gold`)에 없는 문서를 Reranker·Prompt 수정으로 해결하려는 헛수고를 막고 실패 원인을 선행 단계부터 정확히 격리하기 위함.
- **평가 결과가 좋지 않다면 다음에 수정할 모듈은 어디인가?**
  - `recommend_fix` 기준에 따라 실패한 stage에 해당하는 모듈을 우선 수정함: `system_failure`는 GPU/DB/API 연결·Timeout, `candidate_miss`는 Query·Metadata Filter·Indexing·Candidate-k, `ranking_or_context_miss`는 Reranker·Context Top-N·길이 예산, `generation_failure`는 Prompt·근거 주장·출처 검증 로직을 점검함.

## 4. 11월 26일 Agent와 연결
- **Agent가 이 RAG 검색 Tool을 사용하기 전에 추가로 확인해야 할 것은 무엇인가?**
  1. **인프라·연결 상태 확인**: GPU/DB/API 연결 및 Timeout 임계치가 정상인지 확인해 `system_failure` 시 재시도·Fallback 경로를 확보할 것.
  2. **검색 파라미터·스키마 정합성 확인**: Agent가 생성하는 Query 형식, Metadata Filter 키, `Candidate-k`, `Context Top-N`, 토큰 길이 예산이 인덱스 및 LLM 컨텍스트 한도와 맞는지 확인할 것.
  3. **감사 로그·보안 마스킹 확인**: Tool 호출 및 예외 로그에 원본 Prompt, API Key, Password 등이 기록되지 않고 `audit_decision`처럼 안전한 식별자와 `stage`만 남는지 확인할 것.
  4. **근거 부족 시 행동 규칙 설정**: 검색 결과가 비어 있거나(`candidate_miss`) 컨텍스트 근거가 불충분할 때 Agent가 임의로 추측 답변을 생성하지 않도록 Query 재작성(재검색) 또는 보류 응답 가드레일을 둘 것.