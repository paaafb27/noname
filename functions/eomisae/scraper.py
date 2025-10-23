"""
EOMISAE 크롤러

URL: https://eomisae.co.kr/
"""
import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import sys
import os
import re

from common.number_extractor import extract_price_from_title
from common.filter_by_regtime import filter_by_time, parse_time

# common 모듈
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))


class EomisaeScraper:

    def __init__(self):
        self.urls = [
            'https://eomisae.co.kr/os', # 패션정보
            'https://eomisae.co.kr/rt'  # 기타정보
            ]
        self.main_url = 'https://eomisae.co.kr/'
        self.source_site = 'EOMISAE'
        self.max_pages = 5

    def scrape(self):

        all_items = []

        # 각 게시판 크롤링
        for url in self.urls:
            print(f"게시판 크롤링: {url}")
            items = self._scrape_with_pagination(url)
            all_items.extend(items)

        return all_items

    def _scrape_with_pagination(self, url):
        """
        - 페이지의 마지막 게시글이 30분 이내면 다음 페이지 계속 확인
        - 마지막 게시글이 30분 초과하거나 최대 페이지 도달 시 중단
        """
        all_items = []
        page_num = 1
        cutoff_time = datetime.datetime.now() - datetime.timedelta(minutes=30)

        while page_num <= self.max_pages:
            print(f"\n{page_num}페이지 크롤링 중...")

            page_items = self._scrape_page(page_num, url)

            if not page_items:
                print(f"{page_num}페이지: 게시글 없음, 종료")
                break

            # 30분 이내 작성된 게시글 필터링
            page_filtered = filter_by_time(page_items, minutes=30)
            all_items.extend(page_filtered)
            print(f"{page_num}페이지: {len(page_items)}개 → 필터링 {len(page_filtered)}개")

            # 다음 페이지 확인 여부 판단
            # 원본(page_items)의 마지막 게시글 시간으로 판단
            last_item = page_items[-1]
            last_time = parse_time(last_item.get('crawledAt', ''))

            if not last_time:
                print(f"  → 시간 파싱 실패, 크롤링 종료")
                break

            # 마지막 게시글 등록 시간이 30분 초과면 중단
            if last_time < cutoff_time:
                print(f"→ 마지막 게시글 30분 초과 ({last_time.strftime('%H:%M:%S')}), 종료")
                break

            print(f"→ 마지막 게시글 30분 이내 ({last_time.strftime('%H:%M:%S')}), 다음 페이지 확인")
            page_num += 1

        if page_num > self.max_pages:
            print(f"\n⚠️ 최대 페이지({self.max_pages}) 도달, 크롤링 종료")

        print(f"\n✅ 총 {len(all_items)}개 수집 완료")
        return all_items

    def _scrape_page(self, page_num, targetUrl):
        """특정 페이지 크롤링"""
        items = []

        options = Options()
        # image/css 차단 for 속도 향상
        options.add_experimental_option(
            "prefs", {
                "profile.managed_default_content_settings.images": 2,
                "profile.managed_default_content_settings.stylesheets": 2
            }
        )
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--single-process')
        options.binary_location = '/opt/chrome/chrome'  # Lambda Chrome 경로

        driver = webdriver.Chrome(
            executable_path='/opt/chromedriver',
            options=options
        )

        try:
            # 페이지 URL
            if page_num == 1:
                url = targetUrl
            else:
                if 'os' in targetUrl:   # 패션
                    url = f"https://eomisae.co.kr/index.php?mid=os&page={page_num}"
                else:
                    url = f"https://eomisae.co.kr/index.php?mid=rt&page={page_num}"

            driver.get(url)
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # HTML 파싱
            html = driver.page_source
            soup = BeautifulSoup(html, 'lxml')

            # 게시글 목록
            cards = soup.select('div.card_el.n_ntc.clear')
            print(f"게시글 {len(cards)}개 발견")

            for card in cards:
                try:
                    # 필터링
                    title_element = card.select_one('a.pjax')
                    title = title_element.get_text(strip=True)

                    # 레벨 미달 제외
                    if re.search(r'\d+분\s*뒤\s*전체\s*공개로\s*전환됩니다', title):
                        print(f"[어미새] 레벨 미달 제외: {title[:40]}...")
                        continue
                    # "미달 조건 : 레벨" 패턴
                    elif '미달 조건' in title and '레벨' in title:
                        print(f"[어미새] 레벨 미달 제외: {title[:40]}...")
                        continue

                    # 데이터 추출
                    item = self._extract_item(card)
                    if item:
                        items.append(item)

                except Exception as e:
                    print(f"게시글 파싱 실패: {e}")
                    continue

        except Exception as e:
            print(f"    페이지 로딩 실패: {e}")

        finally:
            driver.quit()

        return items

    def _extract_item(self, card):
        """
        세일정보 추출
        """
        # 제목
        title_element = card.locator('a.pjax')
        if not title_element:
            return None
        title = title_element.get_text(strip=True)

        # URL
        product_url = title_element['href']

        # 판매처: 제목 첫 단어
        # ex) "금강제화 더비" → "금강제화"
        #first_word = title.split()[0] if title else '기타'
        store = ''

        # 가격 : 일관된 형식 없음
        price = extract_price_from_title(title)

        # 배송비
        # title에 '무배' 키워드가 있으면 0 없으면 ''
        shipping_fee = ''

        # 등록 시간
        time_element = card.select_one('div.card_content span:nth-of-type(2):not(.fr)')
        time = time_element.get_text(strip=True) if time_element else ''

        # 댓글 수
        reply_element = card.select_one('div.card_content span:nth-of-type(2).fr')
        reply_count = reply_element.get_text(strip=True) if reply_element else None

        # 추천 수
        like_element = card.select_one('div.card_content span:nth-of-type(3).fr')
        like_count = like_element.get_text(strip=True) if like_element else None

        # 이미지 url
        img_element = card.select_one('div.tmb_wrp img.tmb')
        image_url = img_element['src'] if img_element else None

        return {
            'title': title,
            'price': price,
            'storeName': store,
            #'category': category,
            'shippingFee': shipping_fee,
            'productUrl': product_url,
            'imageUrl': image_url,
            'replyCount': reply_count,
            'likeCount': like_count,
            'sourceSite': self.source_site,
            'crawledAt': time
        }