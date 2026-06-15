from datetime import datetime, timedelta, timezone

from server.config import get_client

cw = get_client("cloudwatch")
lc = get_client("lambda")


def list_lambdas() -> list[dict]:
    response = lc.list_functions()
    return [
        {
            "name": fn["FunctionName"],
            "runtime": fn.get("Runtime", "N/A"),
            "memory_mb": fn["MemorySize"],
            "timeout_seconds": fn["Timeout"],
            "last_modified": fn["LastModified"],
        }
        for fn in response.get("Functions", [])
    ]


def get_lambda_metrics(function_name: str, hours: int = 24) -> dict:
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=hours)
    period = 3600  # 1 hour periods

    def get_metric(metric_name: str, stat: str) -> list:
        response = cw.get_metric_statistics(
            Namespace="AWS/Lambda",
            MetricName=metric_name,
            Dimensions=[{"Name": "FunctionName", "Value": function_name}],
            StartTime=start_time,
            EndTime=end_time,
            Period=period,
            Statistics=[stat],
        )
        return sorted(
            [{"timestamp": str(dp["Timestamp"]), "value": dp[stat]} for dp in response["Datapoints"]],
            key=lambda x: x["timestamp"],
        )

    invocations = get_metric("Invocations", "Sum")
    errors = get_metric("Errors", "Sum")
    duration_p99 = get_metric("Duration", "p99")
    duration_avg = get_metric("Duration", "Average")
    throttles = get_metric("Throttles", "Sum")

    total_invocations = sum(dp["value"] for dp in invocations)
    total_errors = sum(dp["value"] for dp in errors)
    error_rate = (total_errors / total_invocations * 100) if total_invocations > 0 else 0

    return {
        "function_name": function_name,
        "time_range_hours": hours,
        "summary": {
            "total_invocations": total_invocations,
            "total_errors": total_errors,
            "error_rate_percent": round(error_rate, 2),
            "total_throttles": sum(dp["value"] for dp in throttles),
        },
        "duration_p99_ms": duration_p99,
        "duration_avg_ms": duration_avg,
        "invocations_per_hour": invocations,
        "errors_per_hour": errors,
    }
