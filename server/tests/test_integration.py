# Integration tests — require real AWS + Pinecone + OpenAI credentials in .env.
# Run with: pytest server/tests/test_integration.py -v

from server.rag.knowledge_base import search_runbooks
from server.tools.cloudwatch_tools import get_cloudwatch_alarms
from server.tools.cost_tools import get_cost_by_service, get_cost_trend
from server.tools.ec2_tools import get_ec2_instances
from server.tools.ecs_tools import get_ecs_services, list_ecs_clusters
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


# --- Combined diagnostic flows ---


def test_lambda_diagnostic_flow():
    """Full Lambda diagnostic: live metrics + alarm state + runbook search."""
    lambdas = list_lambdas()
    assert isinstance(lambdas, list)

    if lambdas:
        fn_name = lambdas[0]["name"]
        metrics = get_lambda_metrics(fn_name, hours=1)
        assert "error_rate_percent" in metrics["summary"]
        assert "duration_p99_ms" in metrics
        assert "invocations_per_hour" in metrics

    alarms = get_cloudwatch_alarms(state="ALL")
    assert isinstance(alarms, list)

    kb_result = search_runbooks("Lambda timeout errors")
    assert "query" in kb_result
    assert "results_count" in kb_result
    assert isinstance(kb_result["results"], list)


def test_cost_analysis_flow():
    """Current spend breakdown + month-over-month trend in one pass."""
    current = get_cost_by_service("current")
    assert "total_usd" in current
    assert "by_service" in current
    assert isinstance(current["by_service"], list)

    trend = get_cost_trend()
    assert "delta_usd" in trend
    assert "trend" in trend
    assert trend["current_month_usd"] == current["total_usd"]


def test_alarms_to_runbook_flow():
    """Check active alarms, then search runbooks relevant to what's firing."""
    alarms = get_cloudwatch_alarms(state="ALL")
    assert isinstance(alarms, list)

    # Search for runbooks matching any firing alarm's metric name,
    # or fall back to a generic query if nothing is firing.
    firing = [a for a in alarms if a["state"] == "ALARM"]
    query = firing[0]["metric"] if firing else "AWS infrastructure incident"

    kb_result = search_runbooks(query)
    assert kb_result["results_count"] >= 0


def test_ecs_cluster_health_flow():
    """List clusters then check service health for each one found."""
    clusters = list_ecs_clusters()
    assert isinstance(clusters, list)

    for cluster_name in clusters[:2]:  # limit to first 2 to keep test fast
        services = get_ecs_services(cluster_name)
        assert isinstance(services, list)
        for svc in services:
            assert "name" in svc
            assert "health" in svc
            assert svc["health"] in ("healthy", "degraded")


def test_vpc_architecture_search_flow():
    """Fetch real VPC topology then search architecture docs for context."""
    vpcs = get_vpc_info()
    assert isinstance(vpcs, list)

    kb_result = search_runbooks("VPC subnets architecture", doc_type="architecture")
    assert "results" in kb_result
