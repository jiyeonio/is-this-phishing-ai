"""평판 신고 시드와 Validation/Test 간 데이터 누수 검사."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from ai.preprocess import preprocess
from backend.reputation import _jaccard


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SEED_PATH = PROJECT_ROOT / "backend" / "seed" / "reports.json"
DATA_DIR = PROJECT_ROOT / "ai" / "data" / "processed"

SPLIT_PATHS = {
    "validation": DATA_DIR / "validation_real.csv",
    "test": DATA_DIR / "test_real.csv",
}

SIMILARITY_THRESHOLD = 0.30



def main() -> None:
    with open(SEED_PATH, encoding="utf-8") as file:
        seed_rows = json.load(file)

    seed_items = []

    for index, row in enumerate(seed_rows, start=1):
        text = str(row.get("text", ""))
        pre = preprocess(text)

        seed_items.append(
            {
                "seed_id": index,
                "text": text,
                "norm": pre["norm"],
                "domains": set(pre["domains"]),
                "tokens": set(pre["tokens"]),
            }
        )

    print("=" * 80)
    print("평판 신고 시드 누수 검사")
    print("시드 신고 수:", len(seed_items))
    print("=" * 80)

    for split_name, split_path in SPLIT_PATHS.items():
        df = pd.read_csv(split_path, encoding="utf-8-sig")

        exact_matches = []
        domain_matches = []
        similar_matches = []

        for row in df.itertuples(index=False):
            content = str(row.content)
            pre = preprocess(content)

            input_norm = pre["norm"]
            input_domains = set(pre["domains"])
            input_tokens = set(pre["tokens"])

            best_similarity = 0.0
            best_seed = None

            for seed in seed_items:
                if input_norm == seed["norm"]:
                    exact_matches.append(
                        {
                            "row_id": int(row.row_id),
                            "seed_id": seed["seed_id"],
                            "label": int(row.label),
                            "content": content,
                        }
                    )

                shared_domains = input_domains & seed["domains"]

                if shared_domains:
                    domain_matches.append(
                        {
                            "row_id": int(row.row_id),
                            "seed_id": seed["seed_id"],
                            "label": int(row.label),
                            "domains": sorted(shared_domains),
                            "content": content,
                        }
                    )

                similarity = _jaccard(
                    input_tokens,
                    seed["tokens"],
                )

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_seed = seed

            if (
                best_seed is not None
                and best_similarity >= SIMILARITY_THRESHOLD
            ):
                similar_matches.append(
                    {
                        "row_id": int(row.row_id),
                        "seed_id": best_seed["seed_id"],
                        "label": int(row.label),
                        "similarity": round(best_similarity, 4),
                        "content": content,
                        "seed_text": best_seed["text"],
                    }
                )

        print()
        print(f"[{split_name}]")
        print("전체 문자 수:", len(df))
        print("완전 동일 문장:", len(exact_matches))
        print("시드와 동일 도메인:", len(domain_matches))
        print(
            f"자카드 {SIMILARITY_THRESHOLD:.2f} 이상:",
            len(similar_matches),
        )

        if similar_matches:
            similar_df = pd.DataFrame(similar_matches)
            similar_df = similar_df.sort_values(
                "similarity",
                ascending=False,
            )

            print()
            print("유사도 상위 10건")
            print(
                similar_df[
                    [
                        "row_id",
                        "seed_id",
                        "label",
                        "similarity",
                        "content",
                        "seed_text",
                    ]
                ]
                .head(10)
                .to_string(index=False)
            )

            output_path = (
                PROJECT_ROOT
                / "ai"
                / "results"
                / f"reputation_seed_{split_name}_similarity.csv"
            )

            output_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            similar_df.to_csv(
                output_path,
                index=False,
                encoding="utf-8-sig",
            )

            print("상세 저장:", output_path)


if __name__ == "__main__":
    main()