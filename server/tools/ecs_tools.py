from server.config import get_client

ecs = get_client("ecs")


def get_ecs_services(cluster_name: str) -> list[dict]:
    service_arns = ecs.list_services(cluster=cluster_name)["serviceArns"]
    if not service_arns:
        return []

    services = ecs.describe_services(cluster=cluster_name, services=service_arns)
    return [
        {
            "name": svc["serviceName"],
            "status": svc["status"],
            "desired_count": svc["desiredCount"],
            "running_count": svc["runningCount"],
            "pending_count": svc["pendingCount"],
            "task_definition": svc["taskDefinition"].split("/")[-1],
            "launch_type": svc.get("launchType", "FARGATE"),
            "health": "healthy" if svc["runningCount"] >= svc["desiredCount"] else "degraded",
        }
        for svc in services["services"]
    ]


def list_ecs_clusters() -> list[str]:
    arns = ecs.list_clusters()["clusterArns"]
    return [arn.split("/")[-1] for arn in arns]
