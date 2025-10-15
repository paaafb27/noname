import requests
import json
import time

from scraper import scraper

from common.send_slack_alert import send_slack_alert

"""
    Spring Boot API로 데이터 전송

    Args:
        api_url: API 엔드포인트 URL
        api_key: API 인증 키
        site: 출처 사이트명
        items: 세일 정보 리스트
        max_retries: 최대 재시도 횟수

    Returns:
        dict: API 응답 결과
"""
def send_to_spring_boot(api_url, api_key, site, items, max_retries=3):

    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': api_key
    }

    payload = {
        'site': site,
        'items': items
    }

    # 재시도 로직
    for attempt in range(max_retries):
        try:
            print(f"API 호출 시도 {attempt + 1}/{max_retries}")

            response = requests.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=60          # 60초
            )

            # 성공
            if response.status_code == 200:
                result = response.json()
                print(f"API 호출 성공: {result}")
                return result
            # 실패
            else:
                print(f"API 호출 실패 (HTTP {response.status_code}): {response.text}")

                # 재시도
                if 500 <= response.status_code < 600:
                    if attempt < max_retries -1:
                        wait_time = 2 ** attempt        # 지수 백오프 (1초, 2초, 4초)
                        print(f"{wait_time}초 후 재시도...")
                        time.sleep(wait_time)
                        continue

                # 재시도 불가능 (4xx)
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}",
                    'message': response.text
                }

        except requests.exceptions.Timeout:
            print(f"API 호출 타임아웃 (시도 {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue

        except Exception as e:
            print(f"API 호출 예외 발생: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue

    # 모든 재시도 실패
    return {
        'success': False,
        'error': 'Max retries exceeded',
        'message': f'{max_retries}번 재시도 후 실패'
    }


"""
    Lambda 핸들러 (독립 실패)

    한 사이트 크롤링 실패 시:
    - 다른 사이트는 정상 실행
    - 에러 로그 기록
    - CloudWatch 알림
"""
def lambda_handler(event, context):
    try:
        # 크롤링 실행
        items = scraper.scrape()

        # API 전송
        result = send_to_spring_boot(...)

        return {
            'statusCode': 200,
            'body': json.dumps({'success': True, ...})
        }

    except Exception as e:
        # 에러 처리
        error_message = f"크롤링 실패: {str(e)}"
        print(error_message)

        # CloudWatch Logs에 자동 기록
        import traceback
        traceback.print_exc()

        # 슬랙 알림
        send_slack_alert(error_message)

        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }