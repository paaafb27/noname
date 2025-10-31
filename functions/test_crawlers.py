"""
전체 사이트 크롤러 통합 테스트 스크립트

사용법:
    python test_crawlers.py                    # 모든 사이트 테스트
    python test_crawlers.py ppomppu            # 특정 사이트만 테스트
    python test_crawlers.py ppomppu ruliweb    # 여러 사이트 테스트

지원 사이트: ppomppu, ruliweb, fmkorea, quasarzone, arcalive, eomisae
"""

import sys
import os
import json
import importlib.util
from datetime import datetime
import argparse

# 사이트별 설정
SITES_CONFIG = {
    'ppomppu': {
        'name': '뽐뿌',
        'path': 'ppomppu/scraper.py',
        'class_name': 'PpomppuScraper'
    },
    'ruliweb': {
        'name': '루리웹',
        'path': 'ruliweb/scraper.py',
        'class_name': 'RuliwebScraper'
    },
    'fmkorea': {
        'name': 'FM코리아',
        'path': 'fmkorea/scraper.py',
        'class_name': 'FmkoreaScraper'
    },
    'quasarzone': {
        'name': '퀘이사존',
        'path': 'quasarzone/scraper.py',
        'class_name': 'QuasarzoneScraper'
    },
    'arcalive': {
        'name': '아카라이브',
        'path': 'arcalive/scraper.py',
        'class_name': 'ArcaliveScraper'
    },
    'eomisae': {
        'name': '어미새',
        'path': 'eomisae/scraper.py',
        'class_name': 'EomisaeScraper'
    }
}


def load_scraper_class(site_key):
    """
    동적으로 스크래퍼 클래스를 로드
    
    Args:
        site_key: 사이트 키 (예: 'ppomppu')
    
    Returns:
        Scraper 클래스
    """
    if site_key not in SITES_CONFIG:
        raise ValueError(f"지원하지 않는 사이트: {site_key}")
    
    config = SITES_CONFIG[site_key]
    script_dir = os.path.dirname(os.path.abspath(__file__))
    scraper_path = os.path.join(script_dir, config['path'])
    
    if not os.path.exists(scraper_path):
        raise FileNotFoundError(f"스크래퍼 파일을 찾을 수 없습니다: {scraper_path}")
    
    # 모듈 동적 로드
    spec = importlib.util.spec_from_file_location(f"{site_key}_scraper", scraper_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # 클래스 가져오기
    scraper_class = getattr(module, config['class_name'])
    return scraper_class


def test_single_site(site_key, save_json=True, filter_minutes=120):
    """
    개별 사이트 테스트
    
    Args:
        site_key: 사이트 키
        save_json: JSON 파일 저장 여부
        filter_minutes: 필터링 시간 (기본 120분)
    
    Returns:
        dict: 테스트 결과
    """
    config = SITES_CONFIG[site_key]
    site_name = config['name']
    
    print(f"\n{'='*70}")
    print(f"🔍 [{site_name}] 크롤러 테스트 시작")
    print(f"{'='*70}")
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"필터링 시간: {filter_minutes}분")
    print()
    
    result = {
        'site_key': site_key,
        'site_name': site_name,
        'success': False,
        'count': 0,
        'duration': 0,
        'error': None,
        'sample_items': []
    }
    
    try:
        # 스크래퍼 클래스 로드
        print(f"📦 스크래퍼 클래스 로드: {config['class_name']}")
        scraper_class = load_scraper_class(site_key)
        
        # 스크래퍼 인스턴스 생성
        scraper = scraper_class()
        
        # 필터링 시간 설정
        if hasattr(scraper, 'filter_minutes'):
            scraper.filter_minutes = filter_minutes
            print(f"⏰ 필터링 시간 설정: {filter_minutes}분")
        
        # 크롤링 실행
        print(f"🚀 크롤링 시작...\n")
        start_time = datetime.now()
        
        items = scraper.scrape()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 결과 저장
        result['success'] = True
        result['count'] = len(items)
        result['duration'] = round(duration, 2)
        result['sample_items'] = items[:3] if items else []
        
        # 결과 출력
        print(f"\n{'='*70}")
        print(f"✅ [{site_name}] 크롤링 완료")
        print(f"{'='*70}")
        print(f"수집 개수: {len(items)}개")
        print(f"소요 시간: {duration:.2f}초")
        print()
        
        # 샘플 데이터 출력
        if items:
            print(f"📊 샘플 데이터 (최대 3개):")
            for i, item in enumerate(items[:3], 1):
                print(f"\n[{i}] {item.get('title', 'N/A')[:60]}...")
                print(f"    가격: {item.get('price', 'N/A')}")
                print(f"    판매처: {item.get('storeName', 'N/A')}")
                print(f"    시간: {item.get('crawledAt', 'N/A')}")
                
                # URL 길이 체크
                product_url = item.get('productUrl', '')
                if product_url:
                    print(f"    URL: {product_url[:60]}...")
            
            if len(items) > 3:
                print(f"\n... 외 {len(items) - 3}개")
            
            # 필수 필드 검증
            required_fields = ['title', 'productUrl', 'sourceSite', 'crawledAt']
            sample = items[0]
            missing_fields = [f for f in required_fields if f not in sample or not sample[f]]
            
            if missing_fields:
                print(f"\n⚠️  경고: 누락된 필수 필드 - {missing_fields}")
            else:
                print(f"\n✅ 필수 필드 검증 통과")
            
            # JSON 저장
            if save_json:
                output_file = f"test_result_{site_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(items, f, ensure_ascii=False, indent=2)
                print(f"\n💾 결과 저장: {output_file}")
        else:
            print("⚠️  수집된 데이터가 없습니다.")
            print("   - 필터링 시간을 늘려보세요 (--minutes 옵션)")
            print("   - 해당 시간대에 게시글이 없을 수 있습니다")
        
        return result
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️  사용자에 의해 중단되었습니다.")
        result['error'] = "사용자 중단"
        return result
        
    except Exception as e:
        print(f"\n{'='*70}")
        print(f"❌ [{site_name}] 크롤링 실패")
        print(f"{'='*70}")
        print(f"에러: {str(e)}")
        print()
        
        # 상세 에러 출력
        import traceback
        print("상세 에러:")
        traceback.print_exc()
        
        result['error'] = str(e)
        return result


