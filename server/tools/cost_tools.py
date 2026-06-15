from datetime import date, datetime

from dateutil.relativedelta import relativedelta

from server.config import get_client

ce = get_client("ce", region_name="us-east-1")  # Cost Explorer is always us-east-1


def get_cost_by_service(month: str = "current") -> dict:
    today = date.today()

    if month == "current":
        start = today.replace(day=1).strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")
    elif month == "last":
        first_of_current = today.replace(day=1)
        last_month_end = first_of_current - relativedelta(days=1)
        start = last_month_end.replace(day=1).strftime("%Y-%m-%d")
        end = first_of_current.strftime("%Y-%m-%d")
    else:
        start = month + "-01"
        end = (datetime.strptime(start, "%Y-%m-%d") + relativedelta(months=1)).strftime("%Y-%m-%d")

    response = ce.get_cost_and_usage(
        TimePeriod={"Start": start, "End": end},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
    )

    services = []
    total = 0.0

    for group in response["ResultsByTime"][0]["Groups"]:
        cost = float(group["Metrics"]["UnblendedCost"]["Amount"])
        if cost > 0.001:
            services.append({"service": group["Keys"][0], "cost_usd": round(cost, 4)})
            total += cost

    return {
        "period": f"{start} to {end}",
        "total_usd": round(total, 4),
        "by_service": sorted(services, key=lambda x: x["cost_usd"], reverse=True),
    }


def get_cost_trend() -> dict:
    current = get_cost_by_service("current")
    last = get_cost_by_service("last")
    delta = current["total_usd"] - last["total_usd"]
    return {
        "current_month_usd": current["total_usd"],
        "last_month_usd": last["total_usd"],
        "delta_usd": round(delta, 4),
        "trend": "up" if delta > 0 else "down",
        "current_breakdown": current["by_service"],
        "last_breakdown": last["by_service"],
    }
