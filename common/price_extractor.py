"""
가격 추출 유틸리티 (공통)
"""

import re

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
