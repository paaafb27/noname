import json
import os
from datetime import datetime
from scraper import RuliwebScraper
from common.api_client import send_to_spring_boot

API_URL = os.environ.get('API_URL')
API_KEY = os.environ.get('API_KEY')
SITE_NAME = 'RULIWEB'

def lambda_handler(event, context):
    try:
        print(f"[{SITE_NAME}] 크롤링 시작 ...")
        scraper = RuliwebScraper()
        items = scraper.scrape()
        print(f"[{SITE_NAME}] 크롤링 완료: {len(items)}개 수집")
        if items:
            result = send_to_spring_boot(
                api_url=API_URL,
                api_key=API_KEY,
                site=SITE_NAME,
                items=items
            )
            print(f"API 전송 완료 : {result}")
            return {'statusCode': 200, 'body': json.dumps({'success': True, 'site': SITE_NAME, 'total_items': len(items)})}
        else:
            return {'statusCode': 200, 'body': json.dumps({'success': True, 'site': SITE_NAME, 'message': '30분 이내 게시글 없음'})}
    except Exception as e:
        print(f"[{SITE_NAME}] 에러: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'statusCode': 500, 'body': json.dumps({'success': False, 'error': str(e)})}