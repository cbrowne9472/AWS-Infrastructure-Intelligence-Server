# API Gateway 5xx Errors Runbook

## Symptoms
- API Gateway returning 502 Bad Gateway or 504 Gateway Timeout to clients
- `5XXError` or `IntegrationLatency` CloudWatch metrics elevated
- Downstream Lambda or HTTP integration reporting errors

## Diagnostic Steps
1. Check API Gateway CloudWatch metrics: `5XXError`, `IntegrationLatency`, `Count`
2. Distinguish 502 vs 504:
   - **502**: Integration (Lambda/HTTP) returned a malformed response
   - **504**: Integration exceeded the API Gateway timeout (29 seconds max)
3. For 502: Check Lambda logs for unhandled exceptions or malformed return values (missing statusCode field)
4. For 504: Check Lambda duration — if p99 exceeds 29s, the request will always time out at API Gateway
5. Check Lambda concurrency limits — if Lambda is throttling, API Gateway gets 429 → may surface as 502
6. Review API Gateway access logs for the specific endpoint and method returning errors
7. Check if a recent deployment changed the Lambda response format

## Resolution
- **502 malformed response**: Fix the Lambda to always return `{"statusCode": 200, "body": "..."}` format
- **504 timeout**: Reduce Lambda execution time or break the work into async jobs with polling
- **Lambda throttling causing 502**: Request a concurrency limit increase for the Lambda function
- **Intermittent 502 after deploy**: Roll back the Lambda alias/version if the new code introduced a bug

## Prevention
- Never exceed 25s Lambda execution time for synchronous API Gateway integrations (leaves 4s buffer)
- Use Lambda aliases with weighted routing for gradual deployments
- Set API Gateway access logging to catch patterns before they escalate
- Validate Lambda response format in unit tests — missing `statusCode` is a common cause of 502
