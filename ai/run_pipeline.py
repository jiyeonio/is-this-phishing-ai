from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.text_features import preprocess_for_model


# ============================================================
# 1. 경로 설정
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODEL_DIR = PROJECT_ROOT / "models"
RESULT_DIR = PROJECT_ROOT / "results"

DATA_PATH = RAW_DIR / "korean_message_dataset.csv"
CLEAN_DATA_PATH = PROCESSED_DIR / "clean_message_dataset.csv"
CONFLICT_PATH = PROCESSED_DIR / "label_conflict_rows.csv"

for directory in [RAW_DIR, PROCESSED_DIR, MODEL_DIR, RESULT_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


# ============================================================
# 2. CSV 안전하게 읽기
# ============================================================

def read_csv_safely(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"파일을 찾을 수 없습니다.\n"
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
            df = pd.read_csv(path, encoding=encoding)
            print(f"CSV 인코딩: {encoding}")
            return df

        except UnicodeDecodeError as error:
            last_error = error

    raise RuntimeError(
        f"CSV 인코딩을 판별하지 못했습니다: {path}"
    ) from last_error


# ============================================================
# 3. 실제 데이터 전처리
# ============================================================

def prepare_real_data(df: pd.DataFrame) -> pd.DataFrame:
    required_columns = {"content", "class"}
    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"필수 컬럼이 없습니다: {sorted(missing_columns)}\n"
            f"현재 컬럼: {df.columns.tolist()}"
        )

    work_df = df.copy()

    print("\n[원본 데이터]")
    print("shape:", work_df.shape)
    print("columns:", work_df.columns.tolist())

    print("\n원본 class 분포")
    print(work_df["class"].value_counts(dropna=False))

    # 원본 라벨
    # class 1: 정상 일반 문자
    # class 2: 피싱 문자
    # class 3: 정상 기관·택배 문자
    label_map = {
        1: 0,
        2: 1,
        3: 0,
    }

    work_df["label"] = work_df["class"].map(label_map)

    invalid_count = int(work_df["label"].isna().sum())

    if invalid_count > 0:
        print(f"\n매핑되지 않은 class 행 {invalid_count:,}개 제거")

        print(
            work_df.loc[
                work_df["label"].isna(),
                "class",
            ].value_counts(dropna=False)
        )

    work_df = work_df.dropna(
        subset=["content", "label"]
    ).copy()

    work_df["content"] = (
        work_df["content"]
        .astype(str)
        .str.strip()
    )

    work_df = work_df[
        work_df["content"].ne("")
    ].copy()

    work_df["label"] = work_df["label"].astype(int)

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

    conflict_df = work_df[
        work_df["content"].isin(conflict_texts)
    ].sort_values(["content", "label"])

    print("\n동일 문장 라벨 충돌 수:", len(conflict_texts))

    if len(conflict_texts) > 0:
        conflict_df.to_csv(
            CONFLICT_PATH,
            index=False,
            encoding="utf-8-sig",
        )

        print("라벨 충돌 행 저장:", CONFLICT_PATH)

        # 동일 문장에 정상/피싱이 동시에 붙은 경우 제거
        work_df = work_df[
            ~work_df["content"].isin(conflict_texts)
        ].copy()

    # ========================================================
    # 동일 문장 중복 제거
    # ========================================================

    before_duplicates = len(work_df)

    work_df = (
        work_df
        .drop_duplicates(subset=["content"])
        .reset_index(drop=True)
    )

    removed_duplicates = before_duplicates - len(work_df)

    # 중복 제거 후 row_id 새로 생성
    work_df.insert(
        loc=0,
        column="row_id",
        value=range(len(work_df)),
    )

    print(f"\n완전중복 제거 수: {removed_duplicates:,}")

    # ========================================================
    # 모델 입력 전처리
    # ========================================================

    print("\n모델 입력 전처리 시작")

    work_df["text"] = work_df["content"].map(
        preprocess_for_model
    )

    # URL/전화번호 신호 컬럼
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

    print("\n[정리 완료]")
    print("shape:", work_df.shape)

    print("\n최종 label 분포")
    print(work_df["label"].value_counts())

    return work_df


# ============================================================
# 4. 특징 요약 출력
# ============================================================

def print_feature_summary(df: pd.DataFrame) -> None:
    feature_columns = [
        "has_official_url",
        "has_shortener_url",
        "has_suspicious_url",
        "has_foreign_phone",
        "has_official_phone",
        "has_mobile_phone",
    ]

    summary = (
        df.groupby("label")[feature_columns]
        .agg(["sum", "mean"])
        .round(4)
    )

    print("\n[라벨별 URL·전화번호 특징]")
    print(summary)

    print("\n[정상 문자 전처리 예시]")

    normal_samples = df.loc[
        df["label"].eq(0),
        ["content", "text"],
    ].head(5)

    for _, row in normal_samples.iterrows():
        print("-" * 80)
        print("원문:", row["content"])
        print("전처리:", row["text"])

    print("\n[피싱 문자 전처리 예시]")

    phishing_samples = df.loc[
        df["label"].eq(1),
        ["content", "text"],
    ].head(5)

    for _, row in phishing_samples.iterrows():
        print("-" * 80)
        print("원문:", row["content"])
        print("전처리:", row["text"])


# ============================================================
# 5. 실행
# ============================================================

def main() -> None:
    print("=" * 80)
    print("피싱 문자 데이터 전처리 시작")
    print("=" * 80)

    print("프로젝트 경로:", PROJECT_ROOT)
    print("원본 데이터:", DATA_PATH)
    print("저장 경로:", CLEAN_DATA_PATH)

    raw_df = read_csv_safely(DATA_PATH)

    clean_df = prepare_real_data(raw_df)

    print_feature_summary(clean_df)

    clean_df.to_csv(
        CLEAN_DATA_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    print("\n" + "=" * 80)
    print("전처리 저장 완료")
    print(CLEAN_DATA_PATH)
    print("=" * 80)


if __name__ == "__main__":
    main()