from __future__ import annotations

import random
from pathlib import Path

import pandas as pd

from src.text_features import preprocess_for_model


# ============================================================
# 기본 설정
# ============================================================

SEED = 42
SAMPLES_PER_TEMPLATE = 10

random.seed(SEED)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

INPUT_PATH = (
    PROCESSED_DIR
    / "train_augmented_v2.csv"
)

SYNTHETIC_PATH = (
    PROCESSED_DIR
    / "hard_phishing_train.csv"
)

OUTPUT_PATH = (
    PROCESSED_DIR
    / "train_augmented_v3.csv"
)


# ============================================================
# 합성용 슬롯
# - HARD DEV 문장을 그대로 복사하지 않음
# - 링크 없는 피싱 행동 요구 중심
# ============================================================

INSTITUTIONS = [
    "한빛금융",
    "드림저축은행",
    "우리생활카드",
    "새봄보험",
    "가람대학교",
    "대한인재개발원",
    "바른채용센터",
    "희망건강관리원",
    "스마트민원센터",
    "안심거래지원팀",
]

NAMES = [
    "민지",
    "서준",
    "하늘",
    "지우",
    "도윤",
    "수빈",
    "현우",
    "유진",
]

RELATIONS = [
    "엄마",
    "아빠",
    "언니",
    "오빠",
    "형",
    "누나",
    "이모",
    "삼촌",
]

AMOUNTS = [
    "3만 원",
    "5만 원",
    "8만 원",
    "12만 원",
    "18만 원",
    "25만 원",
    "48만 원",
]

ITEMS = [
    "노트북",
    "태블릿",
    "카메라",
    "스마트폰",
    "게임기",
    "무선 이어폰",
]

DOCUMENTS = [
    "신분증 사진",
    "통장 사본",
    "거래내역",
    "주민등록번호 앞자리",
    "카드번호와 유효기간",
    "계좌번호와 생년월일",
]

CODES = [
    "A1024",
    "B3817",
    "C5921",
    "D7048",
    "E8625",
    "F9136",
]


# ============================================================
# 템플릿
# - 총 60개 템플릿
# - 템플릿당 10개 → 약 600개 생성
# ============================================================

