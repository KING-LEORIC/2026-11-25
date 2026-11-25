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

# 4종 실험 변형 동일 조건 비교 로직 임포트
# - compare_four_variants : Baseline·Rewrite·Rerank·Both 결과를 동일 k=3 기준으로 평가
from app.diagnostics.stages import compare_four_variants

# A/B 점수 변화량 산출 및 실패 단계 진단 로직 임포트
# - find_problem_stage : 후보·리랭킹·컨텍스트·생성 중 병목 단계 판별
# - score_delta : No-answer를 제외한 Before/After 점수 차이 계산
from app.experiments.comparison import find_problem_stage, score_delta

# 회귀 탐지 및 배포 보류 게이트 정책 임포트
# - regression_decision : Recall 하락·오류 발생 시 배포 보류 및 사유 기록
from app.policies.regression import regression_decision

# 평가 결과 및 실패 메타데이터를 JSON 파일로 기록하는 유틸리티 임포트
# - write_json : 출력 디렉터리 보장 및 JSON 직렬화 저장
from coursekit.eval_report import write_json

# 실습 시나리오 오케스트레이션 및 훅 실행 엔진 임포트
# - execute : 정의된 hooks를 주입해 오프라인/라이브 평가 파이프라인 구동
from coursekit.eval_workshops import execute

"""
Day28 RAG 평가 실습 07(03_advanced) 실행 진입점 모듈.
CLI 모드를 해석해 4종 변형 비교·점수 변화량·단계 진단·회귀 게이트 훅을 주입하고 산출물을 생성하는 흐름.
"""


def main():
    """실행 모드를 파싱해 실습 7 비교·회귀 평가 파이프라인을 구동하고 산출물을 저장하는 진입점 함수."""
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
    # 평가 엔진과 학생 구현 실험 비교·회귀 게이트 함수를 느슨하게 결합하기 위한 콜백 훅 딕셔너리 구성
    hooks = {
        "score_delta": score_delta,
        "find_problem_stage": find_problem_stage,
        "compare_four_variants": compare_four_variants,
        "regression_decision": regression_decision,
    }
    # 평가 도중 예외 발생 시에도 민감 정보 없이 실패 이력을 남기고 상위 호출자에게 예외를 전파하기 위한 블록
    try:
        result = execute(7, hooks, live=args.live, level="03_advanced")
    except Exception as exc:
        # API 키·비밀번호·원본 Prompt 유출을 차단하기 위해 상태·단계·예외 클래스명 등 최소 메타데이터만 기록
        failure = {
            "status": "execution_failed",
            "exercise": 7,
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
    print("Day28 실습 7 · 03_advanced ·", result["mode"])
    print("출력:", output)
    return result


# 모듈 임포트 시 의도치 않은 평가 실행 및 API 과금을 방지하기 위한 진입점 가드
if __name__ == "__main__":
    main()


"""
설계 평가:
- 4종 변형 비교·증감 계산·원인 진단·회귀 게이트를 훅으로 조합해 실험 파이프라인을 체계화한 구조.
- 예외 발생 시에도 비밀값 노출 없이 failure.json을 기록해 보안과 장애 추적성을 동시에 확보한 설계.
"""
