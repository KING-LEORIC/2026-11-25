# CLI 실행 인자 파싱 및 오프라인/실시간 모드 분기를 위한 표준 라이브러리 임포트
# - argparse : 실행 옵션 정의 및 상호 배타적 모드 검증
import argparse

# 상위 프로젝트 루트를 모듈 탐색 경로에 동적으로 추가하기 위한 임포트
# - sys : sys.path 조회 및 패키지 루트 경로 삽입
import sys

# OS 독립적인 파일 경로 계산 및 출력 파일 저장을 위한 임포트
# - Path : 실행 파일 기준 상대 경로 해석 및 결과/보고서 파일 쓰기
from pathlib import Path

# 실행 위치와 무관하게 app·coursekit 패키지를 임포트할 수 있도록 루트 경로 확보 및 중복 등록 방지
ROLE_ROOT = Path(__file__).resolve().parents[2]
if str(ROLE_ROOT) not in sys.path:
    sys.path.insert(0, str(ROLE_ROOT))

# Top-k 검색 Recall 및 고유 적중 수 계산 로직 임포트
# - calculate_recall : No-answer를 None으로 분리한 Recall@k 산출
# - count_gold_hits : 중복을 제거한 Top-k 내 Gold 적중 수 반환
from app.metrics.retrieval import calculate_recall, count_gold_hits

# Precision@k 및 Hit@k 규칙 산출 로직 임포트
# - precision_and_hit : 고정 분모 k 기준 Precision@k와 0/1 Hit@k 동시 계산
from app.metrics.rules import precision_and_hit

# 유효 질문 기준 Recall 평균 및 모수 요약 로직 임포트
# - summarize_valid_recall : None 제외 평균 Recall과 포함·제외 건수 집계
from app.reporting.aggregates import summarize_valid_recall

# 평가 결과 및 실패 메타데이터를 JSON 파일로 기록하는 유틸리티 임포트
# - write_json : 출력 디렉터리 보장 및 JSON 직렬화 저장
from coursekit.eval_report import write_json

# 실습 시나리오 오케스트레이션 및 훅 실행 엔진 임포트
# - execute : 정의된 hooks를 주입해 오프라인/라이브 평가 파이프라인 구동
from coursekit.eval_workshops import execute

"""
Day28 RAG 평가 실습 03(03_advanced) 실행 진입점 모듈.
CLI 모드를 해석해 검색 지표 산출·집계 훅을 평가 엔진에 주입하고, 결과·실패·보고서 파일을 생성하는 흐름.
"""


def main():
    """실행 모드를 파싱해 실습 3 평가 파이프라인을 구동하고 산출물을 저장하는 진입점 함수."""
    parser = argparse.ArgumentParser(description="Day28 RAG Evaluation 실습")
    # 오프라인 고정 데이터 실행과 과금·GPU가 수반되는 라이브 실행의 동시 지정을 막기 위한 상호 배타 그룹
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--offline", action="store_true", help="고정 학습 데이터만 실행(기본값)"
    )
    mode.add_argument(
        "--live",
        action="store_true",
        help="실제 CUDA GPU/DB/LLM 연결. 06~08만 지원하며 API 비용 발생 가능",
    )
    args = parser.parse_args()
    # 평가 엔진과 학생 구현 지표 함수를 느슨하게 결합하기 위한 콜백 훅 딕셔너리 구성
    hooks = {
        "calculate_recall": calculate_recall,
        "count_gold_hits": count_gold_hits,
        "precision_and_hit": precision_and_hit,
        "summarize_valid_recall": summarize_valid_recall,
    }
    # 평가 도중 예외 발생 시에도 민감 정보 없이 실패 이력을 남기고 상위 호출자에게 예외를 전파하기 위한 블록
    try:
        result = execute(3, hooks, live=args.live, level="03_advanced")
    except Exception as exc:
        # API 키·비밀번호·원본 Prompt 유출을 차단하기 위해 상태·단계·예외 클래스명 등 최소 메타데이터만 기록
        failure = {
            "status": "execution_failed",
            "exercise": 3,
            "stage": getattr(exc, "stage", "evaluation"),
            "error_type": type(exc).__name__,
            "mode": "live" if args.live else "offline_fixture",
        }
        write_json(
            Path(__file__).resolve().parent / "outputs" / "failure.json", failure
        )
        raise
    # 정상 완료 시 후속 검증 및 비교를 위해 결과 JSON을 outputs 디렉터리에 영속화
    output = Path(__file__).resolve().parent / "outputs" / "result.json"
    write_json(output, result)
    # 생성된 요약 보고서가 문자열로 존재할 때만 별도 Markdown 파일로 분리 저장해 불필요한 빈 파일 생성 방지
    if isinstance(result.get("markdown_report"), str):
        (output.parent / "report.md").write_text(
            result["markdown_report"], encoding="utf-8"
        )
    print("Day28 실습 3 · 03_advanced ·", result["mode"])
    print("출력:", output)
    return result


# 모듈 임포트 시 의도치 않은 평가 실행 및 API 과금을 방지하기 위한 진입점 가드
if __name__ == "__main__":
    main()


"""
설계 평가:
- 훅(hooks) 주입 패턴으로 검색 지표 산출 로직과 평가 실행 엔진을 분리해 독립적인 단위 검증이 가능한 구조.
- 예외 발생 시에도 비밀값 노출 없이 failure.json을 기록해 보안과 장애 추적성을 동시에 확보한 설계.
"""
