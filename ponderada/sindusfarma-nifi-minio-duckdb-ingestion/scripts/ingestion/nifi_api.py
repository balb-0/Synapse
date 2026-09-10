from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any


API_DEFAULT = "http://localhost:8080/nifi-api"

PROCESSOR_TYPES = {
    "AttributesToJSON": ("org.apache.nifi.processors.standard.AttributesToJSON", "nifi-standard-nar"),
    "ConvertRecord": ("org.apache.nifi.processors.standard.ConvertRecord", "nifi-standard-nar"),
    "FetchFile": ("org.apache.nifi.processors.standard.FetchFile", "nifi-standard-nar"),
    "FetchS3Object": ("org.apache.nifi.processors.aws.s3.FetchS3Object", "nifi-aws-nar"),
    "HashContent": ("org.apache.nifi.processors.standard.HashContent", "nifi-standard-nar"),
    "ListFile": ("org.apache.nifi.processors.standard.ListFile", "nifi-standard-nar"),
    "LogAttribute": ("org.apache.nifi.processors.standard.LogAttribute", "nifi-standard-nar"),
    "PutS3Object": ("org.apache.nifi.processors.aws.s3.PutS3Object", "nifi-aws-nar"),
    "UpdateAttribute": ("org.apache.nifi.processors.attributes.UpdateAttribute", "nifi-update-attribute-nar"),
}

SERVICE_TYPES = {
    "AvroSchemaRegistry": ("org.apache.nifi.schemaregistry.services.AvroSchemaRegistry", "nifi-registry-nar"),
    "CSVReader": ("org.apache.nifi.csv.CSVReader", "nifi-record-serialization-services-nar"),
    "ParquetRecordSetWriter": ("org.apache.nifi.parquet.ParquetRecordSetWriter", "nifi-parquet-nar"),
}


class NifiClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        data = None
        headers = {"Accept": "application/json"}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = response.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"{method} {url} failed: {exc.code} {detail}") from exc

        if not payload:
            return {}
        return json.loads(payload.decode("utf-8"))

    def get(self, path: str) -> dict[str, Any]:
        return self.request("GET", path)

    def post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", path, body)

    def put(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        return self.request("PUT", path, body)

    def delete(self, path: str) -> dict[str, Any]:
        return self.request("DELETE", path)


def bundle(artifact: str) -> dict[str, str]:
    return {"group": "org.apache.nifi", "artifact": artifact, "version": "1.27.0"}


def revision(entity: dict[str, Any]) -> dict[str, Any]:
    current = dict(entity.get("revision", {}))
    current.setdefault("version", 0)
    return current


def root_group_id(client: NifiClient) -> str:
    return client.get("/process-groups/root")["id"]


def root_flow(client: NifiClient) -> dict[str, Any]:
    return client.get("/flow/process-groups/root")["processGroupFlow"]["flow"]


def find_process_group(client: NifiClient, name: str) -> dict[str, Any] | None:
    for group in root_flow(client).get("processGroups", []):
        if group["component"]["name"] == name:
            return group
    return None


def create_process_group(
    client: NifiClient,
    parent_id: str,
    name: str,
    x: float = 300.0,
    y: float = 0.0,
) -> dict[str, Any]:
    body = {
        "revision": {"version": 0},
        "component": {"name": name, "position": {"x": x, "y": y}},
    }
    return client.post(f"/process-groups/{parent_id}/process-groups", body)


def parameter_contexts(client: NifiClient) -> list[dict[str, Any]]:
    return client.get("/flow/parameter-contexts").get("parameterContexts", [])


def find_parameter_context(client: NifiClient, name: str) -> dict[str, Any] | None:
    for context in parameter_contexts(client):
        if context["component"]["name"] == name:
            return context
    return None


def attach_parameter_context(
    client: NifiClient,
    group_id: str,
    parameter_context_id: str,
) -> None:
    entity = client.get(f"/process-groups/{group_id}")
    component = dict(entity["component"])
    component["parameterContext"] = {"id": parameter_context_id}
    client.put(
        f"/process-groups/{group_id}",
        {"revision": revision(entity), "component": component},
    )


def group_flow(client: NifiClient, group_id: str) -> dict[str, Any]:
    return client.get(f"/flow/process-groups/{group_id}")["processGroupFlow"]["flow"]


def controller_services(client: NifiClient, group_id: str) -> list[dict[str, Any]]:
    return client.get(f"/flow/process-groups/{group_id}/controller-services").get(
        "controllerServices", []
    )


def find_service(client: NifiClient, group_id: str, name: str) -> dict[str, Any] | None:
    for service in controller_services(client, group_id):
        if service["component"]["name"] == name:
            return service
    return None


def create_service(
    client: NifiClient,
    group_id: str,
    name: str,
    kind: str,
    properties: dict[str, str | None],
) -> dict[str, Any]:
    type_name, artifact = SERVICE_TYPES[kind]
    body = {
        "revision": {"version": 0},
        "component": {
            "name": name,
            "type": type_name,
            "bundle": bundle(artifact),
            "properties": properties,
        },
    }
    return client.post(f"/process-groups/{group_id}/controller-services", body)


def enable_service(client: NifiClient, service_id: str) -> None:
    entity = client.get(f"/controller-services/{service_id}")
    if entity["component"]["state"] == "ENABLED":
        return
    client.put(
        f"/controller-services/{service_id}/run-status",
        {
            "revision": revision(entity),
            "state": "ENABLED",
            "disconnectedNodeAcknowledged": False,
        },
    )
    for _ in range(30):
        current = client.get(f"/controller-services/{service_id}")
        if current["component"]["state"] == "ENABLED":
            return
        time.sleep(1)


def processors(client: NifiClient, group_id: str) -> list[dict[str, Any]]:
    return group_flow(client, group_id).get("processors", [])


def find_processor(client: NifiClient, group_id: str, name: str) -> dict[str, Any] | None:
    for processor in processors(client, group_id):
        if processor["component"]["name"] == name:
            return processor
    return None


def create_processor(
    client: NifiClient,
    group_id: str,
    name: str,
    kind: str,
    x: float,
    y: float,
) -> dict[str, Any]:
    type_name, artifact = PROCESSOR_TYPES[kind]
    body = {
        "revision": {"version": 0},
        "component": {
            "name": name,
            "type": type_name,
            "bundle": bundle(artifact),
            "position": {"x": x, "y": y},
        },
    }
    return client.post(f"/process-groups/{group_id}/processors", body)


def update_processor(
    client: NifiClient,
    processor_id: str,
    properties: dict[str, str | None] | None = None,
    auto_terminated: list[str] | None = None,
) -> dict[str, Any]:
    current = client.get(f"/processors/{processor_id}")
    component = {
        "id": processor_id,
        "name": current["component"]["name"],
        "type": current["component"]["type"],
        "bundle": current["component"]["bundle"],
        "config": dict(current["component"]["config"]),
    }
    if properties is not None:
        merged = dict(current["component"]["config"].get("properties", {}))
        merged.update(properties)
        component["config"]["properties"] = merged
    if auto_terminated is not None:
        component["config"]["autoTerminatedRelationships"] = auto_terminated
    return client.put(
        f"/processors/{processor_id}",
        {"revision": revision(current), "component": component},
    )


def create_connection(
    client: NifiClient,
    group_id: str,
    source_id: str,
    destination_id: str,
    relationships: list[str],
) -> dict[str, Any]:
    body = {
        "revision": {"version": 0},
        "component": {
            "source": {"id": source_id, "groupId": group_id, "type": "PROCESSOR"},
            "destination": {"id": destination_id, "groupId": group_id, "type": "PROCESSOR"},
            "selectedRelationships": relationships,
        },
    }
    return client.post(f"/process-groups/{group_id}/connections", body)


def stop_processor(client: NifiClient, processor_id: str) -> None:
    entity = client.get(f"/processors/{processor_id}")
    if entity["component"]["state"] == "STOPPED":
        return
    client.put(
        f"/processors/{processor_id}/run-status",
        {
            "revision": revision(entity),
            "state": "STOPPED",
            "disconnectedNodeAcknowledged": False,
        },
    )


def delete_processor(client: NifiClient, processor: dict[str, Any]) -> None:
    stop_processor(client, processor["id"])
    entity = client.get(f"/processors/{processor['id']}")
    client.delete(
        f"/processors/{processor['id']}?version={revision(entity)['version']}"
        "&disconnectedNodeAcknowledged=false"
    )


def set_group_state(client: NifiClient, group_id: str, state: str) -> None:
    client.put(
        f"/flow/process-groups/{group_id}",
        {"id": group_id, "state": state, "disconnectedNodeAcknowledged": False},
    )


def group_status(client: NifiClient, group_id: str) -> dict[str, Any]:
    return client.get(f"/flow/process-groups/{group_id}/status?recursive=true")[
        "processGroupStatus"
    ]["aggregateSnapshot"]

