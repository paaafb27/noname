from datetime import datetime


def log_item(item):

    if not item or not isinstance(item, dict):
        print("  [DEBUG] 로깅할 아이템이 없거나 형식이 올바르지 않습니다.")
        return

    field_order = [
        'title', 'price', 'shippingFee', 'storeName', 'category',
        'productUrl', 'imageUrl', 'replyCount', 'likeCount',
        'sourceSite', 'crawledAt'
    ]

    log_parts = []

    # 정의된 순서대로 필드를 처리
    for field in field_order:
        if field in item:
            value = item[field]

            # 값이 None이면 'N/A'로 표시
            if value is None:
                value = 'N/A'

            if field == 'crawledAt' and value and isinstance(value, str) and 'T' in value:
                try:
                    # ISO 8601 문자열을 datetime 객체로 변환
                    dt_obj = datetime.fromisoformat(value)
                    # 'YYYY-MM-DD HH:MM:SS' 형식으로 변환
                    value = dt_obj.strftime('%Y-%m-%d %H:%M:%S')
                except ValueError:
                    pass  # 파싱 실패 시 원본 값 그대로 사용
            log_parts.append(f"{field}: {value}")

    # 정의되지 않은 나머지 필드들도 뒤에 추가
    for key, value in item.items():
        if key not in field_order:
            log_parts.append(f"{key}: {value if value is not None else 'N/A'}")

    log_message = " | ".join(log_parts)

    print(f"{log_message}")
    print("==================================================")