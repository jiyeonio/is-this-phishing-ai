from __future__ import annotations

import random
from pathlib import Path

import pandas as pd

from src.text_features import preprocess_for_model


# ============================================================
# 1. 기본 설정
# ============================================================

SEED = 42
N_PER_TEMPLATE = 12

random.seed(SEED)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

TRAIN_AUGMENTED_PATH = (
    PROCESSED_DIR
    / "train_augmented.csv"
)

HARD_NEGATIVE_PATH = (
    PROCESSED_DIR
    / "hard_negative_normal_train.csv"
)

TRAIN_AUGMENTED_V2_PATH = (
    PROCESSED_DIR
    / "train_augmented_v2.csv"
)


# ============================================================
# 2. 슬롯 데이터
# ============================================================

BANKS = [
    "새봄은행",
    "가온은행",
    "한빛은행",
    "우리금융",
    "다온저축은행",
]

CARDS = [
    "새봄카드",
    "가온카드",
    "한빛카드",
    "우리카드",
]

SCHOOLS = [
    "새봄대학교",
    "한빛대학교",
    "가온대학교",
    "다온대학교",
]

HOSPITALS = [
    "새봄의원",
    "한빛병원",
    "가온메디컬센터",
    "다온내과",
]

PUBLIC_ORGS = [
    "새봄구청",
    "한빛시청",
    "가온세무서",
    "다온행정복지센터",
]

MAIL_SERVICES = [
    "한빛메일",
    "새봄메일",
    "가온클라우드",
    "다온계정센터",
]

COMPANIES = [
    "새봄테크",
    "한빛솔루션",
    "가온시스템",
    "다온컴퍼니",
]

SHOPPING = [
    "새봄마켓",
    "한빛스토어",
    "가온몰",
    "다온샵",
]

NAMES = [
    "김서연",
    "이민수",
    "박지훈",
    "최하늘",
    "정수빈",
    "강민지",
    "윤도현",
    "한지우",
]

DATES = [
    "내일",
    "모레",
    "이번 주 금요일",
    "다음 주 월요일",
    "7월 22일",
    "7월 25일",
]

DEVICES = [
    "Windows PC",
    "iPhone",
    "Android 기기",
    "MacBook",
    "태블릿",
]

PRODUCTS = [
    "노트북",
    "의류",
    "생활용품",
    "도서",
    "전자제품",
    "운동화",
]

CATEGORIES = [
    "금융·카드",
    "계정·보안",
    "학교·교육",
    "의료·보험",
    "공공기관",
    "채용·업무",
    "중고거래·쇼핑",
    "가족·지인",
    "일상 요청",
    "택배·배송",
]


# ============================================================
# 3. 번호 생성
# ============================================================

def make_code(prefix: str, index: int) -> str:
    return f"{prefix}{index:05d}"


# ============================================================
# 4. 정상 하드 네거티브 템플릿
# - 외부 링크 입력 요구 없음
# - 인증번호 회신 요구 없음
# - 개인계좌 송금 요구 없음
# - 공식 앱/포털/고지서/직접 방문 안내 중심
# ============================================================

