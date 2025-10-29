"""
판매처 자동 추출 유틸리티
"""
import re

def extract_store(title, site, article=None):
    if "EOMISAE" in site:
        # 제목 첫 단어
        first_word = title.split()[0] if title else None
        if first_word:
            return clean_store_name(first_word)

    elif "QUASARZONE" in site:
        # 제목 : [판매처] 상품명
        match = re.search(r'^\[(.+?)\]', title)
        if match:
            store = match.group(1).strip()
            return clean_store_name(store)

    return '기타'

def clean_store_name(name):
    if not name:
        return '기타'

    # 앞뒤 공백
    name = name.strip()

    # 특수문자
    store = re.sub(r'[\[\](){}]', '', name)

    return store