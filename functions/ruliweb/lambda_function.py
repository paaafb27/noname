"""
크롤러 Lambda 함수

연동: Spring Boot CrawlDataController
"""

import json
import os
from datetime import time

from scraper import RuliwebScraper
from common.api_client import send_to_spring_boot

# 환경 변수
API_URL = os.environ.get('API_URL')  # Spring Boot API
API_KEY = os.environ.get('API_KEY')  # 인증 키
SITE_NAME = 'RULIWEB'              # SourceSite enum 값

######################################################################

def lambda_handler(event, context):
    """
    Lambda 핸들러

    EventBridge가 10분마다 호출
    """
    start_time = time.time()

    try:
        print(f"[{SITE_NAME}] 크롤링 시작 ...")

        # 1. 크롤링 실행
        scraper = RuliwebScraper()
        items = scraper.scrape()

        print(f"[{SITE_NAME}] 크롤링 완료: {len(items)}개 수집")

        # 2. Spring Boot API 전송
        if items:
            result = send_to_spring_boot(
                api_url = API_URL,
                api_key = API_KEY,
                site = SITE_NAME,
                items = items
            )

            print(f"API 전송 완료 : {result}")

            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'site': SITE_NAME,
                    'total_items': len(items),
                    'api_result': result
                }, ensure_ascii=False)
            }
        else:
            message = "30분 이내 게시글 없음"
            print(message)

            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'site': SITE_NAME,
                    'total_items': 0,
                    'message': message
                }, ensure_ascii=False)
            }

    except Exception as e:
        print(f"[{SITE_NAME}] 에러: {str(e)}")
        import traceback
        traceback.print_exc()

        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'site': SITE_NAME,
                'error': str(e)
            }, ensure_ascii=False)
        }