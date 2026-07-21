from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


# ============================================================
# 0. AI 모듈 import
#
# 권장 실행:
#   프로젝트 루트에서 python -m ai.run_pipeline
#
# 직접 실행:
#   python ai/run_pipeline.py
#
# 두 실행 방식 모두 지원한다.
# ============================================================

try:
    # 패키지 방식: from ai.run_pipeline import analyze_message
    from .classifier import predict_proba
    from .src.text_features import preprocess_for_model

except ImportError:
    # 직접 실행 방식: python ai/run_pipeline.py
    from classifier import predict_proba
    from src.text_features import preprocess_for_model


# ============================================================
# 1. 경로 설정
# ============================================================

# 현재 파일 위치:
# is-this-phishing-ai/ai/run_pipeline.py
#
# 따라서 PROJECT_ROOT는 ai 폴더를 의미한다.
PROJECT_ROOT = Path(__file__).resolve().parent

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODEL_DIR = PROJECT_ROOT / "models"
RESULT_DIR = PROJECT_ROOT / "results"

DATA_PATH = RAW_DIR / "korean_message_dataset.csv"
CLEAN_DATA_PATH = PROCESSED_DIR / "clean_message_dataset.csv"
CONFLICT_PATH = PROCESSED_DIR / "label_conflict_rows.csv"

for directory in [
    RAW_DIR,
    PROCESSED_DIR,
    MODEL_DIR,
    RESULT_DIR,
]:
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )


# ============================================================
# 2. 실시간 문자 분석 설정
#
# 현재는 KcELECTRA 문자 모델만 사용한다.
# fusion.pkl 완성 후 final_probability 계산 부분만 교체하면 된다.
#
# 아래 임계값은 연동 테스트용 임시값이다.
# 최종 임계값은 validation/test PR curve로 확정해야 한다.
# ============================================================

SUSPICIOUS_THRESHOLD = 0.5
HIGH_RISK_THRESHOLD = 0.8

ANALYSIS_VERSION = "kcelectra-text-only-v1"


# ============================================================
# 3. 백엔드 연동용 단일 문자 분석
# ============================================================

def analyze_message(text: str) -> dict[str, Any]:
    """
    문자 원문 1건을 전처리하고 KcELECTRA로 분석한다.

    처리 흐름:
        원문
        -> preprocess_for_model()
        -> classifier.predict_proba()
        -> 피싱 확률 및 위험 단계 반환

    Parameters
    ----------
    text:
        사용자가 입력하거나 프론트엔드에서 전달한 문자 원문.

    Returns
    -------
    dict:
        백엔드 API가 그대로 JSON으로 반환할 수 있는 분석 결과.

    Raises
    ------
    ValueError:
        입력 문자가 비어 있을 때 발생한다.
    """

    if text is None:
        raise ValueError(
            "분석할 문자 내용이 비어 있습니다."
        )

    original_text = str(text).strip()

    if not original_text:
        raise ValueError(
            "분석할 문자 내용이 비어 있습니다."
        )

    # 학습 시 사용한 것과 동일한 전처리 함수 사용
    processed_text = preprocess_for_model(
        original_text
    )

    if not processed_text:
        raise ValueError(
            "문자 전처리 결과가 비어 있습니다."
        )

    # KcELECTRA가 반환하는 피싱 확률
    model_probability = float(
        predict_proba(processed_text)
    )

    # 혹시 모를 범위 오류 방지
    model_probability = max(
        0.0,
        min(model_probability, 1.0),
    )

    # 현재 메타 분류기가 없으므로
    # 최종 확률은 문자 모델 확률과 동일하게 사용한다.
    final_probability = model_probability

    if final_probability >= HIGH_RISK_THRESHOLD:
        label = "phishing"
        risk_level = "high"

    elif final_probability >= SUSPICIOUS_THRESHOLD:
        label = "suspicious"
        risk_level = "medium"

    else:
        label = "normal"
        risk_level = "low"

    return {
        "original_text": original_text,
        "processed_text": processed_text,

        # 현재 실제 KcELECTRA 문자 모델 확률
        "model_probability": round(
            model_probability,
            4,
        ),

        # 추후 fusion 모델 적용 시 이 값만 교체
        "final_probability": round(
            final_probability,
            4,
        ),

        "label": label,
        "risk_level": risk_level,

        # 현재 어떤 분석 방식으로 결과가 나온 것인지 구분
        "analysis_version": ANALYSIS_VERSION,

        # 메타 분류기가 아직 없다는 것을 명시
        "fusion_applied": False,
    }


# ============================================================
# 4. CSV 안전하게 읽기
# ============================================================

