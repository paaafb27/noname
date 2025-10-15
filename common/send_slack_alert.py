from datetime import time

import requests
import os

"""
    slack 웹훅으로 알림 전송
"""
def send_slack_alert(title, message, level='error'):
    webhook_url = os.environ.get('SLACK_WEBHOOK_ULR')

    if not webhook_url:
        return

    colors = {
        'error': '#ff0000',     # 빨강
        'warning': '#ffa500',   # 주황
        'info': '#00ff00'       # 초록
    }

    payload = {
        'attachments': [{
            'color': colors.get(level, '#808080'),
            'title': title,
            'text': message,
            'footer': 'scanDeals Lambda Crawler',
            'ts': int(time.time())
        }]
    }

    try:
        requests.post(webhook_url, json=payload, timeout=5)
    except:
        pass