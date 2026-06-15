from server.config import get_client

ec2 = get_client("ec2")


def get_vpc_info() -> list[dict]:
    vpcs_response = ec2.describe_vpcs()
    subnets_response = ec2.describe_subnets()
    igw_response = ec2.describe_internet_gateways()

    subnets_by_vpc = {}
    for subnet in subnets_response["Subnets"]:
        vpc_id = subnet["VpcId"]
        if vpc_id not in subnets_by_vpc:
            subnets_by_vpc[vpc_id] = []
        subnets_by_vpc[vpc_id].append(
            {
                "subnet_id": subnet["SubnetId"],
                "cidr": subnet["CidrBlock"],
                "az": subnet["AvailabilityZone"],
                "public": subnet["MapPublicIpOnLaunch"],
                "available_ips": subnet["AvailableIpAddressCount"],
            }
        )

    igws_by_vpc = {}
    for igw in igw_response["InternetGateways"]:
        for attachment in igw.get("Attachments", []):
            igws_by_vpc[attachment["VpcId"]] = igw["InternetGatewayId"]

    vpcs = []
    for vpc in vpcs_response["Vpcs"]:
        name = next(
            (tag["Value"] for tag in vpc.get("Tags", []) if tag["Key"] == "Name"),
            "unnamed",
        )
        vpcs.append(
            {
                "vpc_id": vpc["VpcId"],
                "name": name,
                "cidr": vpc["CidrBlock"],
                "is_default": vpc["IsDefault"],
                "state": vpc["State"],
                "internet_gateway": igws_by_vpc.get(vpc["VpcId"]),
                "subnets": subnets_by_vpc.get(vpc["VpcId"], []),
            }
        )

    return vpcs
