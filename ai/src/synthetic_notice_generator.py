# ============================================================
# synthetic_notice_generator.py
# 정상 기관/택배 안내 문자 <-> 사칭 스미싱 "대조쌍" 합성 생성기
#
# 목적:
#   - 정상 기관 공지 family를 5종 -> 25종+ 로 다양화 (한진 오탐 근본 해결)
#   - 정상/사칭을 "같은 본문 골격 + 다른 URL/번호"로 만들어
#     모델이 본문 모양이 아니라 URL/발신정보 신호를 학습하게 함
#
# 철칙:
#   - 합성 데이터는 TRAIN 에만 넣는다. val/test 는 실제 held-out family 유지.
#   - 여기 mask_for_model() 을 실데이터 전처리에도 동일하게 적용해야 함
#     (기존 평평한 [URL] 마스킹을 이 방식으로 교체).
# ============================================================

import re
import random
import unicodedata
import pandas as pd

SEED = 42
rng = random.Random(SEED)


# ============================================================
# 1. 발신사 레지스트리
#    (name, official_domain, official_number, category)
#    -> 실데이터에서 mine_real_domains() 로 보강 가능
# ============================================================

# 학습 데이터에 이미 있던 5종 (참고용, 골격 시드로 사용)
KNOWN_SENDERS = [
    ("CJ대한통운", "cjlogistics.com", "1588-1255", "delivery"),
    ("우체국택배", "epost.go.kr",     "1588-1300", "delivery"),
    ("쿠팡",       "coupang.com",     "1577-7011", "delivery"),
    ("SLX택배",    "slx.co.kr",       "1600-2882", "delivery"),
    ("한진택배",   "hanjin.com",      "1588-0011", "delivery"),
]

# 학습에 없던 NOVEL 발신사 (일반화 학습용 - 이게 한진류 오탐을 없앰)
NOVEL_SENDERS = [
    ("롯데택배",     "lotteglogis.com", "1588-2121", "delivery"),
    ("로젠택배",     "ilogen.com",      "1588-9988", "delivery"),
    ("경동택배",     "kdexp.com",       "1899-5368", "delivery"),
    ("대신택배",     "ds3211.co.kr",    "1522-8783", "delivery"),
    ("GS Postbox",   "gspostbox.com",   "1577-1287", "delivery"),
    ("KB국민카드",   "kbcard.com",      "1588-1688", "card"),
    ("신한카드",     "shinhancard.com", "1544-7000", "card"),
    ("삼성카드",     "samsungcard.com", "1588-8700", "card"),
    ("현대카드",     "hyundaicard.com", "1577-6000", "card"),
    ("KB국민은행",   "kbstar.com",      "1588-9999", "bank"),
    ("신한은행",     "shinhan.com",     "1599-8000", "bank"),
    ("우리은행",     "wooribank.com",   "1588-5000", "bank"),
    ("카카오뱅크",   "kakaobank.com",   "1599-3333", "bank"),
    ("토스",         "toss.im",         "1599-4905", "bank"),
    ("배달의민족",   "baemin.com",      "1600-0987", "shopping"),
    ("11번가",       "11st.co.kr",      "1599-6001", "shopping"),
    ("G마켓",        "gmarket.co.kr",   "1566-5701", "shopping"),
    ("국민건강보험", "nhis.or.kr",      "1577-1000", "gov"),
    ("국세청",       "hometax.go.kr",   "126",       "gov"),
    ("도로교통공단", "koroad.or.kr",    "1577-1120", "gov"),
    ("SK텔레콤",     "tworld.co.kr",    "114",       "telecom"),
    ("KT",           "kt.com",          "100",       "telecom"),
]

ALL_SENDERS = KNOWN_SENDERS + NOVEL_SENDERS


# ============================================================
# 2. 사칭용 재료 (스미싱 쪽 URL/번호)
# ============================================================

SHORTENERS = [
    "me2.do", "bit.ly", "han.gl", "url.kr", "buly.kr", "vo.la",
    "abit.ly", "c11.kr", "muz.so", "tuney.kr",
]

