from datetime import datetime, timezone
from unittest.mock import patch

from server.tools import lambda_tools


def test_list_lambdas():
    mock_response = {
        "Functions": [
            {
                "FunctionName": "payment-processor",
                "Runtime": "nodejs18.x",
                "MemorySize": 512,
                "Timeout": 30,
                "LastModified": "2025-01-01T00:00:00.000+0000",
            }
        ]
    }

    with patch.object(lambda_tools.lc, "list_functions", return_value=mock_response):
        result = lambda_tools.list_lambdas()

    assert result == [
        {
            "name": "payment-processor",
            "runtime": "nodejs18.x",
            "memory_mb": 512,
            "timeout_seconds": 30,
            "last_modified": "2025-01-01T00:00:00.000+0000",
        }
    ]


def test_get_lambda_metrics_no_invocations():
    with patch.object(lambda_tools.cw, "get_metric_statistics", return_value={"Datapoints": []}):
        result = lambda_tools.get_lambda_metrics("payment-processor", hours=1)

    assert result["function_name"] == "payment-processor"
    assert result["time_range_hours"] == 1
    assert result["summary"]["total_invocations"] == 0
    assert result["summary"]["total_errors"] == 0
    assert result["summary"]["error_rate_percent"] == 0
    assert result["summary"]["total_throttles"] == 0


def test_get_lambda_metrics_calculates_error_rate():
    now = datetime.now(timezone.utc)

    def fake_metric_statistics(**kwargs):
        metric_name = kwargs["MetricName"]
        stat = kwargs["Statistics"][0]
        values = {
            "Invocations": 100.0,
            "Errors": 5.0,
            "Throttles": 2.0,
            "Duration": 250.0,
        }
        return {"Datapoints": [{"Timestamp": now, stat: values[metric_name]}]}

    with patch.object(lambda_tools.cw, "get_metric_statistics", side_effect=fake_metric_statistics):
        result = lambda_tools.get_lambda_metrics("payment-processor", hours=1)

    assert result["summary"]["total_invocations"] == 100.0
    assert result["summary"]["total_errors"] == 5.0
    assert result["summary"]["error_rate_percent"] == 5.0
    assert result["summary"]["total_throttles"] == 2.0
    assert result["duration_p99_ms"][0]["value"] == 250.0
