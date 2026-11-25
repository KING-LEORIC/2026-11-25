# 수행 기록 · Day28 실습 08

| 항목 | 확인된 값 |
| :--- | :--- |
| **실행 모드 / 변형** | `live` (`variant: both`, `level: 03_advanced`) |
| **데이터셋 버전** | `d28-eval-v1` (비용 제어로 상위 3개 문항 실행) |
| **작성 TODO** | `evaluate_one`, `summarize_all`, `write_summary_report`, `agent_release_gate` |
| **1차 Gate 판정** | `ready_for_agent_review: false` (정량 통과, 사람·접근제어 미완료) |

## 1. 질문·입력 및 데이터 계약
- **사용한 `question_id`**: `Q01`, `Q02`, `Q03` 총 3개 질문 (`live` 모드에서는 토큰 과금·실행 시간 제약을 위해 전체 질문 중 앞 3개만 평가함).
- **Gold Label 격리 여부**: `target_inputs(example)`로 `question_id`, `question`, `category`, `history`만 Target에 전달해 정답 유출을 차단했고, `gold`와 `grades`는 Target 외부의 `evaluate_one` 단계에서만 사후 결합함.

## 2. 실제 확인한 출력

### 질문별 평가 지표·출처·지연 시간 (`questions`)
| `question_id` | Recall@3 / RR / nDCG | Precision@3 | `included_ids` (Top-5 `ranked_ids` 중) | 상태 / 출처 유효성 | 총 지연 (`rerank` / `rewrite` / `generation`) |
| :--- | :---: | :---: | :--- | :--- | :--- |
| **Q01** | `1.0` / `1.0` / `1.0` | `0.3333` | `FAC-102-C1`, `FAC-109-C1` | `answered` / `true` | `16,343.5ms` (`5,608.6` / `1,548.5` / `1,586.4`) |
| **Q02** | `1.0` / `1.0` / `1.0` | `0.3333` | `FAC-102-C1`, `FAC-109-C1` | `answered` / `true` | `3,649.5ms` (`204.1` / `1,568.5` / `1,607.6`) |
| **Q03** | `1.0` / `1.0` / `1.0` | `0.3333` | `FAC-102-C1`, `FAC-109-C1` | `answered` / `true` | `3,657.5ms` (`105.0` / `2,043.0` / `1,382.4`) |

### 전체 요약 (`summary`) 및 상태 구분
- **집계 결과**: `mean_recall_at_k: 1.0`, `mean_precision_at_k: 0.3333`, `mrr_at_k: 1.0`, `mean_ndcg_at_k: 1.0` (`evaluated_questions: 3`, `source_integrity_failures: 0`, `status_failures: 0`).
- **No-answer / 실패 / 정상의 차이**:
  - **No-answer**: `no_answer_excluded: 0`, `insufficient_context: 0`으로 이번 3문항에는 정답 부재 질문이 포함되지 않음(포함 시 평균 Recall에서 제외되고 `correct_abstention` 여부로 별도 집계됨).
  - **실패**: `sources_valid: false` 또는 `status`가 `answered`/`insufficient_context` 외 값일 때 `source_integrity_failures`·`status_failures`로 집계되며, `evaluate_one`에서 Trace 필수 필드 누락 시 `ValueError`로 차단됨(이번 실행 0건).
  - **정상**: 3문항 모두 `status: "answered"`, `sources_valid: true`이며 1순위 출처(`FAC-102-C1`) 적중과 근거 기반 답변 생성을 달성함.

### 1차 Agent Release Gate (`agent_gate`) 및 보고서 (`report.md`)
| 검사 항목 (`checks`) | 결과 | 세부 근거 / 기준 |
| :--- | :---: | :--- |
| `retrieval_recall` | **통과 (`true`)** | `mean_recall_at_k: 1.0` (기준 `>= 0.70`) |
| `retrieval_mrr` | **통과 (`true`)** | `mrr_at_k: 1.0` (기준 `>= 0.60`) |
| `source_integrity` | **통과 (`true`)** | `source_integrity_failures: 0` |
| `execution_status` | **통과 (`true`)** | `status_failures: 0` |
| `human_review` | **미통과 (`false`)** | 사람 검수 플래그 미승인 (`False` 전달) |
| `access_control_tests` | **미통과 (`false`)** | 접근 제어 테스트 미승인 (`False` 전달) |

- `outputs/report.md`에는 `Quality decision: 사람 검토 후 추가 판단`이 기록되었으며, 정량·무결성 지표는 모두 통과했지만 `human_review`와 `access_control_tests`가 `false`이므로 최종 `ready_for_agent_review`는 `false`로 보류됨.

## 3. 해설
- **왜 이 공식·분기 조건이 필요한가?**
  - `evaluate_one`(`evaluate_record`)은 Trace 필수 필드가 빠졌을 때 빈 리스트로 메우지 않고 예외를 발생시켜 불완전 로그가 정상 점수로 위장되는 것을 막음.
  - `summarize_all`(`report_summary`)은 서로 다른 `mode`·`data_version`·`variant` 혼합을 차단하고 No-answer를 평균에서 분리해 지표 왜곡을 방지함.
  - `write_summary_report`는 평균 점수만 단독 제출하지 않고 출처 실패 건수와 조건부 판단 문구(`사람 검토 후 추가 판단`)를 병기하며, `agent_release_gate`는 검색 점수가 `1.0`이어도 사람 검수·접근 제어가 통과되지 않으면 Agent 연결을 보류하도록 강제함.
- **결과가 좋지 않거나 추가 개선 시 수정할 모듈은 어디인가?**
  - 이번 `live` 실행에서는 검색·정확도 지표가 모두 `1.0`이지만, `Q01`의 초기 `rerank` 지연(`5.6초`)과 전 문항 `rewrite` 지연(`1.5~2.0초`)이 전체 응답 시간의 큰 비중을 차지하므로 속도 개선 시 **Reranker 웜업·Query Rewrite 최적화**를 우선 검토함.
  - 또한 `agent_gate` 통과를 위해서는 평가 코드 수정이 아니라 **사람 검수(`human_review`)와 접근 제어 테스트(`access_control_tests`) 수행**이 선행되어야 함.

## 4. 11월 26일 Agent와 연결
- **Agent가 이 RAG 검색 Tool을 사용하기 전에 추가로 확인해야 할 사항:**
  1. **미통과 보안·검수 게이트 해소 (`human_review`, `access_control_tests`)**: `ready_for_agent_review`가 `false`인 상태이므로 비공개(`non-public`)·구버전 문서 차단 접근 제어 테스트와 사람 답변 검수를 완료한 뒤 연결할 것.
  2. **전체 질문셋(No-answer 포함) 검증 확대**: 이번 `live` 결과는 `Q01`~`Q03`(모두 `answerable`)만 평가했으므로, `Q06` 같은 No-answer 질의에서도 Tool과 Agent가 추측 없이 안전하게 거절(`insufficient_context`)하는지 확인할 것.
  3. **초기 Cold-start 지연 대비 및 권한 승인**: `Q01`에서 `16.3초`가 소요된 만큼 Agent의 Tool Timeout 설정과 사전 모델 웜업을 확인하고, `agent_gate.scope`에 명시된 대로 Tool 권한·안전성·운영 배포 승인을 별도로 완료할 것.