# 정상 도메인을 살짝 비튼 가짜 도메인 (typosquatting)
def make_spoof_domain():
    style = rng.random()
    if style < 0.45:
        return rng.choice(SHORTENERS)
    if style < 0.75:
        # 이상한 TLD
        base = rng.choice(["cj-delivery", "epost-kr", "coupang-info",
                           "kb-card", "shinhan-secure", "gov-notice",
                           "parcel-check", "delivery-kr"])
        tld = rng.choice([".xyz", ".top", ".cc", ".vip", ".click", ".buzz", ".shop"])
        return base + tld
    # 랜덤 영숫자 도메인
    rand = "".join(rng.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(rng.randint(6, 10)))
    return rand + rng.choice([".com", ".net", ".xyz", ".top"])

FOREIGN_PREFIXES = ["+63", "+84", "+86", "+7", "+380", "+1", "+81"]

def make_foreign_phone():
    return rng.choice(FOREIGN_PREFIXES) + "-" + "-".join(
        "".join(rng.choice("0123456789") for _ in range(4)) for _ in range(2)
    )

def make_burner_mobile():
    # 국내 대포폰처럼 보이는 랜덤 휴대폰
    return "010-" + "".join(rng.choice("0123456789") for _ in range(4)) + "-" + \
           "".join(rng.choice("0123456789") for _ in range(4))


# ============================================================
# 3. 슬롯 풀 (mine_slot_pools() 로 실데이터에서 덮어쓸 수 있음)
# ============================================================

NAME_POOL = ["김철수", "이영희", "박민수", "정하늘", "윤지수", "오준혁",
             "송하나", "강도윤", "최서연", "임재현", "한지민", "조은우"]

TIME_POOL = ["07:00~09:00", "09:00~11:00", "11:00~13:00", "14:00~16:00",
             "16:00~18:00", "18:00~20:00", "20:00~22:00", "22:00~23:00"]

PRODUCT_POOL = ["의류", "생활용품", "도서", "전자제품", "화장품", "식품",
                "스마트워치", "무선이어폰", "운동화", "가방", "주방용품"]

def make_amount():
    return f"{rng.randint(1, 990) * 1000:,}원"

def make_tracking_code():
    return "".join(rng.choice("0123456789") for _ in range(rng.randint(10, 12)))


# ============================================================
# 4. 골격 뱅크 (실제 관측된 포맷 기반)
#    «SENDER» «NAME» «TIME» «URL» «PHONE» «CODE» «PRODUCT» «AMOUNT»
#    -> 플레이스홀더는 sentinel 문자, .format 안 씀 (본문 { } 충돌 방지)
# ============================================================

SKELETONS = {
    "delivery": [
        "[Web발신][«SENDER» 배송완료] «NAME» 고객님의 상품이 배송 완료되었습니다. 확인 «URL»",
        "«NAME» 고객님께서 주문하신 상품을 배송완료 하였습니다. «SENDER» 택배를 이용해주셔서 감사합니다. 조회 «URL»",
        "[«SENDER»] 상품 집하 안내 안녕하세요 «NAME» 고객님. «SENDER»입니다. 오늘 «TIME» 상품이 집하될 예정입니다. 운송장 «CODE» 조회 «URL» 문의 «PHONE»",
        "[Web발신] [«SENDER»] «PRODUCT» 오늘 «TIME» 도착예정입니다. 배송조회 «URL»",
        "(«SENDER» 배달완료) «NAME» 고객님! «SENDER»입니다. 주문하신 «PRODUCT» 배달완료 되었습니다. 조회 «URL»",
        "[«SENDER»] «NAME» 고객님, 안녕하세요. «SENDER» 입니다. 주문하신 «PRODUCT» 상품이 오늘 «TIME» 배송 예정입니다. «URL»",
    ],
    "card": [
        "[«SENDER»] «NAME»님 «AMOUNT» 승인 «TIME» 정상 승인되었습니다. 본인 아닐 시 «PHONE»",
        "[Web발신][«SENDER»] «NAME»님 해외 «AMOUNT» 승인 완료. 본인 미사용시 즉시 «URL» 확인",
        "[«SENDER»] «NAME» 고객님 «AMOUNT» 결제 안내드립니다. 상세내역 «URL»",
    ],
    "bank": [
        "[«SENDER»] «NAME»님 계좌로 «AMOUNT» 입금되었습니다. 거래내역 «URL»",
        "[Web발신][«SENDER»] «NAME» 고객님 이체 «AMOUNT» 완료. 본인 확인 «URL» 문의 «PHONE»",
        "[«SENDER»] «NAME»님 보안 인증이 필요합니다. «URL» 접속 후 진행해 주세요.",
    ],
    "shopping": [
        "[«SENDER»] «NAME»님 주문하신 «PRODUCT» 결제가 완료되었습니다. 주문조회 «URL»",
        "[Web발신][«SENDER»] «NAME» 고객님 «AMOUNT» 결제 완료. 취소는 «URL»",
    ],
    "gov": [
        "[«SENDER»] «NAME»님 안내문이 발송되었습니다. 확인 «URL» 문의 «PHONE»",
        "[Web발신][«SENDER»] «NAME» 귀하 «TIME» 관련 안내드립니다. 자세히 «URL»",
    ],
    "telecom": [
        "[«SENDER»] «NAME»님 «AMOUNT» 요금 안내입니다. 상세 «URL»",
        "[Web발신][«SENDER»] «NAME» 고객님 멤버십 안내 «URL» 문의 «PHONE»",
    ],
}


