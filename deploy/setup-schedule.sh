SITE=$1

# 스케줄 규칙 생성 (10분마다)
aws events put-rule \
    --name scandeals-$SITE-schedule \
    --schedule-expression "rate(10 minutes)" \
    --state ENABLED

# Lambda 타겟 설정
aws events put-targets \
    --rule scandeals-$SITE-schedule \
    --targets "Id"="1","Arn"="arn:aws:lambda:ap-northeast-2:YOUR_ACCOUNT_ID:function:scandeals-$SITE"

# Lambda 권한 부여
aws lambda add-permission \
    --function-name scandeals-$SITE \
    --statement-id scandeals-$SITE-schedule \
    --action 'lambda:InvokeFunction' \
    --principal events.amazonaws.com \
    --source-arn arn:aws:events:ap-northeast-2:YOUR_ACCOUNT_ID:rule/scandeals-$SITE-schedule

echo "✅ EventBridge 스케줄 설정 완료"