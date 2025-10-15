"""
판매처 자동 추출 유틸리티
"""
import re

def extract_store(title, site, article=None):
    if site == 'EOMISAE':
        # 제목 첫 단어
        first_word = title.split()[0] if title else None
        if first_word:
            return clean_store_name(first_word)

    return '기타'

def clean_store_name(name):
    if not name:
        return '기타'

    # 앞뒤 공백
    name = name.strip()

    # 특수문자
    store = re.sub(r'[\[\](){}]', '', name)

    return name