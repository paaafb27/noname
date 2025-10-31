"""
뽐뿌 크롤러 로컬 테스트 스크립트

실행 방법:
1. PowerShell에서: .\test_ppomppu_local.ps1
2. 또는 직접: python test_ppomppu_scraper.py
"""
import json
import datetime
import re
import sys
import os

# ========================================
# common 모듈 Mock (테스트용)
# ========================================

def log_item(item):
    """테스트용 로그 출력"""
    print(f"  - {item.get('title', '')[:50]}... | {item.get('storeName', '')} | {item.get('crawledAt', '')}")


def clean_store_name(name):
    """판매처 이름 정리"""
    if not name:
        return None
    
    # 괄호와 내용 제거
    name = re.sub(r'\[.*?\]', '', name)
    name = re.sub(r'\(.*?\)', '', name)
    
    # 특수문자 제거 및 공백 정리
    name = re.sub(r'[^\w\s가-힣]', '', name)
    name = name.strip()
    
    return name if name else None


def parse_time(time_text):
    """
    시간 텍스트를 datetime 객체로 변환
    형식: "HH:MM:SS" 또는 "MM/DD HH:MM:SS"
    """
    if not time_text:
        return None
    
    kst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(kst)
    
    try:
        # "HH:MM:SS" 형식 (오늘)
        if len(time_text.split(':')) == 3 and '/' not in time_text:
            time_obj = datetime.datetime.strptime(time_text, '%H:%M:%S')
            result = now.replace(hour=time_obj.hour, minute=time_obj.minute, second=time_obj.second, microsecond=0)
            return result
        
        # "MM/DD HH:MM:SS" 형식
        elif '/' in time_text:
            parts = time_text.split(' ')
            date_part = parts[0]  # MM/DD
            time_part = parts[1] if len(parts) > 1 else "00:00:00"
            
            month, day = map(int, date_part.split('/'))
            time_obj = datetime.datetime.strptime(time_part, '%H:%M:%S')
            
            # 현재 연도 사용
            result = now.replace(
                month=month, 
                day=day, 
                hour=time_obj.hour, 
                minute=time_obj.minute, 
                second=time_obj.second, 
                microsecond=0
            )
            
            # 미래 날짜면 작년으로 설정
            if result > now:
                result = result.replace(year=now.year - 1)
            
            return result
    
    except Exception as e:
        print(f"시간 파싱 실패 ({time_text}): {e}")
        return None


def to_iso8601(dt):
    """datetime 객체를 ISO 8601 형식 문자열로 변환"""
    if not dt:
        return None
    return dt.isoformat()


def filter_by_time(items, minutes=30):
    """
    주어진 시간(분) 이내에 작성된 게시글만 필터링
    """
    kst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(kst)
    cutoff_time = now - datetime.timedelta(minutes=minutes)
    
    filtered = []
    for item in items:
        crawled_at = item.get('crawledAt')
        if not crawled_at:
            continue
        
        post_time = datetime.datetime.fromisoformat(crawled_at)
        if post_time >= cutoff_time:
            filtered.append(item)
    
    return filtered


def extract_number_from_text(text):
    """텍스트에서 숫자 추출"""
    if not text:
        return None
    
    # 쉼표 제거
    text = text.replace(',', '')
    
    # 숫자만 추출
    match = re.search(r'\d+', text)
    if match:
        return int(match.group())
    
    return None


def extract_shipping_fee(text):
    """배송비 추출"""
    if not text:
        return None
    
    if any(kw in text for kw in ['무배', '무료', '무료배송', '공짜', '0원']):
        return "무료배송"
    
    number = extract_number_from_text(text)
    if number:
        return str(number)
    
    return text


# ========================================
# scraper.py 내용 복사
# ========================================

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup


