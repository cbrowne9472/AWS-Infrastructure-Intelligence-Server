# IAM Permission Errors Runbook

## Symptoms
- `AccessDeniedException` or `UnauthorizedOperation` in application logs
- CloudTrail showing explicit deny or no matching allow for an API call
- Service failing to start because it cannot assume its IAM role

## Diagnostic Steps
1. Find the exact denied action in CloudTrail:
   - Filter by `errorCode = AccessDenied` or `UnauthorizedOperation`
   - Note the `userIdentity.arn`, `eventName`, and `resources` fields
2. Use IAM Policy Simulator to test the role against the specific action and resource
3. Check for explicit Deny statements — a Deny always overrides any Allow:
   - Service Control Policies (SCPs) at the AWS Organization level
   - Permission boundaries on the role
   - Resource-based policies (bucket policy, KMS key policy, etc.) with explicit Deny
4. Verify the correct role is being assumed — check the instance profile or task role attachment
5. For cross-account: verify the trust policy allows the source account/role to assume this role

## Common Causes
- **Missing action**: IAM policy allows `s3:PutObject` but not `s3:GetBucketLocation` (required by SDK)
- **Wrong resource ARN**: Policy scoped to `arn:aws:s3:::my-bucket/*` but action needs `arn:aws:s3:::my-bucket` (no slash)
- **SCP blocking**: Organization SCP restricts an action that the role's own policy allows
- **Condition mismatch**: Policy has `Condition: {"StringEquals": {"s3:prefix": "uploads/"}}` that the request doesn't satisfy
- **Role not attached**: EC2 instance or ECS task doesn't have the IAM role attached

## Resolution
- Add the missing action to the IAM role policy, scoped to the minimum necessary resource
- Fix the resource ARN format (bucket vs. object vs. both are often both needed)
- Work with the platform/security team to adjust SCPs or permission boundaries
- Attach the correct instance profile to the EC2 instance (requires stop/start, not just restart)

## Prevention
- Use IAM Access Analyzer to surface overly permissive and overly restrictive policies
- Test with least-privilege from day one — it is much harder to reduce permissions later
- Use `aws iam simulate-principal-policy` in CI to catch permission regressions before deployment
- Never use `AdministratorAccess` for application roles — scope to the exact actions needed
