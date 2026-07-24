"""메타분류기 학습·평가용 데이터셋 생성.

입력
- ai/data/processed/validation_real.csv
- ai/data/processed/test_real.csv

출력
- ai/data/processed/meta_validation.csv
- ai/data/processed/meta_test.csv

각 문자에서 동시에 생성하는 신호
- model_p: KcELECTRA 피싱 확률
- rule_s: URL 구조 규칙 점수
- has_url: URL 존재 여부
- url_count: 추출 URL 개수
- rule_evidence: URL 규칙 근거
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from ai.classifier import predict_proba
from ai.preprocess import preprocess
from ai.url_rule_engine import analyze as analyze_url_rules
from backend.reputation import lookup as lookup_reputation


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "ai" / "data" / "processed"

INPUT_FILES = {
    "validation": DATA_DIR / "validation_real.csv",
    "test": DATA_DIR / "test_real.csv",
}

OUTPUT_FILES = {
    "validation": DATA_DIR / "meta_validation.csv",
    "test": DATA_DIR / "meta_test.csv",
}


def make_json_serializable(value):
    """numpy 타입 등이 포함돼도 JSON 문자열로 저장할 수 있게 변환."""
    if isinstance(value, dict):
        return {
            str(key): make_json_serializable(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            make_json_serializable(item)
            for item in value
        ]

    if hasattr(value, "item"):
        return value.item()

    return value


def build_meta_split(
    input_path: Path,
    output_path: Path,
    split_name: str,
) -> pd.DataFrame:
    """하나의 split에서 model_p와 URL 규칙 신호를 생성한다."""
    if not input_path.exists():
        raise FileNotFoundError(
            f"입력 파일을 찾을 수 없습니다: {input_path}"
        )

    df = pd.read_csv(
        input_path,
        encoding="utf-8-sig",
    )

    required_columns = {
        "row_id",
        "content",
        "text",
        "label",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"{input_path.name}에 필수 컬럼이 없습니다: "
            f"{sorted(missing_columns)}"
        )

    records: list[dict] = []

    total = len(df)

    print("=" * 80)
    print(f"{split_name} 메타 데이터 생성 시작")
    print(f"입력 파일: {input_path}")
    print(f"전체 행 수: {total}")
    print("=" * 80)

    for position, row in enumerate(
        df.itertuples(index=False),
        start=1,
    ):
        # 문자모델은 학습 당시와 동일한 text 컬럼을 사용
        model_input = str(row.text)

        # URL 규칙은 원문 content를 전처리해서 사용
        raw_content = str(row.content)
        pre = preprocess(raw_content)

        model_p = predict_proba(model_input)

        rule_s, rule_evidence = analyze_url_rules(pre)
        rep_s, rep_evidence = lookup_reputation(pre)

        urls = pre.get("urls", [])
        domains = pre.get("domains", [])

        records.append(
            {
                "row_id": int(row.row_id),
                "content": raw_content,
                "text": model_input,
                "label": int(row.label),
                "split": split_name,
                "model_p": float(model_p),
                "rule_s": float(rule_s),
                "has_url": int(len(urls) > 0),
                "url_count": int(len(urls)),
                "urls": json.dumps(
                    urls,
                    ensure_ascii=False,
                ),
                "domains": json.dumps(
                    domains,
                    ensure_ascii=False,
                ),
                "rule_evidence": json.dumps(
                    make_json_serializable(rule_evidence),
                    ensure_ascii=False,
                ),
                "rep_s": float(rep_s),
                "rep_evidence": json.dumps(
                    make_json_serializable(rep_evidence),
                    ensure_ascii=False,
                ),
            }
        )

        if (
            position == 1
            or position % 100 == 0
            or position == total
        ):
            print(
                f"[{split_name}] "
                f"{position:,}/{total:,} 완료"
            )

    meta_df = pd.DataFrame(records)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    meta_df.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print(f"{split_name} 저장 완료: {output_path}")
    print(f"행 수: {len(meta_df):,}")
    print(
        "URL 포함:",
        f"{int(meta_df['has_url'].sum()):,}",
    )
    print(
        "model_p 범위:",
        f"{meta_df['model_p'].min():.6f}",
        "~",
        f"{meta_df['model_p'].max():.6f}",
    )
    print(
        "rule_s 범위:",
        f"{meta_df['rule_s'].min():.4f}",
        "~",
        f"{meta_df['rule_s'].max():.4f}",
    )
    print()

    return meta_df


def main() -> None:
    """Validation과 Test 메타 데이터셋을 생성한다."""
    for split_name in (
        "validation",
        "test",
    ):
        build_meta_split(
            input_path=INPUT_FILES[split_name],
            output_path=OUTPUT_FILES[split_name],
            split_name=split_name,
        )

    print("=" * 80)
    print("메타 데이터셋 생성 완료")
    print("=" * 80)
    print(OUTPUT_FILES["validation"])
    print(OUTPUT_FILES["test"])


if __name__ == "__main__":
    main()