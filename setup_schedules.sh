#!/bin/bash

echo "================================================="
echo "   HypeMind AWS EventBridge Initializer Script   "
echo "================================================="

REGION="ap-south-1"
ACCOUNT_ID="433619996781"
LAMBDA_NAME="HypeMind-Agent"
LAMBDA_ARN="arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${LAMBDA_NAME}"

echo "Configuring Rule 1: HypeMind-ImagePoster (Every 6 hours) ..."

aws events put-rule \
    --name "HypeMind-ImagePoster" \
    --schedule-expression "rate(6 hours)" \
    --state "ENABLED" \
    > /dev/null

aws lambda add-permission \
    --function-name "$LAMBDA_NAME" \
    --statement-id "AllowEventBridge-ImagePoster-$(date +%s)" \
    --action "lambda:InvokeFunction" \
    --principal "events.amazonaws.com" \
    --source-arn "arn:aws:events:${REGION}:${ACCOUNT_ID}:rule/HypeMind-ImagePoster" \
    > /dev/null 2>&1 || true

aws events put-targets \
    --rule "HypeMind-ImagePoster" \
    --targets "Id=1,Arn=${LAMBDA_ARN},Input='{\"action\":\"post_scheduled\"}'" \
    > /dev/null

echo "✅ Rule 1 (Image Poster) configured successfully!"
echo "------------------------------------------------"


echo "Configuring Rule 2: HypeMind-VideoAdPoster (Every 1 day) ..."

aws events put-rule \
    --name "HypeMind-VideoAdPoster" \
    --schedule-expression "rate(1 day)" \
    --state "ENABLED" \
    > /dev/null

aws lambda add-permission \
    --function-name "$LAMBDA_NAME" \
    --statement-id "AllowEventBridge-VideoPoster-$(date +%s)" \
    --action "lambda:InvokeFunction" \
    --principal "events.amazonaws.com" \
    --source-arn "arn:aws:events:${REGION}:${ACCOUNT_ID}:rule/HypeMind-VideoAdPoster" \
    > /dev/null 2>&1 || true

aws events put-targets \
    --rule "HypeMind-VideoAdPoster" \
    --targets "Id=1,Arn=${LAMBDA_ARN},Input='{\"action\":\"post_video_ad\"}'" \
    > /dev/null

echo "✅ Rule 2 (Video Ad Poster) configured successfully!"
echo "================================================="
echo "Done! The EventBridge triggers are correctly mapped to your Lambda function payloads."
