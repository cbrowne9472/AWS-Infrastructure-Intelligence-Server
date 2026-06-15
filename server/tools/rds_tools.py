from server.config import get_client

rds = get_client("rds")


def get_rds_instances() -> list[dict]:
    response = rds.describe_db_instances()
    return [
        {
            "identifier": db["DBInstanceIdentifier"],
            "engine": f"{db['Engine']} {db['EngineVersion']}",
            "instance_class": db["DBInstanceClass"],
            "status": db["DBInstanceStatus"],
            "storage_gb": db["AllocatedStorage"],
            "storage_type": db["StorageType"],
            "multi_az": db["MultiAZ"],
            "publicly_accessible": db["PubliclyAccessible"],
            "endpoint": db.get("Endpoint", {}).get("Address"),
            "port": db.get("Endpoint", {}).get("Port"),
        }
        for db in response["DBInstances"]
    ]
