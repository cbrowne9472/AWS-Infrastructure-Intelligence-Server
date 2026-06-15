from server.config import get_client

ec2 = get_client("ec2")


def get_ec2_instances(state: str = "running") -> list[dict]:
    filters = []
    if state != "ALL":
        filters.append({"Name": "instance-state-name", "Values": [state]})

    response = ec2.describe_instances(Filters=filters)
    instances = []

    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            name = next(
                (tag["Value"] for tag in instance.get("Tags", []) if tag["Key"] == "Name"),
                "unnamed",
            )
            instances.append(
                {
                    "instance_id": instance["InstanceId"],
                    "name": name,
                    "instance_type": instance["InstanceType"],
                    "state": instance["State"]["Name"],
                    "availability_zone": instance["Placement"]["AvailabilityZone"],
                    "private_ip": instance.get("PrivateIpAddress"),
                    "public_ip": instance.get("PublicIpAddress"),
                    "launch_time": str(instance["LaunchTime"]),
                    "tags": {t["Key"]: t["Value"] for t in instance.get("Tags", [])},
                }
            )

    return instances
