from __future__ import annotations

import random
from pathlib import Path

import pandas as pd

from src.text_features import preprocess_for_model


# ============================================================
# 기본 설정
# ============================================================

SEED = 42
PAIR_COUNT = 800

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

TRAIN_REAL_PATH = PROCESSED_DIR / "train_real.csv"
SYNTHETIC_PATH = PROCESSED_DIR / "synthetic_train.csv"
AUGMENTED_PATH = PROCESSED_DIR / "train_augmented.csv"

random.seed(SEED)


# ============================================================
# 합성용 슬롯
# - 한진, SLX, CJ, 쿠팡은 사용하지 않음
# - 검증/테스트 브랜드를 학습에서 보지 않게 유지
# ============================================================

SENDERS = [
    "새봄택배",
    "한빛물류",
    "드림택배",
    "우리로지스",
    "대한배송",
    "스마트택배",
]

NAMES = [
    "김민수",
    "이서연",
    "박지훈",
    "최하늘",
    "정수빈",
    "강민지",
    "윤도현",
    "한지우",
]

PRODUCTS = [
    "의류",
    "생활용품",
    "도서",
    "전자제품",
    "식품",
    "주방용품",
    "스포츠용품",
    "컴퓨터 부품",
]

ADDRESSES = [
    "서울특별시 강남구 테헤란로 122",
    "서울특별시 마포구 월드컵로 45",
    "부산광역시 해운대구 센텀로 35",
    "인천광역시 남동구 예술로 90",
    "대구광역시 중구 중앙대로 77",
    "광주광역시 서구 상무대로 55",
]

TIME_RANGES = [
    "09:00~11:00",
    "10:00~12:00",
    "13:00~15:00",
    "14:00~16:00",
    "16:00~18:00",
    "18:00~20:00",
]

SHORT_URLS = [
    "https://bit.ly/3AbCdE",
    "https://tinyurl.com/delivery-check",
    "https://url.kr/parcel22",
    "https://cutt.ly/address-check",
]

SUSPICIOUS_URLS = [
    "http://parcel-update.click/verify",
    "http://delivery-check.top/address",
    "http://safe-parcel.xyz/confirm",
    "http://logistics-help.shop/check",
]


# ============================================================
# 전화번호 생성
# ============================================================

def make_mobile_phone() -> str:
    middle = random.randint(1000, 9999)
    last = random.randint(1000, 9999)
    return f"010-{middle}-{last}"


def make_tracking_number(index: int) -> str:
    return f"DL{index:08d}"


# ============================================================
# 정상 문자 생성
# - URL 없음
# - 기사 휴대전화번호 포함
# - 한진 validation과 비슷한 구조이지만 문구는 그대로 복사하지 않음
# ============================================================

def make_normal_message(index: int) -> str:
    sender = random.choice(SENDERS)
    name = random.choice(NAMES)
    product = random.choice(PRODUCTS)
    address = random.choice(ADDRESSES)
    time_range = random.choice(TIME_RANGES)
    phone = make_mobile_phone()
    tracking = make_tracking_number(index)

    templates = [
        (
            f"[{sender}] 상품 집하 예정 안내\n"
            f"안녕하세요, 고객님.\n"
            f"오늘 {time_range} 사이에 상품 수거를 위해 방문할 예정입니다.\n"
            f"수거 주소: {address}\n"
            f"보내시는 분: {name}\n"
            f"운송장번호: {tracking}\n"
            f"상품명: {product}\n"
            f"담당 기사: {phone}\n"
            f"상품 포장을 완료한 뒤 전달 부탁드립니다."
        ),
        (
            f"[{sender}] 배송 예정 안내\n"
            f"{name} 고객님의 상품이 오늘 {time_range} 사이 배송될 예정입니다.\n"
            f"운송장번호: {tracking}\n"
            f"상품명: {product}\n"
            f"배송 담당자: {phone}\n"
            f"부재 시 안전한 장소에 보관할 수 있습니다."
        ),
        (
            f"[{sender}] 반품 상품 수거 안내\n"
            f"신청하신 반품 상품을 오늘 {time_range} 사이 수거할 예정입니다.\n"
            f"수거지: {address}\n"
            f"신청자: {name}\n"
            f"접수번호: {tracking}\n"
            f"담당 기사 연락처: {phone}\n"
            f"기사 방문 전 상품을 포장해 주세요."
        ),
    ]

    return random.choice(templates)


# ============================================================
# 피싱 문자 생성
# - 휴대전화번호도 포함
# - 단축/의심 URL과 개인정보·결제·주소 수정 요구 포함
# ============================================================

