# Incident #003 — ECS User Service OOM During Traffic Spike

## Date
2025-05-22 19:45 UTC

## Duration
18 minutes

## Severity
P2 — user service degraded, profile and settings pages unavailable

## Summary
The user-service ECS tasks were OOMKilled during an unexpected traffic spike following a viral social media post. Tasks cycled repeatedly and the service fell to 0 running tasks for approximately 8 minutes before auto-scaling launched replacement tasks.

## Root Cause
The user-service task definition allocated 512MB memory. A new feature released in v2.5.0 cached user profile images in memory (a bug — images should have been stored in S3). Under load, each task grew to 600MB+ and was killed by the ECS OOM reaper. Auto-scaling launched new tasks but they also hit the cache bug and were killed, causing a restart loop.

## Timeline
- 19:45 — Traffic spike begins (social media referral, 8x normal user service load)
- 19:47 — First ECS task OOMKilled (exit code 137)
- 19:48 — Auto-scaling triggers, launches 3 new tasks
- 19:51 — All 3 new tasks also OOMKilled within 90 seconds of starting
- 19:53 — RunningTaskCount = 0; user service completely down
- 19:58 — On-call engineer identifies OOM pattern in ECS events
- 20:01 — Hotfix deployed: disabled in-memory image cache (images fetched from S3 directly)
- 20:03 — Tasks start successfully, service recovers

## Resolution
Deployed hotfix removing in-memory image caching. Increased task memory limit to 1024MB as short-term buffer. Images now retrieved from S3 on each request (latency increase acceptable until proper CDN caching is implemented).

## Action Items
- Implement CloudFront CDN for user profile images to reduce S3 latency
- Add memory usage metric (via CloudWatch Agent sidecar) to ECS task definition
- Set ECS alarm on RunningTaskCount < DesiredTaskCount for more than 2 minutes
- Add code review requirement for any new in-memory caching of unbounded data structures

## Lessons Learned
Memory limits in task definitions must account for worst-case load, not average load. A new feature that passes code review in isolation can introduce a memory growth pattern that is only visible at scale. Load testing new features under realistic traffic is essential before production release.
