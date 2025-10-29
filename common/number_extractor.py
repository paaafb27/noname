"""
텍스트에서 숫자 추출
"""

import re


# 가격
def extract_price_from_text(title):
    """
    케이스:
    - (6,980원/무배) → 6980
    - 8,910원 → 8910
    - 10850원 무배 → 10850
    - 12.3만원 → 123000
    - 5,090원 → 5090
    - ￦ 376,650 (KRW) → 376650
    - ￦69920 → 69920
    """

    if not title:
        return None

        # 만원 단위: 12.3만원, 5만원
        man_pattern = r'([0-9]+\.?[0-9]*)\s*만\s*원'
        man_match = re.search(man_pattern, title)
        if man_match:
            try:
                return int(float(man_match.group(1)) * 10000)
            except ValueError:
                pass

        # 원화 기호: ￦69920, ₩99,000
        won_symbol_patterns = [
            r'[￦₩]\s*([0-9,]+)',
        ]
        for pattern in won_symbol_patterns:
            match = re.search(pattern, title)
            if match:
                price_text = match.group(1).replace(',', '')
                try:
                    price = int(price_text)
                    if 100 <= price <= 100000000:
                        return price
                except ValueError:
                    pass

        # 콤마 + 원: 8,910원, 139,000원
        comma_won_pattern = r'([0-9,]+)\s*원'
        comma_won_match = re.search(comma_won_pattern, title)
        if comma_won_match:
            price_text = comma_won_match.group(1).replace(',', '')
            try:
                price = int(price_text)
                if 100 <= price <= 100000000:
                    return price
            except ValueError:
                pass

        # 순수 숫자 (4자리 이상): 69920
        pure_number_pattern = r'(?<!\d)([0-9]{4,})(?!\d)'
        pure_number_match = re.search(pure_number_pattern, title)
        if pure_number_match:
            try:
                price = int(pure_number_match.group(1))
                if 1000 <= price <= 100000000:
                    return price
            except ValueError:
                pass

        # 달러
        dollar_patterns = [
            r'\$\s*([0-9,]+(?:\.[0-9]{1,2})?)',
            r'([0-9,]+(?:\.[0-9]{1,2})?)\s*달러',
            r'([0-9,]+(?:\.[0-9]{1,2})?)\s*USD',
        ]
        for pattern in dollar_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return match.group(0)  # 문자열 그대로 반환

        # 엔화
        yen_patterns = [
            r'¥\s*([0-9,]+)',
            r'([0-9,]+)\s*엔',
            r'([0-9,]+)\s*JPY',
        ]
        for pattern in yen_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return match.group(0)  # 문자열 그대로 반환

        # 유로
        euro_patterns = [
            r'€\s*([0-9,]+(?:\.[0-9]{1,2})?)',
            r'([0-9,]+(?:\.[0-9]{1,2})?)\s*유로',
            r'([0-9,]+(?:\.[0-9]{1,2})?)\s*EUR',
        ]
        for pattern in euro_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return match.group(0)  # 문자열 그대로 반환

        # 무료 키워드
        free_keywords = ['무료', '나눔', '공짜', 'free']
        if any(keyword in title.lower() for keyword in free_keywords):
            if '무료' in title and '원' not in title:
                return None

        return None


# 배송비
def extract_shipping_fee(target_text):
    """
    제목에서 배송비 추출 (공통)
    """

    if not target_text:
        return None

    free_keywords = ['무료', '무배', '무료배송', '배송비무료', '0', '공짜']

    # 1. 무료배송 키워드
    if any(keyword in target_text for keyword in free_keywords):
        return "무료"

    # 2. 배송비 2500원
    shipping_pattern = r'배송비?\s*[:：]?\s*([0-9,]+)원?'
    shipping_match = re.search(shipping_pattern, target_text)
    if shipping_match:
        fee = int(shipping_match.group(1).replace(',', ''))
        if fee == 0:
            return "무료배송"
        return f"{fee:,}원"

    return None


def format_price(price):
    """
    가격을 표시용 문자열로 포맷팅

    Args:
        price (int): 가격 숫자

    Returns:
        str: "8,910" 형태
    """
    if price is None or price == 0:
        return None

    if isinstance(price, str):
        return price  # 외화는 그대로

    return f"{price:,}"


def clean_title(title):
    """
    제목 끝의 [댓글수] 또는 (댓글수) 제거
    """
    if not title:
        return title

    # [숫자] 제거
    cleaned = re.sub(r'\s*\[\d+\]\s*$', '', title)

    # (숫자) 제거
    cleaned = re.sub(r'\s*\(\d+\)\s*$', '', cleaned)

    return cleaned.strip()


def extract_comment_count_from_title(title):
    """
    제목에서 댓글수 추출
    """
    if not title:
        return 0

    # [숫자] 또는 (숫자) 패턴
    patterns = [
        r'\[(\d+)\]\s*$',
        r'\((\d+)\)\s*$',
    ]

    for pattern in patterns:
        match = re.search(pattern, title)
        if match:
            return int(match.group(1))

    return 0

# 괄호 / 대괄호 제거
def extract_number_from_text(text):
    if not text:
        return 0

    text = str(text).strip()

    # 괄호 제거
    text = re.sub(r'[\[\](){}]', '', text)

    # 숫자와 콤마만 추출
    numbers = re.findall(r'[\d,]+', text)

    if not numbers:
        return 0

    # 첫 번째 숫자 그룹 사용
    number_str = numbers[0].replace(',', '')

    if number_str:
        return int(number_str)

    return 0


# ========== 테스트 ==========
if __name__ == "__main__":
    print("=" * 100)
    print("공통 가격 추출 테스트")
    print("=" * 100)

    test_cases = [
        # 원화
        "오늘의집 대추방울토마토 8,910원",
        "청소기 ￦69920",
        "헤드폰 12.3만원",
        "TV 139,000",

        # 외화 (직구)
        "아이폰 $899 직구",
        "카메라 ¥98,000",
        "노트북 €799",

        # 댓글수 포함
        "상품명 8,910원 [15]",
        "상품명 (23)",
    ]

    for title in test_cases:
        price = extract_price_from_text(title)
        cleaned = clean_title(title)
        comment = extract_comment_count_from_title(title)

        print(f"\n원본: {title}")
        print(f"정리: {cleaned}")
        print(f"가격: {format_price(price)}")
        print(f"댓글: {comment}")
        print("-" * 100)