def make_phishing_message(index: int) -> str:
    sender = random.choice(SENDERS)
    name = random.choice(NAMES)
    phone = make_mobile_phone()
    tracking = make_tracking_number(index)

    url = random.choice(
        SHORT_URLS + SUSPICIOUS_URLS
    )

    templates = [
        (
            f"[{sender}] 배송지 오류 안내\n"
            f"{name} 고객님의 상품이 주소 불일치로 보류되었습니다.\n"
            f"운송장번호: {tracking}\n"
            f"오늘 안에 아래 링크에서 주소를 수정하지 않으면 반송됩니다.\n"
            f"{url}\n"
            f"담당자: {phone}"
        ),
        (
            f"[{sender}] 추가 배송비 결제 요청\n"
            f"배송 과정에서 추가 요금이 발생했습니다.\n"
            f"결제가 완료되지 않으면 상품 배송이 취소됩니다.\n"
            f"결제 확인: {url}\n"
            f"문의: {phone}"
        ),
        (
            f"[{sender}] 본인인증 필요\n"
            f"상품 수령을 위해 휴대전화 본인인증이 필요합니다.\n"
            f"아래 링크에서 이름과 인증번호를 입력해 주세요.\n"
            f"{url}\n"
            f"담당 기사: {phone}"
        ),
        (
            f"[{sender}] 택배 반송 예정\n"
            f"수취인 정보 오류로 상품이 반송 처리될 예정입니다.\n"
            f"반송을 취소하려면 즉시 주소와 카드 정보를 확인해 주세요.\n"
            f"{url}\n"
            f"상담 연락처: {phone}"
        ),
    ]

    return random.choice(templates)


# ============================================================
# 합성 데이터 생성
# ============================================================

def build_synthetic_data() -> pd.DataFrame:
    rows = []

    for pair_index in range(PAIR_COUNT):
        normal_raw = make_normal_message(pair_index)
        phishing_raw = make_phishing_message(pair_index)

        rows.append(
            {
                "row_id": f"SYNTH_NORMAL_{pair_index:05d}",
                "content": normal_raw,
                "class": 3,
                "label": 0,
                "text": preprocess_for_model(normal_raw),
                "structured_family": "synthetic_delivery_normal",
                "group_id": f"synthetic_pair_{pair_index:05d}_normal",
                "split": "train",
                "is_synthetic": True,
                "synthetic_type": "normal_mobile_no_url",
            }
        )

        rows.append(
            {
                "row_id": f"SYNTH_PHISHING_{pair_index:05d}",
                "content": phishing_raw,
                "class": 2,
                "label": 1,
                "text": preprocess_for_model(phishing_raw),
                "structured_family": "synthetic_delivery_phishing",
                "group_id": f"synthetic_pair_{pair_index:05d}_phishing",
                "split": "train",
                "is_synthetic": True,
                "synthetic_type": "phishing_mobile_danger_url",
            }
        )

    synthetic_df = pd.DataFrame(rows)

    return synthetic_df.sample(
        frac=1,
        random_state=SEED,
    ).reset_index(drop=True)


# ============================================================
# 실제 train과 합치기
# ============================================================

def main() -> None:
    if not TRAIN_REAL_PATH.exists():
        raise FileNotFoundError(
            f"파일을 찾을 수 없습니다: {TRAIN_REAL_PATH}"
        )

    train_real = pd.read_csv(
        TRAIN_REAL_PATH,
        encoding="utf-8-sig",
    )

    train_real["is_synthetic"] = False
    train_real["synthetic_type"] = "real"

    synthetic_df = build_synthetic_data()

    # 실제 train 컬럼과 합성 컬럼 통합
    all_columns = sorted(
        set(train_real.columns)
        | set(synthetic_df.columns)
    )

    train_real = train_real.reindex(
        columns=all_columns
    )

    synthetic_df = synthetic_df.reindex(
        columns=all_columns
    )

    train_augmented = pd.concat(
        [train_real, synthetic_df],
        ignore_index=True,
    )

    train_augmented = train_augmented.sample(
        frac=1,
        random_state=SEED,
    ).reset_index(drop=True)

    synthetic_df.to_csv(
        SYNTHETIC_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    train_augmented.to_csv(
        AUGMENTED_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    print("=" * 80)
    print("합성 데이터 생성 완료")
    print("=" * 80)

    print("\n실제 train 수:", len(train_real))
    print("합성 데이터 수:", len(synthetic_df))
    print("증강 train 수:", len(train_augmented))

    print("\n합성 라벨 분포")
    print(
        synthetic_df["label"]
        .value_counts()
        .sort_index()
    )

    print("\n전체 증강 train 라벨 분포")
    print(
        train_augmented["label"]
        .value_counts()
        .sort_index()
    )

    print("\n합성 유형")
    print(
        synthetic_df["synthetic_type"]
        .value_counts()
    )

    print("\n저장 위치")
    print(SYNTHETIC_PATH)
    print(AUGMENTED_PATH)

    # 검증/테스트로 잘못 들어가지 않았는지 확인
    assert synthetic_df["split"].eq("train").all()
    assert train_augmented.loc[
        train_augmented["is_synthetic"] == True,
        "split",
    ].eq("train").all()

    print("\n합성 데이터는 train에만 포함됨: 확인 완료")


if __name__ == "__main__":
    main()