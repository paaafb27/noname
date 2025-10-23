"""
전체 사이트 스크래퍼 통합 테스트
"""
import sys
import os
import json
from datetime import datetime



# ✅ PYTHONPATH에 functions 디렉토리 추가 (common 모듈 인식용)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)  # scandeals-crawler
sys.path.insert(0, project_root)  # common 접근 가능
sys.path.insert(0, current_dir)    # functions 접근 가능

from fmkorea.scraper import FmkoreaScraper
from ppomppu.scraper import PpomppuScraper
from ruliweb.scraper import RuliwebScraper
from eomisae.scraper import EomisaeScraper
from arcalive.scraper import ArcaliveScraper
from quasarzone.scraper import QuasarzoneScraper

def test_scraper(scraper_class, site_name):
    """
    개별 스크래퍼 테스트 함수

    Args:
        scraper_class: 스크래퍼 클래스
        site_name: 사이트명

    Returns:
        dict: 테스트 결과 (성공/실패, 수집 개수, 소요 시간)
    """
    print(f"\n{'='*50}")
    print(f"📌 {site_name} 테스트 시작")
    print(f"{'='*50}\n")

    try:
        # 스크래퍼 인스턴스 생성 및 실행
        scraper = scraper_class()

        if hasattr(scraper, 'test_mode'):
            scraper.test_mode = True

        start_time = datetime.now()
        results = scraper.scrape()
        end_time = datetime.now()

        # 결과 출력
        duration = (end_time - start_time).total_seconds()
        print(f"\n✅ {site_name} 완료")
        print(f"   - 수집 개수: {len(results)}개")
        print(f"   - 소요 시간: {duration:.2f}초")

        # 샘플 데이터 출력
        if results:
            print(f"\n   [첫 번째 항목 샘플]")
            sample = results[0]
            print(f"   제목: {sample.get('title', 'N/A')[:50]}...")
            print(f"   가격: {sample.get('price', 'N/A')}")
            print(f"   판매처: {sample.get('storeName', 'N/A')}")
            print(f"   시간: {sample.get('crawledAt', 'N/A')}")

            # 데이터 구조 검증
            required_fields = ['title', 'productUrl', 'sourceSite', 'crawledAt']
            missing_fields = [f for f in required_fields if f not in sample]
            if missing_fields:
                print(f"   ⚠️ 누락된 필드: {missing_fields}")
        else:
            print(f"   ⚠️ 수집된 데이터 없음")

        return {
            'site': site_name,
            'success': True,
            'count': len(results),
            'duration': duration,
            'sample': results[0] if results else None
        }

    except Exception as e:
        print(f"\n❌ {site_name} 실패")
        print(f"   에러: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'site': site_name,
            'success': False,
            'error': str(e)
        }


def main():
    """전체 스크래퍼 테스트 실행"""
    print("\n" + "="*50)
    print("🚀 전체 사이트 스크래퍼 테스트")
    print("="*50)

    # 테스트 대상 목록
    scrapers = [
        (ArcaliveScraper, 'ARCALIVE'),
        (RuliwebScraper, 'RULIWEB'),
        (PpomppuScraper, 'PPOMPPU'),
        (EomisaeScraper, 'EOMISAE'),
        (FmkoreaScraper, 'FMKOREA'),
        (QuasarzoneScraper, 'QUASARZONE')
    ]

    # 전체 테스트 실행
    test_start = datetime.now()
    results = []

    for scraper_class, site_name in scrapers:
        result = test_scraper(scraper_class, site_name)
        results.append(result)

    test_end = datetime.now()
    total_duration = (test_end - test_start).total_seconds()

    # 최종 결과 요약
    print(f"\n{'='*50}")
    print(f"📊 전체 테스트 결과 요약")
    print(f"{'='*50}\n")

    success_count = sum(1 for r in results if r['success'])
    total_items = sum(r.get('count', 0) for r in results if r['success'])

    print(f"✅ 성공: {success_count}/{len(scrapers)}개")
    print(f"📦 총 수집: {total_items}개")
    print(f"⏱️ 전체 소요 시간: {total_duration:.2f}초")
    print()

    # 상세 결과
    for result in results:
        status = "✅" if result['success'] else "❌"
        site = result['site']
        if result['success']:
            count = result['count']
            duration = result['duration']
            print(f"{status} {site:12s} - {count:3d}개 ({duration:.1f}초)")
        else:
            error = result.get('error', 'Unknown error')
            print(f"{status} {site:12s} - 실패: {error[:50]}...")

    # 결과 JSON 저장
    output_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n📄 상세 결과 저장: {output_file}")


if __name__ == '__main__':
    main()