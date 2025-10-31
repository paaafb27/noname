#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
크롤러 긴급 테스트 스크립트
루리웹, 뽐뿌, 에펨코리아 작동 여부 확인
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

# 테스트할 크롤러 설정
CRAWLERS = {
    'PPOMPPU': {
        'url': 'https://www.ppomppu.co.kr/zboard/zboard.php?id=ppomppu',
        'selector': 'tr[class*="list"]'
    },
    'RULIWEB': {
        'url': 'https://bbs.ruliweb.com/market/board/1020',
        'selector': '.table_body tr'
    },
    'FMKOREA': {
        'url': 'https://www.fmkorea.com/hotdeal',
        'selector': '.li_best_wrapper li'
    }
}

def test_connection(site_name, url):
    """사이트 연결 테스트"""
    print(f"\n{'='*50}")
    print(f"🧪 테스트: {site_name}")
    print(f"{'='*50}")
    print(f"📍 URL: {url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ 연결 성공: {response.status_code}")
            return response.text
        else:
            print(f"❌ 연결 실패: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ 에러: {str(e)}")
        return None

def test_parsing(html_content, selector):
    """HTML 파싱 테스트"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        items = soup.select(selector)
        
        if len(items) > 0:
            print(f"✅ 파싱 성공: {len(items)}개 아이템 발견")
            return True
        else:
            print(f"❌ 파싱 실패: 아이템 없음")
            print(f"   시도한 선택자: {selector}")
            return False
            
    except Exception as e:
        print(f"❌ 파싱 에러: {str(e)}")
        return False

def main():
    print("🚀 3개 크롤러 긴급 테스트 시작\n")
    
    results = {}
    
    for site_name, config in CRAWLERS.items():
        html = test_connection(site_name, config['url'])
        
        if html:
            success = test_parsing(html, config['selector'])
            results[site_name] = success
        else:
            results[site_name] = False
    
    # 결과 요약
    print(f"\n{'='*50}")
    print("📊 최종 결과")
    print(f"{'='*50}")
    
    success_count = sum(results.values())
    total_count = len(results)
    
    for site, success in results.items():
        status = "✅ 정상" if success else "❌ 문제"
        print(f"{site}: {status}")
    
    print(f"\n성공률: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    if success_count == 0:
        print("\n⚠️ 모든 크롤러 실패!")
        print("가능한 원인:")
        print("1. 사이트 접속 차단 (IP/Bot 차단)")
        print("2. HTML 구조 변경")
        print("3. 네트워크 문제")
        print("\n💡 해결책:")
        print("- requests_html 또는 selenium 사용")
        print("- User-Agent 변경")
        print("- Proxy 사용")
    elif success_count < total_count:
        failed = [k for k, v in results.items() if not v]
        print(f"\n⚠️ 일부 크롤러 실패: {', '.join(failed)}")
    else:
        print("\n🎉 모든 크롤러 정상 작동!")

if __name__ == "__main__":
    main()