def build_templates() -> dict[str, list]:
    return {
        "금융·카드": [
            lambda i: (
                f"[{random.choice(BANKS)}] "
                f"대출 상담 예약이 {random.choice(DATES)}로 확정되었습니다. "
                f"변경은 공식 앱의 예약 메뉴에서 가능합니다. "
                f"알림번호는 {make_code('B', i)}입니다."
            ),
            lambda i: (
                f"[{random.choice(BANKS)}] "
                f"보안 강화를 위해 앱 업데이트가 필요합니다. "
                f"공식 앱스토어에서 기관명을 검색해 업데이트하세요. "
                f"안내번호는 {make_code('S', i)}입니다."
            ),
            lambda i: (
                f"[{random.choice(CARDS)}] "
                f"카드 재발급 신청이 정상 접수되었습니다. "
                f"배송 현황은 카드사 공식 앱에서 확인할 수 있습니다. "
                f"접수번호는 {make_code('C', i)}입니다."
            ),
            lambda i: (
                f"[{random.choice(CARDS)}] "
                f"해외 결제 차단 설정이 완료되었습니다. "
                f"설정 변경은 공식 앱의 보안 메뉴에서 가능합니다. "
                f"알림번호는 {make_code('F', i)}입니다."
            ),
        ],

        "계정·보안": [
            lambda i: (
                f"[{random.choice(MAIL_SERVICES)}] "
                f"{random.choice(DEVICES)}에서 새 로그인이 감지되었습니다. "
                f"본인이 아니라면 공식 앱의 보안 설정에서 "
                f"모든 기기를 로그아웃하세요. "
                f"알림번호는 {make_code('L', i)}입니다."
            ),
            lambda i: (
                f"[{random.choice(MAIL_SERVICES)}] "
                f"비밀번호 변경이 완료되었습니다. "
                f"본인이 변경하지 않았다면 공식 홈페이지를 직접 입력해 "
                f"보안 설정을 확인하세요. "
                f"알림번호는 {make_code('P', i)}입니다."
            ),
            lambda i: (
                f"[{random.choice(MAIL_SERVICES)}] "
                f"2단계 인증이 활성화되었습니다. "
                f"인증 설정은 공식 앱의 계정 메뉴에서만 변경할 수 있습니다. "
                f"안내번호는 {make_code('A', i)}입니다."
            ),
            lambda i: (
                f"[{random.choice(MAIL_SERVICES)}] "
                f"저장 공간 사용량이 90%를 넘었습니다. "
                f"정리는 공식 앱의 저장 공간 메뉴에서 진행하세요. "
                f"알림번호는 {make_code('D', i)}입니다."
            ),
        ],

        "학교·교육": [
            lambda i: (
                f"[{random.choice(SCHOOLS)}] "
                f"등록금 납부 기간은 {random.choice(DATES)}까지입니다. "
                f"고지서의 학교 명의 가상계좌를 확인하세요. "
                f"안내번호는 {make_code('R', i)}입니다."
            ),
            lambda i: (
                f"[{random.choice(SCHOOLS)}] "
                f"{random.choice(NAMES)} 학생의 장학금 신청이 접수되었습니다. "
                f"결과는 학교 포털 장학 메뉴에서 확인하세요. "
                f"안내번호는 {make_code('J', i)}입니다."
            ),
            lambda i: (
                f"[{random.choice(SCHOOLS)}] "
                f"수강신청 정정 기간은 {random.choice(DATES)}까지입니다. "
                f"변경은 학교 포털에서 직접 진행하세요. "
                f"안내번호는 {make_code('U', i)}입니다."
            ),
            lambda i: (
                f"[{random.choice(SCHOOLS)}] "
                f"현장실습 일정이 확정되었습니다. "
                f"세부 내용은 학교 포털 공지사항에서 확인하세요. "
                f"안내번호는 {make_code('I', i)}입니다."
            ),
        ],

        "의료·보험": [
            lambda i: (
                f"[{random.choice(HOSPITALS)}] "
                f"검사 결과가 등록되었습니다. "
                f"개인정보 보호를 위해 병원 앱 로그인 후 확인할 수 있습니다. "
                f"접수번호는 {make_code('M', i)}입니다."
            ),
            lambda i: (
                f"[{random.choice(HOSPITALS)}] "
                f"진료 예약이 {random.choice(DATES)}로 확정되었습니다. "
                f"변경은 병원 대표번호 또는 공식 앱에서 가능합니다. "
                f"예약번호는 {make_code('H', i)}입니다."
            ),
            lambda i: (
                f"[{random.choice(HOSPITALS)}] "
                f"건강검진 대상자 안내입니다. "
                f"검진 항목은 병원 공식 홈페이지에서 확인하세요. "
                f"안내번호는 {make_code('G', i)}입니다."
            ),
            lambda i: (
                f"[새봄보험] 보험금 청구 서류가 정상 접수되었습니다. "
                f"진행 상태는 보험사 공식 앱에서 확인할 수 있습니다. "
                f"접수번호는 {make_code('Q', i)}입니다."
            ),
        ],

        "공공기관": [
            lambda i: (
                f"[{random.choice(PUBLIC_ORGS)}] "
                f"민원 서류 발급이 완료되었습니다. "
                f"정부24 또는 기관 공식 홈페이지에서 확인하세요. "
                f"문서번호는 {make_code('V', i)}입니다."
            ),
            lambda i: (
                f"[{random.choice(PUBLIC_ORGS)}] "
                f"지방세 납부 안내입니다. "
                f"고지서 또는 공식 세금 납부 서비스를 이용하세요. "
                f"안내번호는 {make_code('T', i)}입니다."
            ),
            lambda i: (
                f"[새봄교통센터] 교통 과태료 조회 결과가 등록되었습니다. "
                f"조회는 정부 공식 교통민원 서비스에서 가능합니다. "
                f"안내번호는 {make_code('K', i)}입니다."
            ),
            lambda i: (
                f"[새봄법원] 등기 문서가 발송되었습니다. "
                f"문서 확인은 법원 공식 사이트 또는 우편물을 이용하세요. "
                f"사건번호는 {make_code('E', i)}입니다."
            ),
        ],

        "채용·업무": [
            lambda i: (
                f"[{random.choice(COMPANIES)}] "
                f"온라인 면접 일정이 {random.choice(DATES)}로 확정되었습니다. "
                f"접속 정보는 채용 사이트 내 지원 현황에서 확인하세요. "
                f"안내번호는 {make_code('W', i)}입니다."
            ),
            lambda i: (
                f"[{random.choice(COMPANIES)}] "
                f"최종 합격 안내가 등록되었습니다. "
                f"결과는 공식 채용 사이트에서 확인하세요. "
                f"지원번호는 {make_code('Y', i)}입니다."
            ),
            lambda i: (
                f"[{random.choice(COMPANIES)}] "
                f"급여계좌 등록 기간은 {random.choice(DATES)}까지입니다. "
                f"사내 인사시스템에서 직접 등록하세요. "
                f"사번 확인번호는 {make_code('N', i)}입니다."
            ),
            lambda i: (
                f"[{random.choice(COMPANIES)}] "
                f"업무용 장비 수령 일정이 확정되었습니다. "
                f"장비 보증금이나 개인계좌 송금은 요구하지 않습니다. "
                f"안내번호는 {make_code('X', i)}입니다."
            ),
        ],

        "중고거래·쇼핑": [
            lambda i: (
                f"[{random.choice(SHOPPING)}] "
                f"{random.choice(PRODUCTS)} 주문의 환불 처리가 완료되었습니다. "
                f"환불 내역은 공식 앱 주문 메뉴에서 확인하세요. "
                f"주문번호는 {make_code('O', i)}입니다."
            ),
            lambda i: (
                f"[{random.choice(SHOPPING)}] "
                f"판매대금 정산이 완료되었습니다. "
                f"정산 내역은 공식 판매자 센터에서 확인하세요. "
                f"정산번호는 {make_code('Z', i)}입니다."
            ),
            lambda i: (
                f"[{random.choice(SHOPPING)}] "
                f"송장번호 등록이 완료되었습니다. "
                f"배송조회는 공식 앱 주문내역에서 가능합니다. "
                f"주문번호는 {make_code('D', i)}입니다."
            ),
            lambda i: (
                f"[중고마켓] 직거래 일정이 {random.choice(DATES)}로 등록되었습니다. "
                f"안전한 공공장소에서 거래하고 선입금은 피하세요. "
                f"거래번호는 {make_code('C', i)}입니다."
            ),
        ],

        "가족·지인": [
            lambda i: (
                f"{random.choice(NAMES)}야, 휴대폰 수리를 맡겨서 "
                f"잠시 연락이 늦을 수 있어. 급한 일은 집 전화로 연락해 줘."
            ),
            lambda i: (
                f"오늘 병원비는 이미 카드로 결제했어. "
                f"따로 송금할 필요 없고 저녁에 영수증 보여줄게."
            ),
            lambda i: (
                f"상품권은 생일 선물로 준비해 뒀어. "
                f"인증번호는 누구에게도 보내지 말고 직접 등록해."
            ),
            lambda i: (
                f"인증번호 문자가 오더라도 나한테 보내지 마. "
                f"본인이 요청한 경우에만 공식 앱에 직접 입력해야 해."
            ),
        ],

        "일상 요청": [
            lambda i: (
                f"공연 환불은 예매처 공식 앱에서 신청했어. "
                f"처리되면 결제했던 카드로 자동 환불된대."
            ),
            lambda i: (
                f"이번 모임 회비는 지난번에 걷은 금액으로 충분해서 "
                f"추가 송금은 안 해도 돼."
            ),
            lambda i: (
                f"사진은 단체 채팅방 앨범에 올려뒀어. "
                f"모르는 링크가 오면 열지 말고 채팅방에서 확인해."
            ),
            lambda i: (
                f"파일은 회사 공유 드라이브에 올렸어. "
                f"개인 메일 링크 말고 사내 계정으로 확인해 줘."
            ),
        ],

        "택배·배송": [
            lambda i: (
                f"[새봄택배] 배송지 변경 신청이 접수되었습니다. "
                f"변경 내용은 공식 앱 주문내역에서 확인하세요. "
                f"접수번호는 {make_code('P', i)}입니다."
            ),
            lambda i: (
                f"[한빛물류] 반품 수거가 {random.choice(DATES)}로 예약되었습니다. "
                f"기사 방문 전 상품을 포장해 주세요. "
                f"접수번호는 {make_code('R', i)}입니다."
            ),
            lambda i: (
                f"[가온택배] 배송이 완료되었습니다. "
                f"배송 위치는 공식 앱의 배송조회 메뉴에서 확인할 수 있습니다. "
                f"운송장번호는 {make_code('L', i)}입니다."
            ),
            lambda i: (
                f"[다온배송] 배송이 하루 지연될 예정입니다. "
                f"추가 배송비나 개인정보 입력은 요구하지 않습니다. "
                f"안내번호는 {make_code('S', i)}입니다."
            ),
        ],
    }