def test_multiple_sites(site_keys, save_json=True, filter_minutes=60):
    """
    여러 사이트 테스트
    
    Args:
        site_keys: 테스트할 사이트 키 리스트
        save_json: JSON 파일 저장 여부
        filter_minutes: 필터링 시간
    
    Returns:
        list: 각 사이트 테스트 결과
    """
    print("\n" + "="*70)
    print("🚀 전체 사이트 크롤러 통합 테스트")
    print("="*70)
    print(f"테스트 대상: {', '.join([SITES_CONFIG[k]['name'] for k in site_keys])}")
    print(f"총 {len(site_keys)}개 사이트")
    print()
    
    results = []
    
    for i, site_key in enumerate(site_keys, 1):
        print(f"\n[{i}/{len(site_keys)}] {SITES_CONFIG[site_key]['name']} 테스트 중...")
        result = test_single_site(site_key, save_json, filter_minutes)
        results.append(result)
    
    # 전체 결과 요약
    print("\n\n" + "="*70)
    print("📊 전체 테스트 결과 요약")
    print("="*70)
    
    success_count = sum(1 for r in results if r['success'])
    total_items = sum(r['count'] for r in results)
    total_duration = sum(r['duration'] for r in results)
    
    print(f"\n성공: {success_count}/{len(site_keys)} 사이트")
    print(f"총 수집: {total_items}개")
    print(f"총 소요시간: {total_duration:.2f}초")
    print()
    
    # 사이트별 결과
    print("사이트별 상세 결과:")
    print("-" * 70)
    for r in results:
        status = "✅" if r['success'] else "❌"
        print(f"{status} {r['site_name']:10s} | {r['count']:4d}개 | {r['duration']:6.2f}초", end="")
        if r['error']:
            print(f" | 에러: {r['error'][:30]}...")
        else:
            print()
    
    print()
    
    # 실패한 사이트 안내
    failed_sites = [r for r in results if not r['success']]
    if failed_sites:
        print("⚠️  실패한 사이트:")
        for r in failed_sites:
            print(f"   - {r['site_name']}: {r['error']}")
        print()
    
    return results


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description='크롤러 테스트 스크립트',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  python test_crawlers.py                      # 모든 사이트 테스트
  python test_crawlers.py ppomppu              # 뽐뿌만 테스트
  python test_crawlers.py ppomppu ruliweb      # 뽐뿌, 루리웹 테스트
  python test_crawlers.py --minutes 60         # 60분 필터링으로 테스트
  python test_crawlers.py --no-save            # JSON 저장 안함
  python test_crawlers.py --list               # 지원 사이트 목록

지원 사이트:
  ppomppu, ruliweb, fmkorea, quasarzone, arcalive, eomisae
        """
    )
    
    parser.add_argument(
        'sites',
        nargs='*',
        help='테스트할 사이트 (없으면 전체)'
    )
    
    parser.add_argument(
        '--minutes',
        type=int,
        default=120,
        help='필터링 시간 (기본: 120분)'
    )
    
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='JSON 파일 저장 안함'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='지원 사이트 목록 출력'
    )
    
    args = parser.parse_args()
    
    # 사이트 목록 출력
    if args.list:
        print("\n지원하는 사이트 목록:")
        print("-" * 40)
        for key, config in SITES_CONFIG.items():
            print(f"  {key:12s} - {config['name']}")
        print()
        return
    
    # 테스트할 사이트 결정
    if args.sites:
        # 명령행 인자로 지정된 사이트
        invalid_sites = [s for s in args.sites if s not in SITES_CONFIG]
        if invalid_sites:
            print(f"❌ 지원하지 않는 사이트: {', '.join(invalid_sites)}")
            print(f"사용 가능: {', '.join(SITES_CONFIG.keys())}")
            return
        test_sites = args.sites
    else:
        # 전체 사이트
        test_sites = list(SITES_CONFIG.keys())
    
    # 테스트 실행
    save_json = not args.no_save
    
    if len(test_sites) == 1:
        # 단일 사이트 테스트
        test_single_site(test_sites[0], save_json, args.minutes)
    else:
        # 다중 사이트 테스트
        test_multiple_sites(test_sites, save_json, args.minutes)


if __name__ == "__main__":
    main()
