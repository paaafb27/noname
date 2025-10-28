import requests
import time

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
                json={'site': site, 'items': items},
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

                # 재시도 (5xx)
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

        except requests.exceptions.HTTPError as http_err:
            print(f"❌ HTTP 에러 발생: {http_err}")
            print(f"    - Status Code: {response.status_code}")
            print(f"    - Response Body: {response.text}")  # 가장 중요한 로그!

        except requests.exceptions.RequestException as req_err:
            print(f"❌ 네트워크 관련 에러 발생: {req_err}")  # DNS, 연결 거부 등

        except json.JSONDecodeError:
            print("❌ JSON 파싱 에러 발생: 서버가 유효한 JSON을 반환하지 않았습니다.")
            print(f"    - Status Code: {response.status_code}")
            print(f"    - Response Body: {response.text}")  # HTML 에러 페이지 등이 반환되었을 수 있음

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