# ============================================================
# 5. 데이터 생성
# ============================================================

def build_hard_negative_data() -> pd.DataFrame:
    templates_by_category = build_templates()

    rows = []
    row_index = 0

    for category in CATEGORIES:
        category_templates = (
            templates_by_category[category]
        )

        for template_index, template_fn in enumerate(
            category_templates
        ):
            for repeat_index in range(
                N_PER_TEMPLATE
            ):
                raw_text = template_fn(
                    row_index
                )

                rows.append(
                    {
                        "row_id": (
                            f"HARD_NEG_{row_index:05d}"
                        ),
                        "content": raw_text,
                        "class": 3,
                        "label": 0,
                        "text": preprocess_for_model(
                            raw_text
                        ),
                        "structured_family": (
                            f"hard_negative_{category}"
                        ),
                        "group_id": (
                            f"hard_negative_"
                            f"{category}_"
                            f"{template_index}_"
                            f"{repeat_index}"
                        ),
                        "split": "train",
                        "is_synthetic": True,
                        "synthetic_type": (
                            f"hard_negative_{category}"
                        ),
                    }
                )

                row_index += 1

    hard_negative_df = pd.DataFrame(
        rows
    )

    hard_negative_df = (
        hard_negative_df
        .drop_duplicates(
            subset=["text"]
        )
        .sample(
            frac=1,
            random_state=SEED,
        )
        .reset_index(drop=True)
    )

    return hard_negative_df


# ============================================================
# 6. 기존 학습 데이터와 결합
# ============================================================

def main() -> None:
    if not TRAIN_AUGMENTED_PATH.exists():
        raise FileNotFoundError(
            f"기존 증강 학습 파일이 없습니다: "
            f"{TRAIN_AUGMENTED_PATH}"
        )

    train_df = pd.read_csv(
        TRAIN_AUGMENTED_PATH,
        encoding="utf-8-sig",
    )

    hard_negative_df = (
        build_hard_negative_data()
    )

    all_columns = sorted(
        set(train_df.columns)
        | set(hard_negative_df.columns)
    )

    train_df = train_df.reindex(
        columns=all_columns
    )

    hard_negative_df = (
        hard_negative_df.reindex(
            columns=all_columns
        )
    )

    train_v2 = pd.concat(
        [
            train_df,
            hard_negative_df,
        ],
        ignore_index=True,
    )

    train_v2 = (
        train_v2
        .sample(
            frac=1,
            random_state=SEED,
        )
        .reset_index(drop=True)
    )

    hard_negative_df.to_csv(
        HARD_NEGATIVE_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    train_v2.to_csv(
        TRAIN_AUGMENTED_V2_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    print("=" * 80)
    print("정상 하드 네거티브 생성 완료")
    print("=" * 80)

    print("\n기존 train 수:", len(train_df))
    print(
        "추가 정상 하드 네거티브 수:",
        len(hard_negative_df),
    )
    print("최종 train v2 수:", len(train_v2))

    print("\n추가 데이터 시나리오 분포")
    print(
        hard_negative_df[
            "synthetic_type"
        ]
        .value_counts()
    )

    print("\n최종 label 분포")
    print(
        train_v2["label"]
        .value_counts()
        .sort_index()
    )

    print("\n저장 위치")
    print(HARD_NEGATIVE_PATH)
    print(TRAIN_AUGMENTED_V2_PATH)

    assert hard_negative_df[
        "label"
    ].eq(0).all()

    assert hard_negative_df[
        "split"
    ].eq("train").all()

    print("\n추가 데이터는 정상 label 0, train 전용: 확인 완료")


if __name__ == "__main__":
    main()