def read_csv_safely(
    path: Path,
) -> pd.DataFrame:
    """
    여러 인코딩을 순서대로 시도하여 CSV를 읽는다.
    """

    if not path.exists():
        raise FileNotFoundError(
            "파일을 찾을 수 없습니다.\n"
            f"확인 경로: {path}"
        )

    encodings = [
        "utf-8-sig",
        "utf-8",
        "cp949",
        "euc-kr",
    ]

    last_error: Exception | None = None

    for encoding in encodings:
        try:
            df = pd.read_csv(
                path,
                encoding=encoding,
            )

            print(
                f"CSV 인코딩: {encoding}"
            )

            return df

        except UnicodeDecodeError as error:
            last_error = error

    raise RuntimeError(
        f"CSV 인코딩을 판별하지 못했습니다: {path}"
    ) from last_error


# ============================================================
# 5. 실제 데이터 전처리
# ============================================================

def prepare_real_data(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    원본 Korean_message 데이터셋을 정리하고
    모델 학습용 전처리 텍스트를 생성한다.
    """

    required_columns = {
        "content",
        "class",
    }

    missing_columns = (
        required_columns
        - set(df.columns)
    )

    if missing_columns:
        raise ValueError(
            f"필수 컬럼이 없습니다: {sorted(missing_columns)}\n"
            f"현재 컬럼: {df.columns.tolist()}"
        )

    work_df = df.copy()

    print("\n[원본 데이터]")
    print("shape:", work_df.shape)
    print(
        "columns:",
        work_df.columns.tolist(),
    )

    print("\n원본 class 분포")
    print(
        work_df["class"]
        .value_counts(dropna=False)
    )

    # 원본 라벨
    # class 1: 정상 일반 문자
    # class 2: 피싱 문자
    # class 3: 정상 기관·택배 문자
    label_map = {
        1: 0,
        2: 1,
        3: 0,
    }

    work_df["label"] = (
        work_df["class"]
        .map(label_map)
    )

    invalid_count = int(
        work_df["label"]
        .isna()
        .sum()
    )

    if invalid_count > 0:
        print(
            f"\n매핑되지 않은 class 행 "
            f"{invalid_count:,}개 제거"
        )

        print(
            work_df.loc[
                work_df["label"].isna(),
                "class",
            ].value_counts(
                dropna=False
            )
        )

    work_df = work_df.dropna(
        subset=[
            "content",
            "label",
        ]
    ).copy()

    work_df["content"] = (
        work_df["content"]
        .astype(str)
        .str.strip()
    )

    work_df = work_df[
        work_df["content"].ne("")
    ].copy()

    work_df["label"] = (
        work_df["label"]
        .astype(int)
    )

    # ========================================================
    # 동일 문장 라벨 충돌 검사
    # ========================================================

    label_counts = (
        work_df.groupby("content")["label"]
        .nunique()
    )

    conflict_texts = label_counts[
        label_counts > 1
    ].index

    conflict_df = (
        work_df[
            work_df["content"]
            .isin(conflict_texts)
        ]
        .sort_values(
            [
                "content",
                "label",
            ]
        )
    )

    print(
        "\n동일 문장 라벨 충돌 수:",
        len(conflict_texts),
    )

    if len(conflict_texts) > 0:
        conflict_df.to_csv(
            CONFLICT_PATH,
            index=False,
            encoding="utf-8-sig",
        )

        print(
            "라벨 충돌 행 저장:",
            CONFLICT_PATH,
        )

        # 동일 문장에 정상/피싱이 동시에 붙은 경우 제거
        work_df = work_df[
            ~work_df["content"]
            .isin(conflict_texts)
        ].copy()

    # ========================================================
    # 동일 문장 중복 제거
    # ========================================================

    before_duplicates = len(work_df)

    work_df = (
        work_df
        .drop_duplicates(
            subset=["content"]
        )
        .reset_index(drop=True)
    )

    removed_duplicates = (
        before_duplicates
        - len(work_df)
    )

    # 중복 제거 후 row_id 새로 생성
    work_df.insert(
        loc=0,
        column="row_id",
        value=range(len(work_df)),
    )

    print(
        f"\n완전중복 제거 수: "
        f"{removed_duplicates:,}"
    )

    # ========================================================
    # 모델 입력 전처리
    #
    # 실시간 서빙에서도 동일한 preprocess_for_model 사용
    # ========================================================

    print(
        "\n모델 입력 전처리 시작"
    )

    work_df["text"] = (
        work_df["content"]
        .map(preprocess_for_model)
    )

    # 전처리 결과가 비어 있는 행 제거
    empty_processed_mask = (
        work_df["text"]
        .astype(str)
        .str.strip()
        .eq("")
    )

    empty_processed_count = int(
        empty_processed_mask.sum()
    )

    if empty_processed_count > 0:
        print(
            "전처리 결과가 비어 있는 행 제거:",
            empty_processed_count,
        )

        work_df = work_df[
            ~empty_processed_mask
        ].copy()

    # ========================================================
    # URL·전화번호 신호 컬럼
    # ========================================================

    work_df["has_official_url"] = (
        work_df["text"]
        .str.contains(
            r"\[URL_OFFICIAL\]",
            regex=True,
            na=False,
        )
        .astype(int)
    )

    work_df["has_shortener_url"] = (
        work_df["text"]
        .str.contains(
            r"\[URL_SHORTENER\]",
            regex=True,
            na=False,
        )
        .astype(int)
    )

    work_df["has_suspicious_url"] = (
        work_df["text"]
        .str.contains(
            r"\[URL_SUSPICIOUS\]",
            regex=True,
            na=False,
        )
        .astype(int)
    )

    work_df["has_foreign_phone"] = (
        work_df["text"]
        .str.contains(
            r"\[PHONE_FOREIGN\]",
            regex=True,
            na=False,
        )
        .astype(int)
    )

    work_df["has_official_phone"] = (
        work_df["text"]
        .str.contains(
            r"\[PHONE_OFFICIAL\]",
            regex=True,
            na=False,
        )
        .astype(int)
    )

    work_df["has_mobile_phone"] = (
        work_df["text"]
        .str.contains(
            r"\[PHONE_MOBILE\]",
            regex=True,
            na=False,
        )
        .astype(int)
    )

    work_df = work_df.reset_index(
        drop=True
    )

    print("\n[정리 완료]")
    print("shape:", work_df.shape)

    print("\n최종 label 분포")
    print(
        work_df["label"]
        .value_counts()
        .sort_index()
    )

    return work_df


# ============================================================
# 6. 특징 요약 출력
# ============================================================

def print_feature_summary(
    df: pd.DataFrame,
) -> None:
    """
    정상/피싱 라벨별 URL 및 전화번호 토큰 분포를 출력한다.
    """

    feature_columns = [
        "has_official_url",
        "has_shortener_url",
        "has_suspicious_url",
        "has_foreign_phone",
        "has_official_phone",
        "has_mobile_phone",
    ]

    summary = (
        df.groupby("label")[
            feature_columns
        ]
        .agg(
            [
                "sum",
                "mean",
            ]
        )
        .round(4)
    )

    print(
        "\n[라벨별 URL·전화번호 특징]"
    )
    print(summary)

    print(
        "\n[정상 문자 전처리 예시]"
    )

    normal_samples = df.loc[
        df["label"].eq(0),
        [
            "content",
            "text",
        ],
    ].head(5)

    for _, row in normal_samples.iterrows():
        print("-" * 80)
        print(
            "원문:",
            row["content"],
        )
        print(
            "전처리:",
            row["text"],
        )

    print(
        "\n[피싱 문자 전처리 예시]"
    )

    phishing_samples = df.loc[
        df["label"].eq(1),
        [
            "content",
            "text",
        ],
    ].head(5)

    for _, row in phishing_samples.iterrows():
        print("-" * 80)
        print(
            "원문:",
            row["content"],
        )
        print(
            "전처리:",
            row["text"],
        )


# ============================================================
# 7. 전체 데이터 전처리 실행
# ============================================================

def main() -> None:
    """
    전체 CSV 데이터셋을 전처리하여 저장한다.

    이 함수는 학습 데이터 생성용이다.
    실시간 백엔드 요청은 analyze_message()를 사용한다.
    """

    print("=" * 80)
    print(
        "피싱 문자 데이터 전처리 시작"
    )
    print("=" * 80)

    print(
        "프로젝트 경로:",
        PROJECT_ROOT,
    )
    print(
        "원본 데이터:",
        DATA_PATH,
    )
    print(
        "저장 경로:",
        CLEAN_DATA_PATH,
    )

    raw_df = read_csv_safely(
        DATA_PATH
    )

    clean_df = prepare_real_data(
        raw_df
    )

    print_feature_summary(
        clean_df
    )

    clean_df.to_csv(
        CLEAN_DATA_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    print(
        "\n" + "=" * 80
    )
    print(
        "전처리 저장 완료"
    )
    print(
        CLEAN_DATA_PATH
    )
    print("=" * 80)


# ============================================================
# 8. 직접 실행
# ============================================================

if __name__ == "__main__":
    main()