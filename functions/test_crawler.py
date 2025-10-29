"""
사이트별 로컬 테스트 스크립트
각 사이트 크롤러를 독립적으로 테스트
"""

import sys
import os
import json
from datetime import datetime

# 테스트할 사이트 선택
SITES = {
    'ppomppu': {
        'path': 'functions/ppomppu',
        'class': 'PpomppuScraper'
    },
    'ruliweb': {
        'path': 'functions/ruliweb',
        'class': 'RuliwebScraper'
    },
    'fmkorea': {
        'path': 'functions/fmkorea',
        'class': 'FmkoreaScraper'
    },
    'quasarzone': {
        'path': 'functions/quasarzone',
        'class': 'QuasarzoneScraper'
    },
    'arcalive': {
        'path': 'functions/arcalive',
        'class': 'ArcaliveScraper'
    },
    'eomisae': {
        'path': 'functions/eomisae',
        'class': 'EomisaeScraper'
    }
}


def test_site(site_name):
    """
    특정 사이트 크롤러 테스트
    """
    if site_name not in SITES:
        print(f"❌ 지원하지 않는 사이트: {site_name}")
        print(f"사용 가능: {', '.join(SITES.keys())}")
        return

    site_info = SITES[site_name]

    print("=" * 60)
    print(f"🔍 {site_name.upper()} 크롤러 테스트")
    print("=" * 60)
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        # 모듈 경로 추가
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), site_info['path']))

        # 스크래퍼 import
        scraper_module = __import__('scraper')
        scraper_class = getattr(scraper_module, site_info['class'])

        # 스크래퍼 실행
        scraper = scraper_class()
        scraper.test_mode = True  # 테스트 모드 활성화

        print("✅ 크롤링 시작...")
        items = scraper.scrape()

        print()
        print("=" * 60)
        print("📊 크롤링 결과")
        print("=" * 60)
        print(f"수집 개수: {len(items)}개")
        print()

        if items:
            # 처음 3개 항목 출력
            for i, item in enumerate(items[:3], 1):
                print(f"[{i}] {item.get('title', 'N/A')}")
                print(f"    가격: {item.get('price_str', item.get('price', 'N/A'))}")
                print(f"    판매처: {item.get('storeName', 'N/A')}")
                print(f"    URL: {item.get('productUrl', 'N/A')[:60]}...")
                print(f"    시간: {item.get('crawledAt', 'N/A')}")
                print()

            if len(items) > 3:
                print(f"... 외 {len(items) - 3}개")
                print()

            # JSON 파일로 저장
            output_file = f"test_output_{site_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False, indent=2)

            print(f"✅ 결과 저장: {output_file}")
        else:
            print("⚠️  크롤링된 항목 없음 (30분 이내 게시글 없거나 에러)")

        print()
        print("=" * 60)
        print(f"종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

    except Exception as e:
        print()
        print("=" * 60)
        print("❌ 에러 발생")
        print("=" * 60)
        print(f"{type(e).__name__}: {str(e)}")

        import traceback
        print()
        print("상세 에러:")
        traceback.print_exc()


def test_all_sites():
    """
    모든 사이트 순차 테스트
    """
    print()
    print("=" * 60)
    print("🚀 전체 사이트 크롤러 테스트")
    print("=" * 60)
    print()

    results = {}

    for site_name in SITES.keys():
        try:
            test_site(site_name)
            results[site_name] = "✅ 성공"
        except Exception as e:
            results[site_name] = f"❌ 실패: {str(e)}"

        print()
        print()

    # 최종 결과 요약
    print("=" * 60)
    print("📋 전체 테스트 결과 요약")
    print("=" * 60)
    for site, result in results.items():
        print(f"{site:15s}: {result}")
    print("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='사이트별 크롤러 테스트')
    parser.add_argument(
        'site',
        nargs='?',
        choices=list(SITES.keys()) + ['all'],
        help='테스트할 사이트 (all: 전체)'
    )

    args = parser.parse_args()

    if not args.site:
        print("사용법:")
        print(f"  python test_crawler.py [사이트명]")
        print()
        print("사용 가능한 사이트:")
        for site in SITES.keys():
            print(f"  - {site}")
        print(f"  - all (전체 테스트)")
        sys.exit(1)

    if args.site == 'all':
        test_all_sites()
    else:
        test_site(args.site)