# 수행 기록 · Day28 실습 02

**실행한 모드:** `offline_fixture` (`level: 03_advanced`, `dataset_version: d28-eval-v1`)

**작성 TODO:** `select_gold`, `validate_gold_ids`, `label_no_answer`, `audit_gold`

## 1. 질문·입력
- **어떤 `question_id`를 사용했는가?**
  - `annotations`에 포함된 `Q01`, `Q05`, `Q06`, `Q07` 총 4개 질문을 사용함.
  - `target_example`로 확인된 입력 예시는 `Q01` (`question: "회의실 예약을 취소하는 방법은?"`, `category: "시설"`, `history: []`).
- **Gold Label을 Target 입력에 전달하지 않았는가?**
  - `target_example`에는 `question_id`, `question`, `category`, `history`만 포함될 뿐 `gold_chunk_ids`가 전혀 전달되지 않았음.
  - `select_gold` 역시 모델 검색 결과가 아니라 평가용 `gold[question_id]`에서만 정답 청크 ID를 읽어 Target 입력과 평가 레이블을 완전히 분리함.

## 2. 실제 확인한 출력
- **결과 JSON과 핵심 점수·출처 ID:**
  - 별도의 검색 Recall 수치 점수 대신 질문별 Gold 청크 ID 목록, 코퍼스 정합성(`valid_ids`), 정답 부재 여부(`no_answer`), 감사 메타데이터(`audit`: `gold_version: "d28-eval-v1"`, `frozen: true`, `review_status: "교육용 사전 검토 레이블"`)가 출력됨.
  - `Q01`: `gold_chunk_ids: ["FAC-102-C1"]`, `valid_ids: true`, `no_answer: false`
  - `Q05`: `gold_chunk_ids: ["ACA-101-C1"]`, `valid_ids: true`, `no_answer: false`
  - `Q06`: `gold_chunk_ids: []`, `valid_ids: true`, `no_answer: true`
  - `Q07`: `gold_chunk_ids: ["FAC-104-C1", "FAC-102-C1"]`, `valid_ids: true`, `no_answer: false`
- **No-answer / 실패 / 정상의 차이:**
  - **No-answer (`Q06`)**: `gold_chunk_ids`가 빈 리스트(`[]`)이고 `no_answer: true`로 분리된 상태. 코퍼스에 정답 근거가 없는 질문이므로 일반 검색 Recall 0점으로 평균내지 않고 별도 평가 대상으로 분리함(`valid_ids: true`).
  - **실패 (`valid_ids: false` 또는 `failure.json`)**: `validate_gold_ids`에서 중복 ID가 있거나 코퍼스에 존재하지 않는 ID가 발견되어 `valid_ids: false`가 되거나, 실행 중 예외로 `outputs/failure.json`이 생성되는 상태(이번 실행에서는 발생하지 않음).
  - **정상 (`Q01`, `Q05`, `Q07`)**: 중복 없이 코퍼스에 실존하는 Gold 청크 ID가 1개 이상 매핑되어 `valid_ids: true`, `no_answer: false`를 모두 충족한 상태.

## 3. 해설
- **왜 이 공식 또는 분기 조건이 필요한가?**
  - `select_gold`의 순서 보존 중복 제거(`dict.fromkeys`)와 `validate_gold_ids`의 중복·실존 여부 이중 검사는, 중복 ID나 코퍼스에 없는 유령 ID가 섞여 Recall 지표가 왜곡되는 것을 막기 위해 필요함.
  - `label_no_answer`의 `len(gold[question_id]) == 0` 분기는 정답이 없는 질문을 일반 질문과 합산해 Recall이 강제로 0점으로 떨어지는 왜곡을 방지하기 위함.
  - `audit_gold`의 `frozen: True`와 `review_status` 기록은 평가 결과에 맞춰 Gold 레이블을 사후 변조하는 데이터 오염을 막고 교육용 레이블의 적용 범위를 명확히 하기 위함.
- **평가 결과가 좋지 않다면 다음에 수정할 모듈은 어디인가?**
  - `valid_ids: false`가 나오면 **레이블 추출·검증 데이터(`app/datasets/labels.py` 또는 원천 Gold·코퍼스 청킹 ID 매핑)**를 수정해 중복 및 누락 ID를 정제해야 함.
  - No-answer 분리가 어긋나면 **`label_no_answer`(`app/datasets/validation.py`)** 또는 원천 데이터셋의 빈 레이블 정의를 점검함.
  - Gold 레이블 자체(`frozen: True`)는 평가 결과로 수정하지 않으며, 실제 검색 성능이 낮다면 리트리버의 **Query·Indexing·Candidate-k** 모듈을 개선함.

## 4. 11월 26일 Agent와 연결
- **Agent가 이 RAG 검색 Tool을 사용하기 전에 추가로 확인해야 할 것은 무엇인가?**
  1. **인덱스·코퍼스 ID 정합성 확인**: Agent가 호출하는 RAG 검색 Tool의 코퍼스 인덱스가 현재 평가 기준(`d28-eval-v1` 등)의 청크 ID 체계와 일치하는지 확인할 것.
  2. **No-answer 질의 대응 가드레일**: `Q06`처럼 코퍼스에 답이 없는 질문이 들어왔을 때 Agent가 임의로 관련 없는 청크를 인용하거나 환각 답변을 내지 않고 "근거 없음/답변 불가"를 반환하도록 분기 규칙을 확인할 것.
  3. **Target 입력 격리 확인**: 실제 실행 시 Agent가 `target_example`과 같은 사용자 질의(`question`, `category`, `history`)만 입력으로 받고, 평가용 `gold_chunk_ids`에 접근하지 않도록 Tool 인터페이스가 분리되어 있는지 확인할 것.
  4. **레이블 검증 수준 확인**: 현재 `review_status`가 `"교육용 사전 검토 레이블"`로 고정되어 있으므로, 실서비스 검증 단계에서는 도메인 전문가 검수를 거친 정식 버전의 평가 데이터셋을 사용하는지 확인할 것.