TEMPLATES = {
    "금융_대출": [
        "{institution}입니다. 우대금리 전환 심사 대상입니다. 확인을 위해 {document}을 문자로 보내주세요. 접수번호 {code}",
        "대출 이자를 낮출 수 있는 대상자로 확인됐습니다. 심사 진행을 위해 {document} 회신이 필요합니다. 관리번호 {code}",
        "{institution} 대환 상담팀입니다. 한도 조회를 위해 본인 확인 자료인 {document}을 답장으로 제출해주세요.",
        "기존 대출을 저금리 상품으로 변경할 수 있습니다. 오늘 중 {document}을 보내야 우대 조건이 유지됩니다.",
        "신용등급 조정 대상입니다. 빠른 처리를 위해 {document}을 담당자 문자로 회신해주세요.",
        "{institution} 특별 금융지원 안내입니다. 지원 가능 금액 확인을 위해 {document}을 보내주세요.",
    ],

    "계정_인증번호": [
        "계정 보안 확인 중입니다. 방금 전송된 여섯 자리 인증번호를 이 문자에 답장해주세요. 알림번호 {code}",
        "로그인 보호 절차가 진행 중입니다. 휴대전화로 받은 인증번호를 담당자에게 회신해주세요.",
        "비정상 접속이 감지됐습니다. 계정 잠금 해제를 위해 인증번호를 문자로 보내주세요.",
        "본인 확인이 완료되지 않았습니다. 수신한 인증 코드를 답장하면 계정 이용이 재개됩니다.",
        "보안 인증 절차가 변경되었습니다. 방금 받은 숫자 코드를 이 번호로 회신해주세요.",
        "계정 복구 신청이 접수됐습니다. 확인용 인증번호를 문자로 전달해주세요.",
    ],

    "채용_보증금": [
        "{institution} 채용팀입니다. 재택 장비 발송 전 보증금 {amount}을 먼저 납부해야 합니다.",
        "최종 합격을 축하드립니다. 업무용 장비 등록비 {amount}을 입금하면 출근 안내를 드립니다.",
        "교육 과정 참가가 확정됐습니다. 좌석 확보를 위해 오늘까지 {amount}을 납부해주세요.",
        "재택근무 키트 배송을 위해 예치금 {amount}이 필요합니다. 입금 후 답장해주세요.",
        "채용 절차 마지막 단계입니다. 사원증과 장비 제작 비용 {amount}을 선납해주세요.",
        "근무 배정을 위해 교육 보증금 {amount}을 개인 계좌로 보내주세요.",
    ],

    "채용_급여정보": [
        "{institution} 인사팀입니다. 급여 등록을 위해 {document}을 문자로 회신해주세요.",
        "입사 서류가 일부 누락됐습니다. 급여 지급을 위해 {document}을 이 번호로 보내주세요.",
        "급여 계좌 확인이 필요합니다. 은행명과 계좌번호, 주민번호 앞자리를 답장해주세요.",
        "근로계약 등록을 위해 신분증과 통장 사본을 휴대전화 문자로 제출해주세요.",
        "첫 급여 지급 전 계좌 인증이 필요합니다. {document}을 담당자에게 보내주세요.",
        "인사정보 등록을 위해 개인정보 서류인 {document} 회신이 필요합니다.",
    ],

    "학교_등록금": [
        "{institution}입니다. 등록금 처리가 누락됐습니다. 오늘까지 {amount}을 안내된 계좌로 보내주세요.",
        "수강 자격 유지 비용 {amount}이 미납 상태입니다. 납부하지 않으면 신청 내역이 취소됩니다.",
        "장학금 지급 전 행정 수수료 {amount}을 먼저 입금해야 합니다.",
        "학적 유지 확인을 위해 {amount} 납부가 필요합니다. 입금 후 문자로 알려주세요.",
        "수강신청 오류 복구 비용이 발생했습니다. 좌석 유지를 위해 {amount}을 납부해주세요.",
        "교육지원금 대상자로 선정됐습니다. 지급 처리비 {amount}을 먼저 보내주세요.",
    ],

    "학교_개인정보": [
        "{institution} 현장실습 담당자입니다. 지원금 지급을 위해 {document}을 문자로 보내주세요.",
        "실습생 등록 정보가 누락됐습니다. {document}을 담당자 휴대전화로 제출해주세요.",
        "장학금 계좌 등록을 위해 신분증 사진과 통장 사본을 답장으로 보내주세요.",
        "교육비 환급 처리를 위해 {document} 회신이 필요합니다.",
        "학생 본인 확인을 위해 주민번호 앞자리와 계좌번호를 문자로 제출해주세요.",
        "학사정보 오류 수정에 필요한 {document}을 이 번호로 보내주세요.",
    ],

    "의료_보험": [
        "미수령 보험금 {amount}이 확인됐습니다. 지급을 위해 인증번호를 답장해주세요.",
        "{institution}입니다. 진료비 환급 처리를 위해 {document}을 문자로 보내주세요.",
        "건강검진 대상자로 선정됐습니다. 예약 확정을 위해 보증금 {amount}을 납부해주세요.",
        "보험 환급금 지급이 보류됐습니다. 계좌 확인을 위해 {document}을 회신해주세요.",
        "병원비 과납금이 있습니다. 환불을 위해 은행명, 계좌번호, 생년월일을 보내주세요.",
        "무료 검진 예약이 접수됐습니다. 예약 취소 방지를 위해 {amount}을 먼저 입금해주세요.",
    ],

    "택배_개인정보": [
        "배송지 변경 요청이 접수됐습니다. 본인이 아니라면 주민번호 앞자리를 문자로 보내주세요.",
        "반품 환불을 위해 은행명과 계좌번호를 답장해주세요. 접수번호 {code}",
        "수취인 확인이 되지 않아 배송이 보류됐습니다. 생년월일과 주소를 문자로 회신해주세요.",
        "상품 환불 계좌 등록이 필요합니다. 계좌번호와 신분증 사진을 보내주세요.",
        "배송 정보 오류가 발견됐습니다. 본인 확인을 위해 {document}을 답장해주세요.",
        "반송 취소를 위해 수취인의 주민번호 앞자리와 계좌번호를 회신해주세요.",
    ],

    "중고거래": [
        "{item} 거래 보호를 위해 보증금 {amount}을 먼저 입금해야 정산이 진행됩니다.",
        "안전거래 수수료가 발생했습니다. 판매 완료를 위해 {amount}을 개인 계좌로 보내주세요.",
        "환불 처리를 위해 카드번호와 유효기간을 채팅으로 알려주세요.",
        "수수료 없이 거래하려고 합니다. 계좌번호를 알려주시면 바로 입금하겠습니다.",
        "구매 확정을 위해 판매자 인증비 {amount}을 먼저 납부해주세요.",
        "거래 오류로 결제가 보류됐습니다. 환불을 위해 {document}을 보내주세요.",
    ],

    "가족_지인": [
        "{relation}, 내 계정 인증번호가 네 번호로 갔어. 방금 받은 여섯 자리 숫자만 알려줘.",
        "{relation}, 급하게 결제해야 하는데 상품권 {amount}어치 사서 번호를 보내줄 수 있어?",
        "{name}아, 지갑을 잃어버려서 그런데 기사님 계좌로 {amount}만 바로 보내줘.",
        "{relation}, 휴대전화가 고장 나서 다른 번호로 연락해. 급한 송금이 있어서 도와줘.",
        "{name}아, 모임 계좌가 바뀌었어. 회비 {amount}을 새 계좌로 보내줘.",
        "{relation}, 온라인 결제가 안 돼. 대신 입금하고 인증번호도 알려줘.",
    ],
}


