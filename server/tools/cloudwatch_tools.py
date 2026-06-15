from server.config import get_client

cw = get_client("cloudwatch")


def get_cloudwatch_alarms(state: str = "ALARM") -> list[dict]:
    """
    state options: ALARM | OK | INSUFFICIENT_DATA
    Pass state=ALL to get all alarms regardless of state.
    """
    kwargs = {}
    if state != "ALL":
        kwargs["StateValue"] = state

    response = cw.describe_alarms(**kwargs)
    alarms = []

    for alarm in response.get("MetricAlarms", []):
        alarms.append(
            {
                "name": alarm["AlarmName"],
                "state": alarm["StateValue"],
                "reason": alarm.get("StateReason", ""),
                "metric": alarm.get("MetricName", ""),
                "namespace": alarm.get("Namespace", ""),
                "threshold": alarm.get("Threshold"),
                "comparison": alarm.get("ComparisonOperator", ""),
                "last_updated": str(alarm.get("StateUpdatedTimestamp", "")),
                "description": alarm.get("AlarmDescription", ""),
            }
        )

    return sorted(alarms, key=lambda x: x["last_updated"], reverse=True)
