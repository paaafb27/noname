"""
모든 scraper.py의 _create_driver 함수를 자동으로 수정하는 스크립트

사용법:
    python fix_all_scrapers.py

실행 후:
    - 6개 scraper 파일이 자동으로 수정됩니다
    - 백업 파일(.backup)이 자동 생성됩니다
"""

import os
import shutil
from pathlib import Path

# 수정할 scraper 목록
SCRAPER_DIRS = [
    'ppomppu',
    'ruliweb', 
    'fmkorea',
    'quasarzone',
    'arcalive',
    'eomisae'
]

# 새로운 _create_driver 함수
NEW_DRIVER_CODE = '''    def _create_driver(self):
        options = Options()

        # User-Agent 설정 (공통)
        options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        # 기본 옵션 (공통)
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--referer=https://www.google.com/')

        # 자동화 감지 우회
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        try:
            # ✅ 환경 자동 감지
            import platform
            is_windows = platform.system() == 'Windows'
            
            if is_windows:
                print("(로컬 Windows 환경 감지 - WebDriverManager 자동 설치)")
                # 로컬: WebDriverManager 사용
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
            else:
                print("(Linux 컨테이너 환경 감지 - Fargate 경로 사용)")
                # Fargate: 고정 경로
                service = Service('/usr/local/bin/chromedriver')
            
            driver = webdriver.Chrome(service=service, options=options)
            print("✅ Chrome 드라이버 생성 성공!")

            # WebDriver 속성 숨기기
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.set_page_load_timeout(60)
            return driver
            
        except Exception as e:
            print(f"❌ Chrome 드라이버 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            raise
'''


def find_function_range(lines, function_name):
    """
    함수의 시작과 끝 라인 번호 찾기
    
    Returns:
        tuple: (start_line, end_line) or None
    """
    start = None
    indent_level = None
    
    for i, line in enumerate(lines):
        # 함수 시작 찾기
        if line.strip().startswith(f'def {function_name}('):
            start = i
            # 함수 본문의 들여쓰기 레벨 찾기
            for j in range(i+1, len(lines)):
                if lines[j].strip() and not lines[j].strip().startswith('#'):
                    indent_level = len(lines[j]) - len(lines[j].lstrip())
                    break
            continue
        
        # 함수 끝 찾기 (같은 레벨의 다른 def 또는 class 만나면)
        if start is not None and indent_level is not None:
            current_indent = len(line) - len(line.lstrip())
            
            # 빈 줄이 아니고, 같거나 작은 들여쓰기 레벨이면서 def/class로 시작하면
            if line.strip() and current_indent <= indent_level - 4:
                if line.strip().startswith(('def ', 'class ')):
                    return (start, i)
    
    # 파일 끝까지 함수가 계속되는 경우
    if start is not None:
        return (start, len(lines))
    
    return None


def fix_scraper_file(scraper_path):
    """
    개별 scraper.py 파일 수정
    
    Args:
        scraper_path: scraper.py 파일 경로
    
    Returns:
        bool: 성공 여부
    """
    if not os.path.exists(scraper_path):
        print(f"  ⚠️  파일 없음: {scraper_path}")
        return False
    
    try:
        # 백업 생성
        backup_path = scraper_path + '.backup'
        shutil.copy2(scraper_path, backup_path)
        print(f"  💾 백업 생성: {backup_path}")
        
        # 파일 읽기
        with open(scraper_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # _create_driver 함수 범위 찾기
        function_range = find_function_range(lines, '_create_driver')
        
        if not function_range:
            print(f"  ⚠️  _create_driver 함수를 찾을 수 없습니다")
            return False
        
        start_line, end_line = function_range
        print(f"  📍 함수 위치: {start_line+1}~{end_line} 라인")
        
        # 새 코드로 교체
        new_lines = (
            lines[:start_line] + 
            [NEW_DRIVER_CODE + '\n'] + 
            lines[end_line:]
        )
        
        # 파일 쓰기
        with open(scraper_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        print(f"  ✅ 수정 완료")
        return True
        
    except Exception as e:
        print(f"  ❌ 수정 실패: {e}")
        # 백업 복구
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, scraper_path)
            print(f"  🔄 백업에서 복구됨")
        return False


def main():
    """메인 함수"""
    print("\n" + "="*70)
    print("🔧 전체 Scraper 드라이버 함수 자동 수정")
    print("="*70)
    print()
    
    script_dir = Path(__file__).parent
    success_count = 0
    
    for scraper_dir in SCRAPER_DIRS:
        scraper_path = script_dir / scraper_dir / 'scraper.py'
        
        print(f"[{scraper_dir}]")
        
        if fix_scraper_file(str(scraper_path)):
            success_count += 1
        
        print()
    
    # 결과 요약
    print("="*70)
    print(f"📊 수정 완료: {success_count}/{len(SCRAPER_DIRS)} 파일")
    print("="*70)
    
    if success_count == len(SCRAPER_DIRS):
        print("\n✅ 모든 파일 수정 성공!")
        print("\n다음 단계:")
        print("  1. python test_crawlers.py ruliweb fmkorea  # 테스트")
        print("  2. 문제없으면 Fargate 배포 진행")
    else:
        print(f"\n⚠️  {len(SCRAPER_DIRS) - success_count}개 파일 수정 실패")
        print("  수동으로 driver_fix_patch.py 참고하여 수정 필요")
    
    print()


if __name__ == "__main__":
    main()
