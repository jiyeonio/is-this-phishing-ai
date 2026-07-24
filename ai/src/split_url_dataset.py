from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# 1. 기본 설정
# ============================================================

SEED = 42

TRAIN_RATIO = 0.70
VALIDATION_RATIO = 0.15
TEST_RATIO = 0.15

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

INPUT_PATH = PROCESSED_DIR / "url_dataset.csv"

ALL_SPLIT_PATH = (
    PROCESSED_DIR
    / "url_dataset_with_split.csv"
)

TRAIN_PATH = (
    PROCESSED_DIR
    / "url_train.csv"
)

VALIDATION_PATH = (
    PROCESSED_DIR
    / "url_validation.csv"
)

TEST_PATH = (
    PROCESSED_DIR
    / "url_test.csv"
)


# ============================================================
# 2. 라벨별 도메인 그룹 분할
# ============================================================

def assign_domain_splits(
    df: pd.DataFrame,
    label_value: int,
) -> dict[str, str]:
    """
    같은 domain이 여러 URL을 가지고 있어도
    train/validation/test 중 하나에만 들어가도록 분할한다.
    """

    label_df = df[
        df["label"].eq(label_value)
    ].copy()

    domain_summary = (
        label_df.groupby(
            "domain",
            as_index=False,
        )
        .agg(
            rows=("url", "size")
        )
    )

    rng = np.random.default_rng(
        SEED + label_value
    )

    shuffled_indices = rng.permutation(
        len(domain_summary)
    )

    domain_summary = (
        domain_summary
        .iloc[shuffled_indices]
        .reset_index(drop=True)
    )

    # 행 수가 많은 도메인을 먼저 배치
    domain_summary = (
        domain_summary
        .sort_values(
            "rows",
            ascending=False,
            kind="stable",
        )
        .reset_index(drop=True)
    )

    total_rows = int(
        domain_summary["rows"].sum()
    )

    target_rows = {
        "train": total_rows * TRAIN_RATIO,
        "validation": (
            total_rows * VALIDATION_RATIO
        ),
        "test": total_rows * TEST_RATIO,
    }

    current_rows = {
        "train": 0,
        "validation": 0,
        "test": 0,
    }

    assignments: dict[str, str] = {}

    for _, row in domain_summary.iterrows():
        domain = str(row["domain"])
        rows = int(row["rows"])

        deficits = {
            split: (
                target_rows[split]
                - current_rows[split]
            )
            for split in target_rows
        }

        chosen_split = max(
            deficits,
            key=deficits.get,
        )

        assignments[domain] = (
            chosen_split
        )

        current_rows[chosen_split] += rows

    print(
        f"\n[label={label_value}] "
        f"도메인 수: {len(domain_summary):,}"
    )

    for split_name in [
        "train",
        "validation",
        "test",
    ]:
        print(
            f"- {split_name}: "
            f"{current_rows[split_name]:,}개"
        )

    return assignments


# ============================================================
# 3. 분할 생성
# ============================================================

def create_split(
    df: pd.DataFrame,
) -> pd.DataFrame:
    required_columns = {
        "url",
        "domain",
        "label",
    }

    missing = (
        required_columns
        - set(df.columns)
    )

    if missing:
        raise ValueError(
            f"필수 컬럼 누락: {sorted(missing)}"
        )

    work_df = df.copy()

    work_df["label"] = (
        work_df["label"]
        .astype(int)
    )

    work_df["split"] = pd.NA

    for label_value in [0, 1]:
        assignment = assign_domain_splits(
            work_df,
            label_value=label_value,
        )

        label_mask = (
            work_df["label"]
            .eq(label_value)
        )

        work_df.loc[
            label_mask,
            "split",
        ] = (
            work_df.loc[
                label_mask,
                "domain",
            ]
            .map(assignment)
        )

    if work_df["split"].isna().any():
        missing_count = int(
            work_df["split"]
            .isna()
            .sum()
        )

        raise RuntimeError(
            f"split 미할당 행: {missing_count}"
        )

    work_df["split"] = (
        work_df["split"]
        .astype(str)
    )

    return work_df


# ============================================================
# 4. 누수 검증
# ============================================================

def validate_split(
    split_df: pd.DataFrame,
) -> None:
    print("\n" + "=" * 80)
    print("도메인 누수 검증")
    print("=" * 80)

    split_names = [
        "train",
        "validation",
        "test",
    ]

    split_domains = {
        split_name: set(
            split_df.loc[
                split_df["split"]
                .eq(split_name),
                "domain",
            ]
        )
        for split_name in split_names
    }

    for index, left_name in enumerate(
        split_names
    ):
        for right_name in split_names[
            index + 1:
        ]:
            overlap = (
                split_domains[left_name]
                & split_domains[right_name]
            )

            print(
                f"{left_name}/{right_name} "
                f"도메인 교집합: "
                f"{len(overlap)}"
            )

            if overlap:
                raise AssertionError(
                    "도메인 누수가 발생했습니다.\n"
                    f"예시: {list(overlap)[:10]}"
                )

    print("\n도메인 누수 없음: 확인 완료")


# ============================================================
# 5. 저장
# ============================================================

def save_split_files(
    split_df: pd.DataFrame,
) -> None:
    train_df = (
        split_df[
            split_df["split"]
            .eq("train")
        ]
        .reset_index(drop=True)
    )

    validation_df = (
        split_df[
            split_df["split"]
            .eq("validation")
        ]
        .reset_index(drop=True)
    )

    test_df = (
        split_df[
            split_df["split"]
            .eq("test")
        ]
        .reset_index(drop=True)
    )

    split_df.to_csv(
        ALL_SPLIT_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    train_df.to_csv(
        TRAIN_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    validation_df.to_csv(
        VALIDATION_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    test_df.to_csv(
        TEST_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    print("\n" + "=" * 80)
    print("URL 데이터 분할 완료")
    print("=" * 80)

    print("\n전체 분할 결과")

    summary = (
        split_df.groupby(
            [
                "split",
                "label",
            ],
            as_index=False,
        )
        .agg(
            rows=("url", "size"),
            domains=(
                "domain",
                "nunique",
            ),
        )
    )

    print(
        summary.to_string(
            index=False
        )
    )

    print("\n저장 위치")
    print("Train:", TRAIN_PATH)
    print("Validation:", VALIDATION_PATH)
    print("Test:", TEST_PATH)


# ============================================================
# 6. 전체 실행
# ============================================================

def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"파일이 없습니다: {INPUT_PATH}"
        )

    print("=" * 80)
    print("URL 데이터 도메인 기준 분할 시작")
    print("=" * 80)

    df = pd.read_csv(
        INPUT_PATH,
        encoding="utf-8-sig",
    )

    print("입력 shape:", df.shape)

    split_df = create_split(df)

    validate_split(split_df)

    save_split_files(split_df)


if __name__ == "__main__":
    main()