# S3 Access Denied Runbook

## Symptoms
- `AccessDenied` errors when reading or writing to S3
- Lambda or ECS tasks failing with S3 permission errors
- CloudTrail showing `s3:GetObject` or `s3:PutObject` denied events

## Diagnostic Steps
1. Check CloudTrail for the exact denied API call, the principal ARN, and the bucket/key
2. Verify the IAM role attached to the compute resource has an S3 policy with the required actions
3. Check the S3 bucket policy — it may have an explicit Deny that overrides the IAM allow
4. Check if the bucket has Block Public Access settings that might conflict
5. Verify the bucket and the compute resource are in the same account — cross-account access requires both IAM and bucket policy grants
6. Check if the object is KMS-encrypted — the IAM role needs `kms:Decrypt` on the key too
7. Confirm the S3 endpoint or VPC routing if the resource is in a VPC

## Resolution
- Add the missing S3 actions (`s3:GetObject`, `s3:PutObject`, `s3:ListBucket`) to the IAM role policy
- Remove any explicit Deny from the bucket policy that blocks the role, or add an exception
- For cross-account: add a bucket policy granting the external account's role access
- For KMS: add `kms:Decrypt` and `kms:GenerateDataKey` to the IAM role for the key ARN

## Prevention
- Use IAM Access Analyzer to validate S3 permissions before deploying
- Test S3 access from the actual compute resource (not from your admin role) in staging
- Tag S3 buckets with the owning service so permission audits are easier
- Avoid wildcard resource `"*"` in bucket policies — always scope to the specific bucket ARN