# ============================================================
# 문장 생성
# ============================================================

def fill_template(template: str) -> str:
    return template.format(
        institution=random.choice(INSTITUTIONS),
        name=random.choice(NAMES),
        relation=random.choice(RELATIONS),
        amount=random.choice(AMOUNTS),
        item=random.choice(ITEMS),
        document=random.choice(DOCUMENTS),
        code=random.choice(CODES),
    )


def build_synthetic_phishing() -> pd.DataFrame:
    rows = []
    row_index = 0

    for category, templates in TEMPLATES.items():
        for template_index, template in enumerate(templates):
            for sample_index in range(SAMPLES_PER_TEMPLATE):
                raw_text = fill_template(template)

                rows.append(
                    {
                        "row_id": (
                            f"HARD_PHISH_{row_index:05d}"
                        ),
                        "content": raw_text,
                        "class": 2,
                        "label": 1,
                        "text": preprocess_for_model(raw_text),
                        "structured_family": (
                            "synthetic_hard_phishing"
                        ),
                        "group_id": (
                            f"hard_phish_{category}_"
                            f"{template_index:02d}_"
                            f"{sample_index:02d}"
                        ),
                        "split": "train",
                        "is_synthetic": True,
                        "synthetic_type": (
                            f"hard_phishing_{category}"
                        ),
                    }
                )

                row_index += 1

    synthetic_df = pd.DataFrame(rows)

    # 동일한 문장 중복 제거
    synthetic_df = (
        synthetic_df
        .drop_duplicates(
            subset=["text"]
        )
        .sample(
            frac=1,
            random_state=SEED,
        )
        .reset_index(drop=True)
    )

    return synthetic_df


# ============================================================
# 기존 V2와 합치기
# ============================================================

def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"파일을 찾을 수 없습니다: {INPUT_PATH}"
        )

    train_v2 = pd.read_csv(
        INPUT_PATH,
        encoding="utf-8-sig",
    )

    synthetic_df = build_synthetic_phishing()

    all_columns = sorted(
        set(train_v2.columns)
        | set(synthetic_df.columns)
    )

    train_v2 = train_v2.reindex(
        columns=all_columns
    )

    synthetic_df = synthetic_df.reindex(
        columns=all_columns
    )

    train_v3 = pd.concat(
        [
            train_v2,
            synthetic_df,
        ],
        ignore_index=True,
    )

    train_v3 = (
        train_v3
        .sample(
            frac=1,
            random_state=SEED,
        )
        .reset_index(drop=True)
    )

    synthetic_df.to_csv(
        SYNTHETIC_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    train_v3.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    print("=" * 80)
    print("링크 없는 피싱 합성 데이터 생성 완료")
    print("=" * 80)

    print("\n기존 V2 수:", len(train_v2))
    print(
        "추가 피싱 데이터 수:",
        len(synthetic_df),
    )
    print("최종 V3 수:", len(train_v3))

    print("\n추가 데이터 유형 분포")
    print(
        synthetic_df[
            "synthetic_type"
        ]
        .value_counts()
        .sort_index()
    )

    print("\n최종 라벨 분포")
    print(
        train_v3["label"]
        .value_counts()
        .sort_index()
    )

    print("\n저장 위치")
    print(SYNTHETIC_PATH)
    print(OUTPUT_PATH)

    assert (
        synthetic_df["label"]
        .eq(1)
        .all()
    )

    assert (
        synthetic_df["split"]
        .eq("train")
        .all()
    )

    print(
        "\n추가 데이터는 피싱 label 1, "
        "train 전용: 확인 완료"
    )


if __name__ == "__main__":
    main()