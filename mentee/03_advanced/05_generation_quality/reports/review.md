# 수행 기록 · Day28 실습 05

**실행한 모드:** `offline_fixture` (`level: 03_advanced`, `dataset_version: d28-eval-v1`)

**작성 TODO:** `claim_faithfulness`, `describe_claim_result`, `label_answer_quality`, `prepare_human_review`

## 1. 질문·입력
- **어떤 `question_id`를 사용했는가?**
  - `outputs/result.json`에는 별도의 `question_id` 대신 `generation_reviews`의 `case_id`인 `G01`, `G02`, `G03`, `G04` 총 4개 생성 평가 케이스가 사용됨.
- **Gold Label을 Target 입력에 전달하지 않았는가?**
  - 모델의 생성 입력(Target)에는 정답 레이블이 전달되지 않았으며, `claim_faithfulness`와 `describe_claim_result` 역시 Reference Answer(정답지)가 아니라 제공된 Context 대비 Claim의 `supported` 여부(`label_source: "human_fixture"`)만 검증함.

## 2. 실제 확인한 출력
- **결과 JSON과 핵심 점수·출처 ID:**
  - 별도 문서 출처 ID는 출력되지 않았고, 4개 케이스 모두 `label_source: "human_fixture"`, `human_review.judge: "human_fixture"`, `reviewer: "교육용 검수자"`, `disagreement: "추가 사람 검토 필요"`, `publishable: false`로 기록됨.
  - **`G01`**: `faithfulness: 0.6666...`, `reason: "근거 불충분: 벌금이 5만원"`, `answer_relevance: "높음"`, `answer_correctness: "부분정답"`
  - **`G02`**: `faithfulness: 0.0`, `reason: "근거 불충분: 내일 오후 6시 마감"`, `answer_relevance: "높음"`, `answer_correctness: "오답"`
  - **`G03`**: `faithfulness: 1.0`, `reason: "모든 Claim이 제공된 Context와 일치"`, `answer_relevance: "낮음"`, `answer_correctness: "오답"`
  - **`G04`**: `faithfulness: null`, `reason: "검토할 Claim 없음: 별도 판정 필요"`, `answer_relevance: "높음"`, `answer_correctness: "정답"`
- **No-answer / 실패 / 정상의 차이:**
  - **검토할 Claim 없음 (`G04`, `faithfulness: null`)**: Claim 목록이 비어 있어 `faithfulness`를 `0.0`이나 `1.0`으로 단정하지 않고 `null` 및 `"검토할 Claim 없음: 별도 판정 필요"`로 분리한 상태(`answer_relevance: "높음"`, `answer_correctness: "정답"`).
  - **실패 (`G01`, `G02`, `G03`)**: `G01`·`G02`는 근거에 없는 주장(`벌금이 5만원`, `내일 오후 6시 마감`)이 포함되어 `faithfulness`가 낮게 나온 **근거 불충분(환각) 실패**이고, `G03`은 `faithfulness: 1.0`으로 Context와 일치하지만 질문에 답하지 못해 `answer_relevance: "낮음"`, `answer_correctness: "오답"`으로 판정된 **질문 부적합 실패**임(허용 루브릭 외 값 입력 시 `ValueError`가 발생하나 이번 실행에서는 예외 없음).
  - **정상 및 배포 보류 (`human_review`)**: 근거 충실도와 질문 적합성·정답성이 모두 충족되어야 정상 답변으로 볼 수 있으며, 본 실행에서는 교육용 사람 검수 픽스처이므로 전 케이스가 `publishable: false`로 자동 배포가 보류됨.

## 3. 해설
- **왜 이 공식 또는 분기 조건이 필요한가?**
  - `claim_faithfulness`와 `describe_claim_result`의 `if not claims:` 분기는 검토할 Claim이 없는 사례(`G04`)를 `"모든 Claim 지원(1.0)"`이나 `"완전 실패(0.0)"`로 오판하지 않고 별도 판정으로 분리하기 위해 필요함.
  - `label_answer_quality`에서 `answer_relevance`와 `answer_correctness`를 분리하고 루브릭을 검증하는 이유는, `G03`처럼 Context와 일치해 Faithfulness가 `1.0`이어도 질문 의도에 맞지 않으면(`낮음`/`오답`) 올바른 답변이 아니기 때문임.
  - `prepare_human_review`의 `judge: "human_fixture"`와 `publishable: false` 고정은 자동 평가 점수만으로 규정·의료·금융 등 민감 답변을 임의 확정·배포하는 것을 막기 위한 안전장치임.
- **평가 결과가 좋지 않다면 다음에 수정할 모듈은 어디인가?**
  - `G01`·`G02`처럼 `faithfulness`가 낮고 미지원 Claim이 발생하면 **생성 Prompt(근거 외 추측 금지 지시)·출처 검증·답변 후처리 가드레일** 모듈을 수정해야 함.
  - `G03`처럼 `faithfulness: 1.0`인데 `answer_relevance`가 낮다면 **Retriever/Reranker의 질문 의도 정합성 및 질문 반영 Prompt**를 점검해야 함.
  - `G04`처럼 Claim이 비어 있다면 **Claim 분해기(Claim Extractor) 또는 단답형 응답 평가 규칙**을 보완해야 함.

## 4. 11월 26일 Agent와 연결
- **Agent가 이 RAG 검색 Tool을 사용하기 전에 추가로 확인해야 할 것은 무엇인가?**
  1. **근거 외 수치·기한 생성 차단**: Agent가 검색 Tool에서 받은 Context에 없는 내용(`G01`의 "벌금이 5만원", `G02`의 "내일 오후 6시 마감")을 임의로 지어내지 않도록 생성 프롬프트와 출처 대조 검증이 적용되어 있는지 확인할 것.
  2. **질문 의도 적합성 재검증 (`G03` 교훈)**: 검색된 문서와 일치하더라도 사용자의 원래 질문에 답이 되지 않으면 의미가 없으므로, Agent가 Context를 읽은 뒤 질문 적합성이 낮을 때 쿼리를 재작성해 재검색하는지 확인할 것.
  3. **고위험 도메인 자동 확정 제한 (`publishable: false`)**: 규정·의료·금융 등 오류가 치명적인 질의에서는 Agent가 단독 확정 답변을 내보내지 않고 출처 제시 및 사람 검토 에스컬레이션 정책을 따르는지 확인할 것.