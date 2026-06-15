from unittest.mock import patch

from server.tools import cloudwatch_tools


def test_get_cloudwatch_alarms_filters_by_state():
    mock_response = {
        "MetricAlarms": [
            {
                "AlarmName": "high-error-rate",
                "StateValue": "ALARM",
                "StateReason": "Threshold crossed",
                "MetricName": "Errors",
                "Namespace": "AWS/Lambda",
                "Threshold": 5.0,
                "ComparisonOperator": "GreaterThanThreshold",
                "StateUpdatedTimestamp": "2025-01-01T00:00:00Z",
                "AlarmDescription": "Too many errors",
            }
        ]
    }

    with patch.object(cloudwatch_tools.cw, "describe_alarms", return_value=mock_response) as mock_describe:
        result = cloudwatch_tools.get_cloudwatch_alarms(state="ALARM")

    mock_describe.assert_called_once_with(StateValue="ALARM")
    assert result[0]["name"] == "high-error-rate"
    assert result[0]["state"] == "ALARM"
    assert result[0]["threshold"] == 5.0


def test_get_cloudwatch_alarms_all_state_returns_everything():
    with patch.object(cloudwatch_tools.cw, "describe_alarms", return_value={"MetricAlarms": []}) as mock_describe:
        result = cloudwatch_tools.get_cloudwatch_alarms(state="ALL")

    mock_describe.assert_called_once_with()
    assert result == []


def test_get_cloudwatch_alarms_sorted_by_last_updated_desc():
    mock_response = {
        "MetricAlarms": [
            {
                "AlarmName": "older-alarm",
                "StateValue": "ALARM",
                "StateUpdatedTimestamp": "2025-01-01T00:00:00Z",
            },
            {
                "AlarmName": "newer-alarm",
                "StateValue": "ALARM",
                "StateUpdatedTimestamp": "2025-02-01T00:00:00Z",
            },
        ]
    }

    with patch.object(cloudwatch_tools.cw, "describe_alarms", return_value=mock_response):
        result = cloudwatch_tools.get_cloudwatch_alarms(state="ALARM")

    assert [a["name"] for a in result] == ["newer-alarm", "older-alarm"]
