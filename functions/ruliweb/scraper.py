"""
루리웹 크롤러

URL: https://bbs.ruliweb.com/market/board/1020
필터링: notice, company, best 클래스 제외
판매처: <span class="subject_tag"> 또는 제목에서 추출
"""
import datetime
import random
import time

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
)
from common.number_extractor import (
    extract_price_from_text,
    extract_shipping_fee,
    clean_title,
    extract_comment_count_from_title,
    format_price, extract_number_from_text
)
from bs4 import BeautifulSoup
import sys
import os
import re
import boto3  # [추가] S3 업로드를 위해 import

from webdriver_manager.core.os_manager import ChromeType

from common.log_util import log_item
from common.store_extractor import clean_store_name

# common 모듈
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from common.filter_by_regtime import filter_by_time, parse_time, to_iso8601



class RuliwebScraper:

    def __init__(self):
        self.url = 'https://bbs.ruliweb.com/market/board/1020'
        self.main_url = 'https://www.ruliweb.com/'
        self.source_site = 'RULIWEB'
        self.max_pages = 3
        self.test_mode = False

        # 환경 변수에서 필터링 시간 읽기 (기본값 30분)
        self.filter_minutes = int(os.environ.get('FILTER_MINUTES', 30))

        # [추가] 디버깅 파일을 저장할 S3 버킷 이름 (환경 변수에서 가져오기)
        self.s3_bucket_name = os.environ.get('S3_BUCKET_NAME')

    def scrape(self):
        """페이징 크롤링 (30분 필터링)"""
        return self._scrape_with_pagination()

    def _scrape_with_pagination(self):
        """
        - 페이지의 마지막 게시글이 30분 이내면 다음 페이지 계속 확인
        - 마지막 게시글이 30분 초과하거나 최대 페이지 도달 시 중단
        """

        all_items = []
        page_num = 1
        driver = None

        kst = datetime.timezone(datetime.timedelta(hours=9))
        filter_minutes = self.filter_minutes
        now = datetime.datetime.now(kst)
        cutoff_time = now - datetime.timedelta(minutes=filter_minutes)

        try:
            driver = self._create_driver()
            print("Chrome 브라우저 시작")

            while page_num <= self.max_pages:
                print(f"\n{page_num}페이지 크롤링...")

                # 같은 driver 재사용
                page_items = self._scrape_page(driver, page_num)

                if not page_items:
                    print(f"{page_num}페이지: 게시글 없음, 종료")
                    break

                # 30분 이내 작성된 게시글 필터링
                page_filtered = filter_by_time(page_items, minutes=filter_minutes)
                if page_filtered:
                    print(f"수집 대상 {len(page_filtered)}개:")
                    for filtered_item in page_filtered:
                        log_item(filtered_item)

                all_items.extend(page_filtered)
                print(f"{page_num}페이지: {len(page_items)}개 → 필터링 {len(page_filtered)}개")

                # 다음 페이지 확인 여부 판단
                last_item = page_items[-1]
                crawled_at_str = last_item.get('createdAt', '')
                print(f"last_item_time: {crawled_at_str}")

                last_time = None
                if crawled_at_str:
                    try:
                        # 'yyyy-MM-dd HH:mm:ss' 형식이면 직접 파싱
                        if len(crawled_at_str) == 19 and crawled_at_str[10] == ' ':
                            last_time = datetime.datetime.strptime(crawled_at_str, '%Y-%m-%d %H:%M:%S')
                            last_time = last_time.replace(tzinfo=kst)
                        else:
                            # parse_time으로 파싱 (상대 시간 등)
                            last_time = parse_time(crawled_at_str)
                    except Exception as e:
                        print(f"시간 파싱 중 오류: {e}")
                        last_time = None

                if not last_time:
                    print(f"시간 파싱 실패, 크롤링 종료")
                    break  # continue 대신 break로 종료

                if last_time < cutoff_time:
                    print(f"마지막 게시글 {filter_minutes}분 초과 ({last_time.strftime('%H:%M:%S')}), 종료")
                    break

                print(f"마지막 게시글 {filter_minutes}분 이내 ({last_time.strftime('%H:%M:%S')}), 다음 페이지 확인")

                # 페이지 간 메모리 정리
                driver.execute_script("window.stop();")
                driver.delete_all_cookies()

                page_num += 1

            if page_num > self.max_pages:
                print(f"\n최대 페이지({self.max_pages}) 도달, 크롤링 종료")

            print(f"\n총 {len(all_items)}개 수집\n")
            return all_items

        except Exception as e:
            print(f"크롤링 실패: {e}")
            import traceback
            traceback.print_exc()
            return all_items  # 수집된 데이터라도 반환

        finally:
            if driver:
                try:
                    driver.quit()
                    print("Chrome 브라우저 정상 종료")
                except Exception as e:
                    print(f"Chrome 종료 중 에러: {e}")

    def _create_driver(self):
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
            # 환경 자동 감지
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
            print("Chrome 드라이버 생성 성공!")

            # WebDriver 속성 숨기기
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.set_page_load_timeout(60)
            return driver
            
        except Exception as e:
            print(f"❌ Chrome 드라이버 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _scrape_page(self, driver, page_num):
        """특정 페이지 크롤링"""

        items = []
        html = None

        try:
            # 페이지 URL
            if page_num == 1:
                url = self.main_url

                try:
                    boardSelector = "//a[@class='text_center special_dot' and contains(., '핫딜')]"
                    board_element = WebDriverWait(driver, 60).until(
                        EC.presence_of_element_located((By.XPATH, boardSelector))
                    )
                    
                    # element.click()
                    ActionChains(driver).move_to_element(board_element).click().perform()
                    print("핫딜 게시판 클릭")
                    time.sleep(random.uniform(1, 3))

                except TimeoutException:
                    print("Timeout: 30초 안에 '핫딜' 요소를 찾지 못했습니다.")

                except NoSuchElementException:
                    print("요소를 찾을 수 없습니다. XPath를 다시 확인하세요.")

                except ElementClickInterceptedException:
                    print("다른 요소가 클릭을 가로막고 있습니다. 스크롤이나 대기 로직이 필요할 수 있습니다.")

                except ElementNotInteractableException:
                    print("요소가 현재 클릭 가능한 상태가 아닙니다 (예: 숨겨져 있음).")

                except Exception as e:
                    print(f"핫딜 게시판 클릭 실패, 직접 이동: {e}")
                    driver.get(self.url)
                    time.sleep(2)
            else:
                # 2페이지 이상
                try:
                    # url = f"{self.main_url}/index.php?mid=hotdeal&page={page_num}"
                    nextPagePath = f"//*[@class='bd_pg clear']//a[normalize-space()='{page_num}']"
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, nextPagePath))
                    )
                    nextPageEl = driver.find_element(By.XPATH, nextPagePath)
                    ActionChains(driver).move_to_element(nextPageEl).click().perform()
                except Exception as e:
                    print(f"핫딜 게시판 클릭 실패, 직접 이동: {e}")
                    url = f"{self.url}&page={page_num}"
                    driver.get(url)
                    time.sleep(2)

            # 재시도 로직 추가
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    driver.get(url)
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"  재시도 {attempt + 1}/{max_retries}...")
                        time.sleep(10)
                    else:
                        print(f"  최종 실패: {e}")
                        raise

            try:
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".board_list_table"))
                )
                print("게시글 로드 확인")
            except Exception as e:
                # 타임아웃 되어도 계속 진행 (부분 데이터라도 수집)
                print(f"명시적 대기 타임아웃 (계속 진행): {e}")


            # HTML 파싱
            html = driver.page_source
            soup = BeautifulSoup(html, 'lxml')

            # 게시글 목록
            rows = soup.select('.board_list_table tbody tr.blocktarget')
            print(f"페이지 {page_num}: {len(rows)}개 발견")

            # 다른 선택자들도 시도
            if len(rows) == 0:
                print(f"  [DEBUG] 다른 선택자 시도...")
                alternative_rows = soup.select('.board_list_table')
                print(f"  [DEBUG] 대체 선택자: {len(alternative_rows)}개")

            if not rows:
                # 게시글이 0개일 때도 디버깅 파일 저장
                print(f"게시글이 0개입니다. 현재 페이지 상태를 디버깅용으로 S3에 저장합니다.")
                self._save_debug_files_to_s3(driver, error_prefix="no_posts_found")

            for row in rows:
                try:
                    # 필터링 : 공지 / 광고 제외
                    classes = row.get('class', [])
                    if 'best' in classes:
                        continue

                    # 데이터 추출
                    item = self._extract_item(row)
                    if item:
                        items.append(item)

                except Exception as e:
                    print(f"게시글 파싱 실패: {e}")
                    continue


        except Exception as e:
            # 이 경우에도 현재 상태 저장
            self._save_debug_files_to_s3(driver, error_prefix="page_load_error")
            import traceback
            traceback.print_exc()

        finally:
            html = None
            soup = None

        return items

    def _extract_item(self, row):
        """
        세일정보 추출
        """
        # 제목
        title_element = row.select_one('a.subject_link.deco')
        raw_title = title_element.get_text(strip=True) if title_element else None
        title = clean_title(raw_title)
        # reply_count = extract_comment_count_from_title(title)


        # 패턴 1: 제목 맨 끝 (n / m) → n=가격, m=배송비
        price = None
        shipping_fee = None
        price_shipping_pattern = r'\(([0-9,\.]+)\s*/\s*(.+?)\)\s*$'
        match = re.search(price_shipping_pattern, raw_title)
        if match:
            price_text = match.group(1).replace(',', '')
            shipping_text = match.group(2).strip()

            try:
                # 가격
                price = float(price_text)
            except:
                pass

            # 배송비
            shipping_fee = extract_shipping_fee(shipping_text)

            # 가격/배송비 제거한 제목
            title = title[:match.start()].strip()

        # 패턴 2: 일반 가격 추출 (common util)
        if price is None:
            price = extract_price_from_text(title)

        # 판매처
        # 1) element 확인
        # 2) 제목에서 [판매처] 추출
        store_element = row.select_one('span.subject_tag')
        if store_element:
            store = store_element.get_text(strip=True)
            store = clean_store_name(store)
        else:
            store = '기타'

        # 댓글 수
        reply_element = row.select_one('span.num_reply')
        reply_count = reply_element.get_text(strip=True) if reply_element else 0
        reply_count = extract_number_from_text(reply_count)

        # 좋아요 수
        like_element = row.select_one('td.recomd')
        like_count = like_element.get_text(strip=True) if like_element else 0

        # 등록 시간
        time_element = row.select_one('td.time')
        if time_element:
            time_text = time_element.get_text(strip=True)
            # print(f"  [DEBUG] 원본 시간: {time_text}")
            time_obj = parse_time(time_text)
            if not time_obj:
                print(f"  [DEBUG] 파싱 실패!")
            time = to_iso8601(time_obj) if time_obj else None

        # 카테고리
        category_element = row.select_one('td.divsn.text_over a')
        category = category_element.get_text(strip=True) if category_element else None

        # URL
        product_url = title_element['href']

        # 이미지 url
        image_url = None


        return {
            'title': title,
            'price': price,
            'storeName': store,
            'category': category,
            'shippingFee': shipping_fee,
            'productUrl': product_url,
            'imageUrl': image_url,
            'replyCount': reply_count,
            'likeCount': like_count,
            'sourceSite': self.source_site,
            'crawledAt': time
        }

    def _save_debug_files_to_s3(self, driver, error_prefix):
        """
        에러 발생 시 스크린샷과 HTML을 S3에 저장

        Args:
            driver: Selenium WebDriver 인스턴스
            error_prefix: 파일명 접두사 (예: "no_posts_found", "page_load_error")

        목적:
            - 프로덕션 환경에서 디버깅 용이성 확보
            - 크롤링 실패 원인 추적

        효과:
            - CloudWatch 로그만으로 부족한 정보 보완
            - 실제 페이지 상태 시각적 확인 가능
        """
        if not self.s3_bucket_name:
            print("⚠️ S3 버킷 이름이 설정되지 않아 디버그 파일을 저장할 수 없습니다.")
            return

        try:
            kst = datetime.timezone(datetime.timedelta(hours=9))
            timestamp = datetime.datetime.now(kst).strftime('%Y%m%d_%H%M%S')
            s3_client = boto3.client('s3')

            # 1. HTML 소스 저장
            html_filename = f"{error_prefix}_{timestamp}.html"
            html_content = driver.page_source
            s3_client.put_object(
                Bucket=self.s3_bucket_name,
                Key=f"debug/{self.source_site}/{html_filename}",
                Body=html_content.encode('utf-8'),
                ContentType='text/html'
            )
            print(f"✅ HTML 저장: s3://{self.s3_bucket_name}/debug/{self.source_site}/{html_filename}")

            # 2. 스크린샷 저장
            screenshot_filename = f"{error_prefix}_{timestamp}.png"
            screenshot_data = driver.get_screenshot_as_png()
            s3_client.put_object(
                Bucket=self.s3_bucket_name,
                Key=f"debug/{self.source_site}/{screenshot_filename}",
                Body=screenshot_data,
                ContentType='image/png'
            )
            print(f"✅ 스크린샷 저장: s3://{self.s3_bucket_name}/debug/{self.source_site}/{screenshot_filename}")

        except Exception as e:
            print(f"❌ S3 디버그 파일 저장 실패: {e}")
            import traceback
            traceback.print_exc()