def fill_skeleton(skeleton, sender, is_spoof):
    """sentinel 치환. is_spoof=True 면 URL/PHONE 을 사칭 재료로."""
    name, domain, phone, category = sender

    if is_spoof:
        url = "https://" + make_spoof_domain() + "/" + rng.choice(["track", "chk", "info", "id" + make_tracking_code()])
        phone_val = make_foreign_phone() if rng.random() < 0.5 else make_burner_mobile()
    else:
        url = "https://" + domain + "/" + rng.choice(["track", "mypage", "order", "notice"])
        phone_val = phone

    text = skeleton
    text = text.replace("«SENDER»", name)
    text = text.replace("«NAME»", rng.choice(NAME_POOL))
    text = text.replace("«TIME»", rng.choice(TIME_POOL))
    text = text.replace("«PRODUCT»", rng.choice(PRODUCT_POOL))
    text = text.replace("«AMOUNT»", make_amount())
    text = text.replace("«CODE»", make_tracking_code())
    text = text.replace("«URL»", url)
    text = text.replace("«PHONE»", phone_val)
    return text


# ============================================================
# 5. 모델 입력용 마스킹 (실데이터 전처리에도 똑같이 써야 함!)
#    URL 을 평평한 [URL] 로 죽이지 않고 위험 신호로 분류
# ============================================================

OFFICIAL_DOMAINS = {d for _, d, _, _ in ALL_SENDERS}
OFFICIAL_NUMBERS = {re.sub(r"\D", "", p) for _, _, p, _ in ALL_SENDERS}

URL_RE = re.compile(r"(?i)\b(?:https?://|www\.)[^\s]+|\b(?:[a-z0-9-]+\.)+[a-z]{2,}(?:/[^\s]*)?")
PHONE_RE = re.compile(r"(?<!\d)(?:\+\d{1,3}[-\s]?)?0?\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4}(?!\d)")

def _host_of(url):
    host = re.sub(r"(?i)^https?://", "", url).split("/")[0].lower()
    return host.replace("www.", "")

def classify_url(url):
    host = _host_of(url)
    # 접미사 매칭: track.hanjin.com, epost.go.kr(.go.kr 2단계) 모두 정확히 처리
    if any(host == d or host.endswith("." + d) for d in OFFICIAL_DOMAINS):
        return " [URL_OFFICIAL] "
    if any(host == s or host.endswith("." + s) for s in SHORTENERS):
        return " [URL_SHORTENER] "
    return " [URL_SUSPICIOUS] "

def classify_phone(num):
    digits = re.sub(r"\D", "", num)
    if num.strip().startswith("+") and not digits.startswith("82"):
        return " [PHONE_FOREIGN] "
    if digits in OFFICIAL_NUMBERS:
        return " [PHONE_OFFICIAL] "
    if digits.startswith("010"):
        return " [PHONE_MOBILE] "
    if re.match(r"^(1[0-9]{3}|15|16|18)", digits):
        return " [PHONE_OFFICIAL] "  # 15xx/16xx/18xx 대표번호
    return " [PHONE_MOBILE] "