class PpomppuScraper:

    def __init__(self):
        self.url = 'https://www.ppomppu.co.kr/zboard/zboard.php?id=ppomppu'
        self.source_site = 'PPOMPPU'
        self.main_url = 'https://www.ppomppu.co.kr/zboard/'
        self.max_pages = 3  # 최대 페이지 제한 (무한 루프 방지)
        self.test_mode = False

        # 환경 변수에서 필터링 시간 읽기 (기본값 30분)
        self.filter_minutes = int(os.environ.get('FILTER_MINUTES', 30))

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
            print(f"Chrome 브라우저 시작 : {self.url}")

            while page_num <= self.max_pages:
                print(f"\n{page_num}페이지 크롤링...")

                # ✅ 같은 driver 재사용
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
                crawled_at_str = last_item.get('crawledAt', '')
                print(f"crawled_at_str = {crawled_at_str}")

                # ✅ 수정: crawledAt이 ISO 형식인지 확인 후 적절한 파싱 수행
                last_time = None
                if crawled_at_str:
                    try:
                        # ISO 8601 형식이면 직접 변환
                        if 'T' in crawled_at_str and ('+' in crawled_at_str or 'Z' in crawled_at_str):
                            last_time = datetime.datetime.fromisoformat(crawled_at_str)
                        else:
                            # 원본 텍스트 형식이면 parse_time 사용
                            last_time = parse_time(crawled_at_str)
                    except Exception as e:
                        print(f"시간 파싱 중 오류: {e}")
                        last_time = None

                if not last_time:
                    print(f"시간 파싱 실패, 크롤링 종료")
                    break

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
            return all_items            # 수집된 데이터라도 반환

        finally:
            if driver:
                try:
                    driver.quit()
                    print("Chrome 브라우저 정상 종료")
                except Exception as e:
                    print(f"Chrome 종료 중 에러: {e}")

    def _create_driver(self):
        """로컬 환경용 드라이버 생성"""
        options = Options()

        # 로컬 테스트용 설정
        print("로컬 환경에서 Chrome 드라이버 생성 중...")
        
        # User-Agent 설정
        options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # 일반 옵션
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--referer=https://www.google.com/')
        
        # 자동화 감지 우회
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # headless 모드 (테스트 시 주석 처리하면 브라우저 확인 가능)
        # options.add_argument('--headless=new')

        try:
            driver = webdriver.Chrome(options=options)
            print("Chrome 드라이버 생성 성공!")

            # WebDriver 속성 숨기기
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.set_page_load_timeout(60)
            return driver
            
        except Exception as e:
            print(f"Chrome 드라이버 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _scrape_page(self, driver, page_num):
        """
        개별 페이지 크롤링
        """
        items = []
        html = None

        try:
            if page_num == 1:
                url = self.url
            else:
                url = f"{self.url}&page={page_num}"

            driver.get(url)

            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '#revolution_main_table'))
                )
                print("게시글 로드 확인")
            except Exception as e:
                # 타임아웃 되어도 계속 진행 (부분 데이터라도 수집)
                print(f"명시적 대기 타임아웃 (계속 진행): {e}")

            # HTML 파싱
            html = driver.page_source
            soup = BeautifulSoup(html, 'lxml')

            # 게시글 목록
            rows = soup.select('#revolution_main_table tbody tr.baseList')
            print(f"페이지 {page_num}: {len(rows)}개 발견")

            # 다른 선택자들도 시도
            if len(rows) == 0:
                print(f"  [DEBUG] 다른 선택자 시도...")
                alternative_rows = soup.select('#revolution_main_table')
                print(f"  [DEBUG] 대체 선택자: {len(alternative_rows)}개")

            for row in rows:
                try:
                    # 필터링 : 공지 / 광고 제외
                    if self._is_excluded(row):
                        continue

                    # 데이터 추출
                    item = self._extract_item(row)
                    if item:
                        items.append(item)

                except Exception as e:
                    print(f"게시글 파싱 실패: {e}")
                    continue

        except Exception as e:
            print(f"페이지 로딩 실패: {e}")
            import traceback
            traceback.print_exc()

        finally:
            html = None
            soup = None

        return items

    def _is_excluded(self, row):
        """
        제외 조건:
        - 글번호 영역에 <img> 태그 포함 (쇼핑뽐뿌, 핫딜, 쇼핑포럼)
        """
        numb_cell = row.select_one('td.baseList-space.baseList-numb')
        if numb_cell and numb_cell.find('img'):
            return True

        return False

    def _extract_item(self, row):
        """
        세일정보 추출
        """
        # 제목
        title_element = row.select_one('a.baseList-title')
        raw_title = title_element.get_text(strip=True) if title_element else None

        # (가격/배송비)
        pattern = r'\(([0-9,\.]+)원?\s*/\s*(.+?)\)\s*$'
        match = re.search(pattern, raw_title)

        # 제목 (가격/배송비) 제거
        if match:
            title = raw_title[:match.start()].strip()
            # 가격/배송비 추출
        else:
            title = raw_title  # 패턴 없으면 원본 제목 사용

        price = None
        shipping_fee = None

        if match:
            # 가격
            price_text = match.group(1).replace(',', '')
            try:
                if '만' in raw_title:
                    price = int(float(price_text) * 10000)
                else:
                    price = int(float(price_text))
            except:
                pass

            # 배송비
            shipping_text = match.group(2).strip()
            if any(kw in shipping_text for kw in ['무배', '무료', '무료배송', '공짜', '0']):
                shipping_fee = "무료배송"
            elif shipping_text.replace(',', '').isdigit():
                fee = int(shipping_text.replace(',', ''))
                shipping_fee = f"{fee}"
            else:
                shipping_fee = shipping_text

        # 판매처 : 제목에서 추출
        store = None
        store_element = title_element.select_one('em.baseList-head.subject_preface')
        if store_element:
            store = store_element.get_text(strip=True).strip('[]')
            store = clean_store_name(store)
        else:
            store = '기타'

        # 댓글 수
        reply_count = 0
        reply_element = row.select_one('span.baseList-c')
        if reply_element:
            reply_count = reply_element.get_text(strip=True)


        # 좋아요 수 (추천 - 비추천)
        like_count = 0
        like_element = row.select_one('td.baseList-rec')
        like_text = like_element.get_text(strip=True)
        if like_element:
            pattern = r"(\d+)\s*-\s*(\d+)"
            match = re.search(pattern, like_text)
            if match:
                like = int(match.group(1))
                dislike = int(match.group(2))
                like_count = like + dislike

        # 등록 시간
        time = None
        time_element = row.select_one('time.baseList-time')
        if time_element:
            time_text = time_element.get_text(strip=True)
            time_obj = parse_time(time_text)
            time = to_iso8601(time_obj) if time_obj else None

            time = parse_time(time_text)
            print(f"time_obj : {time_obj}")
            print(f"time : {time}")

        # 카테고리
        category_element = row.select_one('small.baseList-small')
        category = category_element.get_text(strip=True) if category_element else None
        category = clean_store_name(category)

        # URL
        href = title_element.get('href', '')
        if not href:
            print(f" href 속성 없음 (제목: {raw_title[:30]}...)")
            return None
        product_url = self.main_url + href

        # 이미지 url
        image_element = row.select_one('a.baseList-thumb img')
        image_url = image_element.get('src') if image_element else None

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


# ========================================
# 메인 실행
# ========================================

if __name__ == "__main__":
    print("=" * 60)
    print("뽐뿌 크롤러 로컬 테스트")
    print("=" * 60)
    print()
    
    try:
        # 크롤러 실행
        scraper = PpomppuScraper()
        results = scraper.scrape()
        
        print("\n" + "=" * 60)
        print("크롤링 결과 요약")
        print("=" * 60)
        print(f"총 수집 항목: {len(results)}개")
        
        if results:
            print("\n최근 5개 항목:")
            for i, item in enumerate(results[:5], 1):
                print(f"\n{i}. {item['title'][:50]}...")
                print(f"   판매처: {item.get('storeName', 'N/A')}")
                print(f"   가격: {item.get('price', 'N/A')}원")
                print(f"   배송비: {item.get('shippingFee', 'N/A')}")
                print(f"   시간: {item.get('crawledAt', 'N/A')}")
            
            # 결과를 JSON 파일로 저장
            output_file = 'ppomppu_test_result.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\n전체 결과가 '{output_file}' 파일로 저장되었습니다.")
        
        print("\n" + "=" * 60)
        print("테스트 완료!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
