"""
텍스트에서 숫자 추출
"""

import re

# 가격
def extract_price_from_title(title):
    """
    1. (17,800원 / 무배) → 17800
    2. (5,000원) → 5000
    3. 17,800원 → 17800
    4. 5만원 → 50000

    Returns:
        int: 가격 (원 단위)
        None: 가격 정보 없음
    """

    if not title:
        return None

    # 원화
    won_pattern = [
        r'\d{1,3}(?:,\d{3})+\s*원',  # 99,000원
        r'₩\s*\d{1,3}(?:,\d{3})+',  # ₩99,000
        r'\d{4,}\s*원',  # 99000원 (쉼표 없음)
    ]

    for pattern in won_pattern:
        match = re.search(pattern, title)
        if match:
            price_text = match.group(0)
            # 가격 범위 검증
        
    # 달러
    dollar_patterns = [
        r'\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?',  # $899, $1,299.99
        r'\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?\s*달러',  # 899달러
        r'\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?\s*USD',  # 899 USD
    ]

    for pattern in dollar_patterns:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            return match.group(0)
    # 엔화
    yen_patterns = [
        r'¥\s*\d{1,3}(?:,\d{3})+',  # ¥98,000
        r'\d{1,3}(?:,\d{3})+\s*엔',  # 98,000엔
        r'\d{1,3}(?:,\d{3})+\s*JPY',  # 98,000 JPY
    ]

    for pattern in yen_patterns:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            return match.group(0)
    
    # 유로
    euro_patterns = [
        r'€\s*\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?',  # €799.99
        r'\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?\s*유로',  # 799유로
        r'\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?\s*EUR',  # 799 EUR
    ]

    for pattern in euro_patterns:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            return match.group(0)

    # 무료 키워드 체크
    free_keywords = ['무료', '나눔', '공짜', 'free']
    if any(keyword in title.lower() for keyword in free_keywords):
        return 0

    # 가격정보 X
    return None


# 테스트
if __name__ == "__main__":
    test_cases = [
        ("삼성 갤럭시 99,000원", "99,000원"),
        ("아이폰 $899 직구", "$899"),
        ("카메라 ¥98,000", "¥98,000"),
        ("노트북 €799", "€799"),
        ("무료 나눔", "무료"),
        ("가격 문의", None),
    ]

    for title, expected in test_cases:
        result = extract_price_from_title(title)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{title}' → {result}")


# 배송비
def extract_shipping_fee_from_title(title, site):

    free_keywords = ['무료', '무배', '무료배송', '배송비무료']

    if "PPOMPPU" in site:
        # 패턴 (가격/배송비)
        pattern = r'\([\d,]+원\s*/\s*(.+?)\)'
        match = re.search(pattern, title)

        if not match:
            return None

        shipping_str = match.group(1).strip()

        # 무료 배송
        if any(keyword in shipping_str for keyword in free_keywords):
            return 0

        # 배송비 추출
        price_match = re.search(r'([\d,]+)원?', shipping_str)
        if price_match:
            return int(price_match.group(1).replace(',', ''))
        else:
            return None

    elif "RULIWEB" in site:
        # 무료배송
        if any(keyword in title for keyword in free_keywords):
            return 0
        else:
            return None

# 괄호 / 대괄호 제거
def extract_number_from_text(text):

    if not text:
        return 0

    # 괄호 제거
    text = re.sub(r'[\[\](){}]', '', text)

    # 숫자와 콤마만 추출
    numbers = re.findall(r'[\d,]+', text)

    if not numbers:
        return 0

    # 첫 번째 숫자 그룹 사용
    number_str = numbers[0].replace(',', '')

    try:
        return int(number_str)
    except:
        return 0