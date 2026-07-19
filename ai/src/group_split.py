from __future__ import annotations

import hashlib
import re
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# 1. 기본 설정
# ============================================================

SEED = 42

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

CLEAN_DATA_PATH = (
    PROCESSED_DIR
    / "clean_message_dataset.csv"
)

ALL_SPLIT_PATH = (
    PROCESSED_DIR
    / "all_real_with_split.csv"
)

TRAIN_PATH = (
    PROCESSED_DIR
    / "train_real.csv"
)

VALIDATION_PATH = (
    PROCESSED_DIR
    / "validation_real.csv"
)

TEST_PATH = (
    PROCESSED_DIR
    / "test_real.csv"
)

SPLIT_SUMMARY_PATH = (
    PROCESSED_DIR
    / "split_summary.csv"
)

FAMILY_SUMMARY_PATH = (
    PROCESSED_DIR
    / "structured_family_summary.csv"
)

PROCESSED_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# 2. CSV 안전하게 읽기
# ============================================================

def read_csv_safely(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            "전처리 파일을 찾을 수 없습니다.\n"
            f"확인 경로: {path}\n"
            "먼저 프로젝트 최상위에서 "
            "`python run_pipeline.py`를 실행하세요."
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

            print("CSV 인코딩:", encoding)

            return df

        except UnicodeDecodeError as error:
            last_error = error

    raise RuntimeError(
        f"CSV 인코딩을 읽지 못했습니다: {path}"
    ) from last_error


# ============================================================
# 3. 구조화 정상 문자 family 탐지
# ============================================================

def detect_structured_family(
    content: object,
    label: int,
) -> str:
    """
    정상 기관·택배 템플릿 family를 판별한다.

    피싱(label=1)은 전부 phishing으로 두고,
    정상(label=0)에서 기존 대형 템플릿을 분리한다.
    """

    if int(label) == 1:
        return "phishing"

    text = str(content).lower()

    # 한진택배 집하 안내
    if (
        "한진택배" in text
        or "한진 택배" in text
    ):
        return "hanjin_pickup"

    # SLX 배송 안내
    if (
        "slx택배" in text
        or "slx 택배" in text
        or "[slx" in text
    ):
        return "slx_delivery"

    # 우체국택배
    if (
        "우체국택배" in text
        or "우체국 택배" in text
        or "우체국 소포" in text
        or "epost" in text
    ):
        return "korea_post"

    # 쿠팡 배송
    if "쿠팡" in text:
        return "coupang"

    # CJ대한통운
    if (
        "cj대한통운" in text
        or "cj 대한통운" in text
        or "cj택배" in text
        or "cj 택배" in text
    ):
        # 기존 실험의 CJ 계열을 조금 더 세분화
        if (
            "배송완료" in text
            or "배달완료" in text
        ):
            return "cj_complete"

        if (
            "집하" in text
            or "수거" in text
        ):
            return "cj_pickup"

        return "cj_general"

    return "other"


# ============================================================
# 4. 템플릿 정규화
# ============================================================

def make_template_text(text: object) -> str:
    """
    이름, 금액, 운송장 번호, 시간 같은 슬롯을 제거해
    같은 문장 골격끼리 묶기 위한 템플릿을 만든다.

    URL 위험 토큰은 유지한다.
    예:
        [URL_OFFICIAL]
        [URL_SHORTENER]
        [URL_SUSPICIOUS]
    """

    value = str(text).lower()

    # URL 및 전화번호 분류 토큰은 의미가 있으므로 유지
    protected_tokens = {
        "[url_official]": " url_official_token ",
        "[url_shortener]": " url_shortener_token ",
        "[url_suspicious]": " url_suspicious_token ",
        "[phone_official]": " phone_official_token ",
        "[phone_mobile]": " phone_mobile_token ",
        "[phone_foreign]": " phone_foreign_token ",
        "[phone_other]": " phone_other_token ",
    }

    for original, replacement in protected_tokens.items():
        value = value.replace(
            original,
            replacement,
        )

    # 고객 이름 슬롯 제거
    value = re.sub(
        r"[가-힣]{2,4}\s*(?=고객님|회원님|님)",
        " name_token ",
        value,
    )

    # 시간 범위
    value = re.sub(
        r"\d{1,2}\s*:\s*\d{2}"
        r"\s*[~\-]\s*"
        r"\d{1,2}\s*:\s*\d{2}",
        " time_range_token ",
        value,
    )

    # 개별 시간
    value = re.sub(
        r"\d{1,2}\s*:\s*\d{2}",
        " time_token ",
        value,
    )

    # 금액
    value = re.sub(
        r"\d{1,3}(?:,\d{3})+\s*원",
        " amount_token ",
        value,
    )

    value = re.sub(
        r"\d+\s*만\s*원",
        " amount_token ",
        value,
    )

    value = re.sub(
        r"\d+\s*원",
        " amount_token ",
        value,
    )

    # 긴 운송장·인증번호
    value = re.sub(
        r"(?<!\d)\d{6,}(?!\d)",
        " long_number_token ",
        value,
    )

    # 나머지 숫자
    value = re.sub(
        r"\d+",
        " number_token ",
        value,
    )

    # 반복되는 ㅋㅋ, ㅎㅎ 등 축약
    value = re.sub(
        r"(ㅋ|ㅎ|ㅠ|ㅜ){2,}",
        r"\1\1",
        value,
    )

    # 특수문자 정리
    value = re.sub(
        r"[^0-9a-z가-힣_\[\]\s]",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    ).strip()

    # 보호 토큰 복원
    restore_tokens = {
        "url_official_token": "[URL_OFFICIAL]",
        "url_shortener_token": "[URL_SHORTENER]",
        "url_suspicious_token": "[URL_SUSPICIOUS]",
        "phone_official_token": "[PHONE_OFFICIAL]",
        "phone_mobile_token": "[PHONE_MOBILE]",
        "phone_foreign_token": "[PHONE_FOREIGN]",
        "phone_other_token": "[PHONE_OTHER]",
    }

    for temporary, original in restore_tokens.items():
        value = value.replace(
            temporary,
            original,
        )

    return value


# ============================================================
# 5. 안정적인 group_id 생성
# ============================================================

def make_group_key(row: pd.Series) -> str:
    """
    label + family + template을 함께 사용한다.

    정상과 피싱이 우연히 같은 템플릿이더라도
    같은 group으로 합치지 않는다.
    """

    return (
        f"label={int(row['label'])}"
        f"|family={row['structured_family']}"
        f"|template={row['template_text_v3']}"
    )


def stable_group_id(group_key: str) -> str:
    """
    실행할 때마다 동일한 group_id가 생성되도록
    SHA-1 해시 앞 16자리를 사용한다.
    """

    return hashlib.sha1(
        group_key.encode("utf-8")
    ).hexdigest()[:16]


# ============================================================
# 6. 일반 그룹 80:10:10 분할
# ============================================================

def assign_groups_by_target_rows(
    group_df: pd.DataFrame,
    seed: int = SEED,
) -> dict[str, str]:
    """
    각 label 안에서 group 단위로 80:10:10 분할한다.

    행 단위 랜덤 분할이 아니라 group_id 전체를
    한 split에만 배치한다.
    """

    assignment: dict[str, str] = {}

    ratios = {
        "train": 0.80,
        "validation": 0.10,
        "test": 0.10,
    }

    for label_value in sorted(
        group_df["label"].unique()
    ):
        label_groups = (
            group_df[
                group_df["label"].eq(label_value)
            ]
            .copy()
            .reset_index(drop=True)
        )

        rng = np.random.default_rng(
            seed + int(label_value)
        )

        random_order = rng.permutation(
            len(label_groups)
        )

        label_groups = (
            label_groups
            .iloc[random_order]
            .reset_index(drop=True)
        )

        # 큰 그룹을 먼저 배치하되,
        # 같은 크기에서는 랜덤 순서를 유지
        label_groups = (
            label_groups
            .sort_values(
                "rows",
                ascending=False,
                kind="stable",
            )
            .reset_index(drop=True)
        )

        total_rows = int(
            label_groups["rows"].sum()
        )

        target_rows = {
            split: total_rows * ratio
            for split, ratio in ratios.items()
        }

        current_rows = {
            "train": 0,
            "validation": 0,
            "test": 0,
        }

        for _, group_row in label_groups.iterrows():
            group_id = str(
                group_row["group_id"]
            )

            rows = int(
                group_row["rows"]
            )

            # 현재 목표 대비 가장 부족한 split 선택
            deficits = {
                split: (
                    target_rows[split]
                    - current_rows[split]
                )
                for split in ratios
            }

            chosen_split = max(
                deficits,
                key=deficits.get,
            )

            assignment[group_id] = chosen_split
            current_rows[chosen_split] += rows

        print(
            f"\n[label={label_value}] "
            "일반 그룹 분할 행 수"
        )

        for split in [
            "train",
            "validation",
            "test",
        ]:
            print(
                f"- {split}: "
                f"{current_rows[split]:,}"
            )

    return assignment


# ============================================================
# 7. 분할 생성
# ============================================================

def create_group_split(
    clean_df: pd.DataFrame,
) -> pd.DataFrame:
    required_columns = {
        "row_id",
        "content",
        "text",
        "label",
    }

    missing_columns = (
        required_columns
        - set(clean_df.columns)
    )

    if missing_columns:
        raise ValueError(
            "필수 컬럼이 없습니다.\n"
            f"누락 컬럼: {sorted(missing_columns)}\n"
            f"현재 컬럼: {clean_df.columns.tolist()}"
        )

    work_df = clean_df.copy()

    work_df["label"] = (
        work_df["label"]
        .astype(int)
    )

    print("\n구조화 family 탐지 시작")

    work_df["structured_family"] = [
        detect_structured_family(
            content=content,
            label=label,
        )
        for content, label in zip(
            work_df["content"],
            work_df["label"],
        )
    ]

    print("\n구조화 family 분포")
    print(
        work_df["structured_family"]
        .value_counts()
    )

    print("\n템플릿 정규화 시작")

    work_df["template_text_v3"] = (
        work_df["text"]
        .map(make_template_text)
    )

    empty_template_count = int(
        work_df["template_text_v3"]
        .eq("")
        .sum()
    )

    if empty_template_count > 0:
        print(
            "경고: 빈 템플릿 수:",
            empty_template_count,
        )

        # 빈 템플릿은 row_id 기반으로 서로 다른 그룹 처리
        empty_mask = (
            work_df["template_text_v3"]
            .eq("")
        )

        work_df.loc[
            empty_mask,
            "template_text_v3",
        ] = (
            "empty_template_"
            + work_df.loc[
                empty_mask,
                "row_id",
            ].astype(str)
        )

    work_df["group_key"] = work_df.apply(
        make_group_key,
        axis=1,
    )

    work_df["group_id"] = (
        work_df["group_key"]
        .map(stable_group_id)
    )

    group_df = (
        work_df.groupby(
            [
                "group_id",
                "label",
                "structured_family",
            ],
            as_index=False,
        )
        .agg(
            rows=("row_id", "size"),
            template_example=(
                "template_text_v3",
                "first",
            ),
        )
    )

    print("\n전체 group 수:", len(group_df))

    print("\n큰 group 상위 15개")
    print(
        group_df
        .sort_values(
            "rows",
            ascending=False,
        )
        .head(15)
        [
            [
                "group_id",
                "label",
                "structured_family",
                "rows",
                "template_example",
            ]
        ]
        .to_string(index=False)
    )

    # ========================================================
    # 기존 대형 정상 family는 실험 목적에 맞게 고정
    # ========================================================

    fixed_family_split = {
        # train에서 정상 기관 문자 구조를 학습
        "cj_complete": "train",
        "cj_pickup": "train",
        "cj_general": "train",
        "korea_post": "train",
        "coupang": "train",

        # 실제 held-out family
        "hanjin_pickup": "validation",
        "slx_delivery": "test",
    }

    work_df["split"] = pd.NA

    for family, split_name in (
        fixed_family_split.items()
    ):
        family_mask = (
            work_df["structured_family"]
            .eq(family)
        )

        work_df.loc[
            family_mask,
            "split",
        ] = split_name

    fixed_group_ids = set(
        work_df.loc[
            work_df["split"].notna(),
            "group_id",
        ]
    )

    remaining_group_df = group_df[
        ~group_df["group_id"].isin(
            fixed_group_ids
        )
    ].copy()

    print(
        "\n고정 family를 제외한 일반 group 수:",
        len(remaining_group_df),
    )

    group_assignment = (
        assign_groups_by_target_rows(
            remaining_group_df,
            seed=SEED,
        )
    )

    remaining_mask = (
        work_df["split"].isna()
    )

    work_df.loc[
        remaining_mask,
        "split",
    ] = (
        work_df.loc[
            remaining_mask,
            "group_id",
        ]
        .map(group_assignment)
    )

    unassigned_count = int(
        work_df["split"]
        .isna()
        .sum()
    )

    if unassigned_count > 0:
        raise RuntimeError(
            f"split 미할당 행이 "
            f"{unassigned_count:,}개 있습니다."
        )

    work_df["split"] = (
        work_df["split"]
        .astype(str)
    )

    return work_df


# ============================================================
# 8. 누수 검증
# ============================================================

def validate_split(
    split_df: pd.DataFrame,
) -> None:
    print("\n" + "=" * 80)
    print("분할 누수 검증")
    print("=" * 80)

    split_names = [
        "train",
        "validation",
        "test",
    ]

    split_frames = {
        split: split_df[
            split_df["split"].eq(split)
        ].copy()
        for split in split_names
    }

    # --------------------------------------------------------
    # 1) group_id 교집합
    # --------------------------------------------------------

    for index, left_name in enumerate(
        split_names
    ):
        for right_name in split_names[
            index + 1:
        ]:
            left_ids = set(
                split_frames[left_name][
                    "group_id"
                ]
            )

            right_ids = set(
                split_frames[right_name][
                    "group_id"
                ]
            )

            overlap = (
                left_ids
                & right_ids
            )

            print(
                f"group_id 교집합 "
                f"{left_name}/{right_name}: "
                f"{len(overlap)}"
            )

            if overlap:
                raise AssertionError(
                    "group_id 누수가 발생했습니다.\n"
                    f"{left_name}/{right_name}: "
                    f"{list(overlap)[:10]}"
                )

    # --------------------------------------------------------
    # 2) 완전 동일 content 교집합
    # --------------------------------------------------------

    for index, left_name in enumerate(
        split_names
    ):
        for right_name in split_names[
            index + 1:
        ]:
            left_texts = set(
                split_frames[left_name][
                    "content"
                ]
            )

            right_texts = set(
                split_frames[right_name][
                    "content"
                ]
            )

            overlap = (
                left_texts
                & right_texts
            )

            print(
                f"완전동일 content 교집합 "
                f"{left_name}/{right_name}: "
                f"{len(overlap)}"
            )

            if overlap:
                raise AssertionError(
                    "완전동일 content 누수가 "
                    "발생했습니다."
                )

    # --------------------------------------------------------
    # 3) label + template_text_v3 교집합
    # --------------------------------------------------------

    for index, left_name in enumerate(
        split_names
    ):
        for right_name in split_names[
            index + 1:
        ]:
            left_templates = set(
                zip(
                    split_frames[left_name][
                        "label"
                    ],
                    split_frames[left_name][
                        "template_text_v3"
                    ],
                )
            )

            right_templates = set(
                zip(
                    split_frames[right_name][
                        "label"
                    ],
                    split_frames[right_name][
                        "template_text_v3"
                    ],
                )
            )

            overlap = (
                left_templates
                & right_templates
            )

            print(
                f"label+template 교집합 "
                f"{left_name}/{right_name}: "
                f"{len(overlap)}"
            )

            if overlap:
                raise AssertionError(
                    "템플릿 누수가 발생했습니다.\n"
                    f"{left_name}/{right_name}: "
                    f"{list(overlap)[:3]}"
                )

    print("\n누수 검증 통과")


# ============================================================
# 9. 분할 요약
# ============================================================

def print_and_save_summary(
    split_df: pd.DataFrame,
) -> None:
    summary = (
        split_df.groupby(
            ["split", "label"],
            as_index=False,
        )
        .agg(
            rows=("row_id", "size"),
            groups=("group_id", "nunique"),
            templates=(
                "template_text_v3",
                "nunique",
            ),
        )
    )

    summary["label_name"] = (
        summary["label"]
        .map(
            {
                0: "NORMAL",
                1: "PHISHING",
            }
        )
    )

    summary = summary[
        [
            "split",
            "label",
            "label_name",
            "rows",
            "groups",
            "templates",
        ]
    ]

    print("\n" + "=" * 80)
    print("분할 요약")
    print("=" * 80)

    print(
        summary.to_string(
            index=False
        )
    )

    summary.to_csv(
        SPLIT_SUMMARY_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    family_summary = (
        split_df.groupby(
            [
                "split",
                "label",
                "structured_family",
            ],
            as_index=False,
        )
        .agg(
            rows=("row_id", "size"),
            groups=("group_id", "nunique"),
        )
        .sort_values(
            [
                "split",
                "label",
                "rows",
            ],
            ascending=[
                True,
                True,
                False,
            ],
        )
    )

    print("\n구조화 family 구성")
    print(
        family_summary.to_string(
            index=False
        )
    )

    family_summary.to_csv(
        FAMILY_SUMMARY_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    hanjin_df = split_df[
        split_df["structured_family"]
        .eq("hanjin_pickup")
    ]

    print("\n한진택배 held-out 확인")
    print(
        hanjin_df["split"]
        .value_counts(dropna=False)
    )

    if not hanjin_df.empty:
        hanjin_splits = set(
            hanjin_df["split"]
        )

        if hanjin_splits != {
            "validation"
        }:
            raise AssertionError(
                "한진택배 데이터는 validation에만 "
                "존재해야 합니다.\n"
                f"현재 split: {hanjin_splits}"
            )


# ============================================================
# 10. 저장
# ============================================================

def save_split_files(
    split_df: pd.DataFrame,
) -> None:
    save_columns = [
        column
        for column in split_df.columns
        if column != "group_key"
    ]

    output_df = (
        split_df[save_columns]
        .copy()
    )

    train_df = (
        output_df[
            output_df["split"].eq("train")
        ]
        .reset_index(drop=True)
    )

    validation_df = (
        output_df[
            output_df["split"]
            .eq("validation")
        ]
        .reset_index(drop=True)
    )

    test_df = (
        output_df[
            output_df["split"].eq("test")
        ]
        .reset_index(drop=True)
    )

    output_df.to_csv(
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
    print("분할 파일 저장 완료")
    print("=" * 80)

    print(
        "전체:",
        ALL_SPLIT_PATH,
    )

    print(
        "Train:",
        TRAIN_PATH,
        train_df.shape,
    )

    print(
        "Validation:",
        VALIDATION_PATH,
        validation_df.shape,
    )

    print(
        "Test:",
        TEST_PATH,
        test_df.shape,
    )


# ============================================================
# 11. 전체 실행 함수
# ============================================================

def run_group_split() -> pd.DataFrame:
    print("=" * 80)
    print("실제 데이터 그룹 분할 시작")
    print("=" * 80)

    print("입력 파일:", CLEAN_DATA_PATH)

    clean_df = read_csv_safely(
        CLEAN_DATA_PATH
    )

    print("입력 shape:", clean_df.shape)

    split_df = create_group_split(
        clean_df
    )

    validate_split(
        split_df
    )

    print_and_save_summary(
        split_df
    )

    save_split_files(
        split_df
    )

    return split_df


# ============================================================
# 12. 직접 실행
# ============================================================

if __name__ == "__main__":
    run_group_split()