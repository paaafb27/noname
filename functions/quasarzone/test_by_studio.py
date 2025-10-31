# -----------------------------------------------------------------
# 로컬 테스트를 위한 실행 스크립트 (local_test.py)
# (모든 파일이 같은 폴더에 있을 경우)
# -----------------------------------------------------------------

# Selenium 및 WebDriver 자동 관리자 임포트
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from scraper import QuasarzoneScraper



def main():
    """
    로컬 PC에서 Selenium WebDriver를 설정하고 스크레이퍼를 실행합니다.
    """
    service = ChromeService(executable_path=ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')

    # User-Agent 설정 (공통)
    options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    # 기본 옵션 (공통)
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--referer=https://www.google.com/')

    # 자동화 감지 우회
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = None
    try:
        driver = webdriver.Chrome(service=service, options=options)
        print("✅ 로컬 크롬 드라이버가 성공적으로 시작되었습니다.")

        # 1. 스크레이퍼 객체 생성
        scraper = QuasarzoneScraper()

        # 2. 스크레이퍼의 메인 실행 함수 호출
        scraped_items = scraper.scrape()  # scrape()가 메인 함수라고 가정

        # 3. 결과 확인
        print("\n" + "=" * 50)
        print(f"✅ 총 {len(scraped_items)}개의 아이템 수집 완료!")
        print("=" * 50)

        if scraped_items:
            print("\n[수집된 첫 번째 아이템 예시]")
            import pprint
            pprint.pprint(scraped_items[0])

    except Exception as e:
        print(f"❌ 테스트 실행 중 오류가 발생했습니다: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if driver:
            driver.quit()
            print("\n✅ 드라이버를 종료하고 테스트를 마칩니다.")


if __name__ == "__main__":
    main()