def mask_for_model(text):
    text = unicodedata.normalize("NFKC", str(text))
    text = text.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    # URL 먼저 (전화 정규식과 겹치지 않게)
    text = URL_RE.sub(lambda m: classify_url(m.group(0)), text)
    text = PHONE_RE.sub(lambda m: classify_phone(m.group(0)), text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ============================================================
# 6. 실데이터에서 재료 보강 (옵션, 있으면 현실성 ↑)
# ============================================================

def mine_slot_pools(clean_df):
    """실데이터 정상 문자에서 이름/시간 슬롯을 추가 수집."""
    global NAME_POOL, TIME_POOL
    normal = clean_df.loc[clean_df["label"] == 0, "content"].astype(str)
    names = set()
    for t in normal:
        for m in re.findall(r"([가-힣]{2,4})\s*(?:고객님|회원님|님)", t):
            names.add(m)
    times = set(re.findall(r"\d{1,2}:\d{2}\s*~\s*\d{1,2}:\d{2}", " ".join(normal.tolist())))
    if names:
        NAME_POOL = sorted(names)[:200]
    if times:
        TIME_POOL = sorted(times)[:100]
    print(f"[mine] 이름 슬롯 {len(NAME_POOL)}개, 시간 슬롯 {len(TIME_POOL)}개")


# ============================================================
# 7. 생성 메인
# ============================================================

def generate_synthetic(
    n_per_skeleton=40,
    spoof_ratio=0.5,
    use_novel_only_for_legit=False,
):
    """
    각 (카테고리 골격) 마다 정상 n개 + 사칭 n*spoof_ratio개 생성.
    반환: DataFrame[content, text, label, structured_family, is_synthetic]
      - content: 원문(비마스킹)  text: 모델 입력용 마스킹 결과
    """
    rows = []
    senders_by_cat = {}
    for s in ALL_SENDERS:
        senders_by_cat.setdefault(s[3], []).append(s)

    legit_senders_by_cat = {}
    for s in (NOVEL_SENDERS if use_novel_only_for_legit else ALL_SENDERS):
        legit_senders_by_cat.setdefault(s[3], []).append(s)

    for category, skeleton_list in SKELETONS.items():
        legit_pool = legit_senders_by_cat.get(category, [])
        spoof_pool = senders_by_cat.get(category, [])
        if not legit_pool or not spoof_pool:
            continue

        for skeleton in skeleton_list:
            # 정상
            for _ in range(n_per_skeleton):
                sender = rng.choice(legit_pool)
                raw = fill_skeleton(skeleton, sender, is_spoof=False)
                rows.append({
                    "content": raw,
                    "text": mask_for_model(raw),
                    "label": 0,
                    "structured_family": f"synth_{category}",
                    "is_synthetic": True,
                })
            # 사칭 (같은 골격, 나쁜 URL/번호)
            for _ in range(int(n_per_skeleton * spoof_ratio)):
                sender = rng.choice(spoof_pool)
                raw = fill_skeleton(skeleton, sender, is_spoof=True)
                rows.append({
                    "content": raw,
                    "text": mask_for_model(raw),
                    "label": 1,
                    "structured_family": f"synth_{category}_spoof",
                    "is_synthetic": True,
                })

    df = pd.DataFrame(rows)
    # 합성 내부 중복 제거
    df = df.drop_duplicates(subset=["text"]).reset_index(drop=True)
    return df


# ============================================================
# 8. 노트북 사용 예시 (주석 해제해서 셀에서 실행)
# ============================================================
if __name__ == "__main__":
    # mine_slot_pools(clean_df)   # 실데이터 있으면 먼저 호출
    synth = generate_synthetic(n_per_skeleton=40, spoof_ratio=0.5)
    print("합성 데이터:", synth.shape)
    print(synth["label"].value_counts())
    print(synth["structured_family"].value_counts())
    print("\n--- 정상 예시 ---")
    for _, r in synth[synth.label == 0].head(3).iterrows():
        print("원문 :", r["content"])
        print("마스킹:", r["text"], "\n")
    print("--- 사칭 예시 (같은 골격) ---")
    for _, r in synth[synth.label == 1].head(3).iterrows():
        print("원문 :", r["content"])
        print("마스킹:", r["text"], "\n")
