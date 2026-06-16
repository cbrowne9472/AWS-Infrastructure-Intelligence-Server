# Integration tests — require real AWS credentials in .env to pass.
# Run with: pytest server/tests/test_integration.py -v

from server.tools.cloudwatch_tools import get_cloudwatch_alarms
from server.tools.cost_tools import get_cost_by_service, get_cost_trend
from server.tools.ec2_tools import get_ec2_instances
from server.tools.ecs_tools import list_ecs_clusters
from server.tools.lambda_tools import get_lambda_metrics, list_lambdas
from server.tools.rds_tools import get_rds_instances
from server.tools.vpc_tools import get_vpc_info


def test_list_lambdas_returns_list():
    result = list_lambdas()
    assert isinstance(result, list)
    for fn in result:
        assert "name" in fn
        assert "runtime" in fn
        assert "memory_mb" in fn
        assert "timeout_seconds" in fn


def test_get_lambda_metrics_if_functions_exist():
    lambdas = list_lambdas()
    if not lambdas:
        return
    metrics = get_lambda_metrics(lambdas[0]["name"], hours=1)
    assert "function_name" in metrics
    assert "summary" in metrics
    assert "error_rate_percent" in metrics["summary"]


def test_get_cloudwatch_alarms_returns_list():
    result = get_cloudwatch_alarms(state="ALL")
    assert isinstance(result, list)
    for alarm in result:
        assert "name" in alarm
        assert "state" in alarm


def test_get_ec2_instances_returns_list():
    result = get_ec2_instances(state="ALL")
    assert isinstance(result, list)


def test_list_ecs_clusters_returns_list():
    result = list_ecs_clusters()
    assert isinstance(result, list)


def test_get_rds_instances_returns_list():
    result = get_rds_instances()
    assert isinstance(result, list)


def test_get_vpc_info_returns_list():
    result = get_vpc_info()
    assert isinstance(result, list)
    for vpc in result:
        assert "vpc_id" in vpc
        assert "subnets" in vpc


def test_get_cost_by_service_shape():
    result = get_cost_by_service("current")
    assert "total_usd" in result
    assert "by_service" in result
    assert "period" in result


def test_get_cost_trend_shape():
    result = get_cost_trend()
    assert "current_month_usd" in result
    assert "last_month_usd" in result
    assert "delta_usd" in result
    assert result["trend"] in ("up", "down")
