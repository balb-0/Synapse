from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nifi_api import (
    API_DEFAULT,
    NifiClient,
    attach_parameter_context,
    create_connection,
    create_process_group,
    create_processor,
    create_service,
    delete_processor,
    enable_service,
    find_parameter_context,
    find_process_group,
    find_processor,
    find_service,
    group_flow,
    group_status,
    processors,
    revision,
    root_group_id,
    set_group_state,
    update_processor,
)


PG_NAME = "01_SINDUSFARMA_RAW_BRONZE"
PARAMETER_CONTEXT_NAME = "sindusfarma-local-secure"
FLOW_EXPORT_PATH = Path("nifi/flows/01_SINDUSFARMA_RAW_BRONZE.json")
MANIFEST_ATTRIBUTES = (
    "dataset,run_id,ingestion_id,filename,source_path,file_hash,fileSize,"
    "file_size_bytes,source_row_count,destination_row_count,raw_object_key,"
    "bronze_object_key,success_marker_key,status,started_at,finished_at,"
    "destination_path,rejected_object_key,error_message"
)


@dataclass(frozen=True)
class Dataset:
    name: str
    file_name: str
    expected_rows: int
    key_columns: tuple[str, ...]


DATASETS = [
    Dataset("clientes", "clientes.csv", 5430, ("id_cliente",)),
    Dataset("empresas", "empresas.csv", 779, ("id_empresa",)),
    Dataset("pesquisas", "pesquisas.csv", 366, ("id_pesquisa",)),
    Dataset("questoes", "questoes.csv", 231, ("id_pergunta",)),
    Dataset("respondentes", "respondentes.csv", 18735, ("id_pesq", "id_empresa", "id_cliente")),
    Dataset("respostas", "respostas.csv", 20607, ("id_resposta",)),
]


PROCESSOR_TYPES = {
    "AttributesToJSON": (
        "org.apache.nifi.processors.standard.AttributesToJSON",
        "nifi-standard-nar",
    ),
    "ConvertRecord": (
        "org.apache.nifi.processors.standard.ConvertRecord",
        "nifi-standard-nar",
    ),
    "FetchFile": (
        "org.apache.nifi.processors.standard.FetchFile",
        "nifi-standard-nar",
    ),
    "FetchS3Object": (
        "org.apache.nifi.processors.aws.s3.FetchS3Object",
        "nifi-aws-nar",
    ),
    "HashContent": (
        "org.apache.nifi.processors.standard.HashContent",
        "nifi-standard-nar",
    ),
    "ListFile": (
        "org.apache.nifi.processors.standard.ListFile",
        "nifi-standard-nar",
    ),
    "LogAttribute": (
        "org.apache.nifi.processors.standard.LogAttribute",
        "nifi-standard-nar",
    ),
    "PutS3Object": (
        "org.apache.nifi.processors.aws.s3.PutS3Object",
        "nifi-aws-nar",
    ),
    "UpdateAttribute": (
        "org.apache.nifi.processors.attributes.UpdateAttribute",
        "nifi-update-attribute-nar",
    ),
}

SERVICE_TYPES = {
    "AvroSchemaRegistry": (
        "org.apache.nifi.schemaregistry.services.AvroSchemaRegistry",
        "nifi-registry-nar",
    ),
    "CSVReader": (
        "org.apache.nifi.csv.CSVReader",
        "nifi-record-serialization-services-nar",
    ),
    "ParquetRecordSetWriter": (
        "org.apache.nifi.parquet.ParquetRecordSetWriter",
        "nifi-parquet-nar",
    ),
}


def repo_file(*parts: str) -> Path:
    return Path(__file__).resolve().parents[2].joinpath(*parts)


def read_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def required_value(values: dict[str, str], key: str) -> str:
    value = values.get(key)
    if not value:
        raise RuntimeError(f"Variavel obrigatoria ausente: {key}. Copie .env.example para .env.")
    return value


def local_parameter_values() -> dict[str, str]:
    file_values = read_env_file(repo_file(".env"))
    merged = {**file_values, **os.environ}
    return {
        "input.dir": merged.get("NIFI_INPUT_DIR", "/opt/nifi/input"),
        "minio.bucket": merged.get("MINIO_BUCKET", "sindusfarma-data"),
        "minio.endpoint": merged.get("MINIO_INTERNAL_ENDPOINT", "http://minio:9000"),
        "minio.access.key": required_value(merged, "MINIO_ROOT_USER"),
        "minio.secret.key": required_value(merged, "MINIO_ROOT_PASSWORD"),
        "aws.region": merged.get("AWS_REGION", "us-east-1"),
    }


def ensure_parameter_context(client: NifiClient) -> dict[str, Any]:
    context = find_parameter_context(client, PARAMETER_CONTEXT_NAME)
    if context:
        return context

    values = local_parameter_values()
    params = [
        ("input.dir", values["input.dir"], False),
        ("minio.bucket", values["minio.bucket"], False),
        ("minio.endpoint", values["minio.endpoint"], False),
        ("minio.access.key", values["minio.access.key"], True),
        ("minio.secret.key", values["minio.secret.key"], True),
        ("aws.region", values["aws.region"], False),
    ]
    body = {
        "revision": {"version": 0},
        "component": {
            "name": PARAMETER_CONTEXT_NAME,
            "description": "Parametros locais seguros para NiFi + MinIO da entrega Sindusfarma.",
            "parameters": [
                {
                    "parameter": {
                        "name": name,
                        "value": value,
                        "sensitive": sensitive,
                    }
                }
                for name, value, sensitive in params
            ],
        },
    }
    return client.post("/parameter-contexts", body)


def ensure_group(client: NifiClient) -> dict[str, Any]:
    group = find_process_group(client, PG_NAME)
    if group:
        return group
    return create_process_group(client, root_group_id(client), PG_NAME, x=620, y=0)


def service_type(kind: str) -> tuple[str, str]:
    return SERVICE_TYPES[kind]


def processor_type(kind: str) -> tuple[str, str]:
    return PROCESSOR_TYPES[kind]


def controller_services(client: NifiClient, group_id: str) -> list[dict[str, Any]]:
    return client.get(
        f"/flow/process-groups/{group_id}/controller-services"
    ).get("controllerServices", [])


def update_service_properties(
    client: NifiClient,
    service: dict[str, Any],
    properties: dict[str, str | None],
) -> dict[str, Any]:
    service_id = service["id"]
    current = client.get(f"/controller-services/{service_id}")
    if current["component"]["state"] == "ENABLED":
        return current
    merged = dict(current["component"].get("properties", {}))
    merged.update(properties)
    body = {
        "revision": revision(current),
        "component": {
            "id": service_id,
            "name": current["component"]["name"],
            "type": current["component"]["type"],
            "bundle": current["component"]["bundle"],
            "properties": merged,
        },
    }
    return client.put(f"/controller-services/{service_id}", body)


def create_or_update_service(
    client: NifiClient,
    group_id: str,
    name: str,
    kind: str,
    properties: dict[str, str | None],
) -> dict[str, Any]:
    existing = find_service(client, group_id, name)
    if existing:
        return update_service_properties(client, existing, properties)
    type_name, artifact = service_type(kind)
    return create_service(
        client,
        group_id,
        name,
        kind,
        properties,
    )


def ensure_services(client: NifiClient, group_id: str) -> dict[str, str]:
    schemas = {
        dataset.name: repo_file("nifi", "schemas", f"{dataset.name}.avsc").read_text(
            encoding="utf-8"
        )
        for dataset in DATASETS
    }
    registry_props: dict[str, str | None] = {
        "avro-reg-validated-field-names": "true",
        **schemas,
    }
    registry = create_or_update_service(
        client,
        group_id,
        "schema-registry-sindusfarma",
        "AvroSchemaRegistry",
        registry_props,
    )
    enable_service(client, registry["id"])

    ids = {"registry": registry["id"]}
    for dataset in DATASETS:
        reader_props = {
            "schema-access-strategy": "schema-name",
            "schema-registry": registry["id"],
            "schema-name": dataset.name,
            "csv-reader-csv-parser": "commons-csv",
            "CSV Format": "custom",
            "Value Separator": ";",
            "Skip Header Line": "true",
            "ignore-csv-header": "true",
            "Trim Fields": "true",
            "csvutils-character-set": "UTF-8",
        }
        reader = create_or_update_service(
            client,
            group_id,
            f"csv-reader-{dataset.name}",
            "CSVReader",
            reader_props,
        )
        enable_service(client, reader["id"])
        ids[f"reader:{dataset.name}"] = reader["id"]

    writer = create_or_update_service(
        client,
        group_id,
        "parquet-writer-bronze",
        "ParquetRecordSetWriter",
        {
            "schema-access-strategy": "inherit-record-schema",
            "Schema Write Strategy": "no-schema",
            "compression-type": "SNAPPY",
        },
    )
    enable_service(client, writer["id"])
    ids["writer"] = writer["id"]
    return ids


def s3_put_properties() -> dict[str, str]:
    return {
        "Bucket": "#{minio.bucket}",
        "Region": "#{aws.region}",
        "Access Key": "#{minio.access.key}",
        "Secret Key": "#{minio.secret.key}",
        "Endpoint Override URL": "#{minio.endpoint}",
        "Signer Override": "AWSS3V4SignerType",
        "use-path-style-access": "true",
    }


def s3_fetch_properties() -> dict[str, str]:
    props = s3_put_properties()
    props.pop("use-path-style-access", None)
    return props


def create_or_update_processor(
    client: NifiClient,
    group_id: str,
    name: str,
    kind: str,
    position: tuple[float, float],
    properties: dict[str, str | None],
) -> dict[str, Any]:
    processor = find_processor(client, group_id, name)
    if processor is None:
        type_name, artifact = processor_type(kind)
        processor = create_processor(client, group_id, name, kind, *position)
    return update_processor(client, processor["id"], properties)


def dataset_specs(
    dataset: Dataset,
    base_y: float,
    service_ids: dict[str, str],
) -> list[tuple[str, str, tuple[float, float], dict[str, str | None]]]:
    name = dataset.name
    csv_name = dataset.file_name
    s3_put = s3_put_properties()
    s3_fetch = s3_fetch_properties()
    return [
        (
            f"{name} 01 List",
            "ListFile",
            (0, base_y),
            {
                "Input Directory": "#{input.dir}",
                "File Filter": f"^{re.escape(csv_name)}$",
                "Recurse Subdirectories": "false",
                "Input Directory Location": "Local",
                "listing-strategy": "timestamps",
            },
        ),
        (
            f"{name} 02 Fetch",
            "FetchFile",
            (300, base_y),
            {
                "File to Fetch": "${absolute.path}/${filename}",
                "Completion Strategy": "None",
            },
        ),
        (
            f"{name} 03 SHA-256",
            "HashContent",
            (600, base_y),
            {"Hash Algorithm": "SHA-256", "Hash Attribute Name": "file_hash"},
        ),
        (
            f"{name} 04 Attributes",
            "UpdateAttribute",
            (900, base_y),
            {
                "dataset": name,
                "run_id": "${now():format('yyyyMMddHHmmssSSS')}",
                "ingestion_id": "${uuid}",
                "started_at": "${now():format(\"yyyy-MM-dd'T'HH:mm:ss.SSS'Z'\")}",
                "raw_object_key": f"raw/{name}/${{file_hash}}/${{filename}}",
                "bronze_object_key": f"bronze/{name}/${{file_hash}}/{name}.parquet",
                "success_marker_key": f"manifests/success_hashes/{name}/${{file_hash}}.json",
                "manifest_success_key": (
                    f"manifests/events/dataset={name}/status=SUCCESS/"
                    "${now():format('yyyyMMddHHmmssSSS')}-${file_hash}-${uuid}.json"
                ),
                "manifest_skipped_key": (
                    f"manifests/events/dataset={name}/status=SKIPPED_ALREADY_INGESTED/"
                    "${now():format('yyyyMMddHHmmssSSS')}-${file_hash}-${uuid}.json"
                ),
                "file_size_bytes": "${fileSize}",
                "source_path": "${absolute.path}/${filename}",
            },
        ),
        (
            f"{name} 05 Check marker",
            "FetchS3Object",
            (1200, base_y),
            {**s3_fetch, "Object Key": "${success_marker_key}"},
        ),
        (
            f"{name} 06A Mark skipped",
            "UpdateAttribute",
            (1500, base_y - 120),
            {
                "status": "SKIPPED_ALREADY_INGESTED",
                "finished_at": "${now():format(\"yyyy-MM-dd'T'HH:mm:ss.SSS'Z'\")}",
                "destination_path": "${bronze_object_key}",
            },
        ),
        (
            f"{name} 06A Skipped JSON",
            "AttributesToJSON",
            (1800, base_y - 120),
            {
                "Destination": "flowfile-content",
                "Attributes List": MANIFEST_ATTRIBUTES,
                "Include Core Attributes": "true",
                "Pretty Print": "true",
            },
        ),
        (
            f"{name} 06A Put skipped manifest",
            "PutS3Object",
            (2100, base_y - 120),
            {**s3_put, "Object Key": "${manifest_skipped_key}"},
        ),
        (
            f"{name} 06B Put raw",
            "PutS3Object",
            (1500, base_y + 120),
            {**s3_put, "Object Key": "${raw_object_key}"},
        ),
        (
            f"{name} 07 Convert to Parquet",
            "ConvertRecord",
            (1800, base_y + 120),
            {
                "record-reader": service_ids[f"reader:{name}"],
                "record-writer": service_ids["writer"],
                "include-zero-record-flowfiles": "false",
            },
        ),
        (
            f"{name} 08 Put bronze",
            "PutS3Object",
            (2100, base_y + 120),
            {**s3_put, "Object Key": "${bronze_object_key}"},
        ),
        (
            f"{name} 09 Mark success",
            "UpdateAttribute",
            (2400, base_y + 120),
            {
                "status": "SUCCESS",
                "finished_at": "${now():format(\"yyyy-MM-dd'T'HH:mm:ss.SSS'Z'\")}",
                "destination_path": "${bronze_object_key}",
                "source_row_count": "${record.count}",
                "destination_row_count": "${record.count}",
            },
        ),
        (
            f"{name} 10 Success JSON",
            "AttributesToJSON",
            (2700, base_y + 120),
            {
                "Destination": "flowfile-content",
                "Attributes List": MANIFEST_ATTRIBUTES,
                "Include Core Attributes": "true",
                "Pretty Print": "true",
            },
        ),
        (
            f"{name} 11 Put success manifest",
            "PutS3Object",
            (3000, base_y + 120),
            {**s3_put, "Object Key": "${manifest_success_key}"},
        ),
        (
            f"{name} 12 Put success marker",
            "PutS3Object",
            (3300, base_y + 120),
            {**s3_put, "Object Key": "${success_marker_key}"},
        ),
    ]


def create_dataset_processors(
    client: NifiClient,
    group_id: str,
    service_ids: dict[str, str],
) -> dict[str, str]:
    ids: dict[str, str] = {}
    for index, dataset in enumerate(DATASETS):
        for name, kind, position, properties in dataset_specs(dataset, index * 360, service_ids):
            entity = create_or_update_processor(
                client, group_id, name, kind, position, properties
            )
            ids[name] = entity["id"]

    mark_failure = create_or_update_processor(
        client,
        group_id,
        "99 Mark failure",
        "UpdateAttribute",
        (1500, len(DATASETS) * 360 + 120),
        {
            "status": "PIPELINE_FAILED",
            "finished_at": "${now():format(\"yyyy-MM-dd'T'HH:mm:ss.SSS'Z'\")}",
            "error_message": "${error.message}",
            "rejected_object_key": (
                "rejected/${dataset}/"
                "${now():format('yyyyMMddHHmmssSSS')}-${file_hash}-${uuid}.json"
            ),
            "destination_path": "${rejected_object_key}",
        },
    )
    ids["99 Mark failure"] = mark_failure["id"]

    failure_json = create_or_update_processor(
        client,
        group_id,
        "99 Failure JSON",
        "AttributesToJSON",
        (1800, len(DATASETS) * 360 + 120),
        {
            "Destination": "flowfile-content",
            "Attributes List": MANIFEST_ATTRIBUTES,
            "Include Core Attributes": "true",
            "Pretty Print": "true",
        },
    )
    ids["99 Failure JSON"] = failure_json["id"]

    put_failure = create_or_update_processor(
        client,
        group_id,
        "99 Put rejected manifest",
        "PutS3Object",
        (2100, len(DATASETS) * 360 + 120),
        {**s3_put_properties(), "Object Key": "${rejected_object_key}"},
    )
    ids["99 Put rejected manifest"] = put_failure["id"]

    log = create_or_update_processor(
        client,
        group_id,
        "99 Log failures",
        "LogAttribute",
        (2400, len(DATASETS) * 360 + 120),
        {},
    )
    ids["99 Log failures"] = log["id"]
    return ids


def connections(client: NifiClient, group_id: str) -> list[dict[str, Any]]:
    return group_flow(client, group_id).get("connections", [])


def delete_connections(client: NifiClient, group_id: str) -> None:
    for connection in list(connections(client, group_id)):
        client.delete(
            f"/connections/{connection['id']}?version={revision(connection)['version']}"
            "&disconnectedNodeAcknowledged=false"
        )


def delete_generated_processors(client: NifiClient, group_id: str) -> None:
    for processor in list(processors(client, group_id)):
        delete_processor(client, processor)


def reset_group(client: NifiClient, group_id: str) -> None:
    set_group_state(client, group_id, "STOPPED")
    delete_connections(client, group_id)
    delete_generated_processors(client, group_id)


def clear_listfile_state(client: NifiClient, group_id: str) -> None:
    for processor in processors(client, group_id):
        component = processor["component"]
        if component["type"].endswith(".ListFile"):
            client.post(f"/processors/{processor['id']}/state/clear-requests", {})
            print(f"cleared_state={component['name']}")


def connection_exists(
    client: NifiClient,
    group_id: str,
    source_id: str,
    destination_id: str,
    relationships: list[str],
) -> bool:
    desired = sorted(relationships)
    for connection in connections(client, group_id):
        component = connection["component"]
        if (
            component["source"]["id"] == source_id
            and component["destination"]["id"] == destination_id
            and sorted(component.get("selectedRelationships", [])) == desired
        ):
            return True
    return False


def connect(
    client: NifiClient,
    group_id: str,
    ids: dict[str, str],
    source: str,
    destination: str,
    relationships: list[str],
    connected: dict[str, set[str]],
) -> None:
    if not connection_exists(client, group_id, ids[source], ids[destination], relationships):
        create_connection(client, group_id, ids[source], ids[destination], relationships)
    connected.setdefault(source, set()).update(relationships)


def create_connections(
    client: NifiClient,
    group_id: str,
    ids: dict[str, str],
) -> dict[str, set[str]]:
    connected: dict[str, set[str]] = {name: set() for name in ids}
    for dataset in DATASETS:
        name = dataset.name
        connect(client, group_id, ids, f"{name} 01 List", f"{name} 02 Fetch", ["success"], connected)
        connect(client, group_id, ids, f"{name} 02 Fetch", f"{name} 03 SHA-256", ["success"], connected)
        connect(client, group_id, ids, f"{name} 03 SHA-256", f"{name} 04 Attributes", ["success"], connected)
        connect(client, group_id, ids, f"{name} 04 Attributes", f"{name} 05 Check marker", ["success"], connected)
        connect(client, group_id, ids, f"{name} 05 Check marker", f"{name} 06A Mark skipped", ["success"], connected)
        connect(client, group_id, ids, f"{name} 05 Check marker", f"{name} 06B Put raw", ["failure"], connected)
        connect(client, group_id, ids, f"{name} 06A Mark skipped", f"{name} 06A Skipped JSON", ["success"], connected)
        connect(client, group_id, ids, f"{name} 06A Skipped JSON", f"{name} 06A Put skipped manifest", ["success"], connected)
        connect(client, group_id, ids, f"{name} 06B Put raw", f"{name} 07 Convert to Parquet", ["success"], connected)
        connect(client, group_id, ids, f"{name} 07 Convert to Parquet", f"{name} 08 Put bronze", ["success"], connected)
        connect(client, group_id, ids, f"{name} 08 Put bronze", f"{name} 09 Mark success", ["success"], connected)
        connect(client, group_id, ids, f"{name} 09 Mark success", f"{name} 10 Success JSON", ["success"], connected)
        connect(client, group_id, ids, f"{name} 10 Success JSON", f"{name} 11 Put success manifest", ["success"], connected)
        connect(client, group_id, ids, f"{name} 11 Put success manifest", f"{name} 12 Put success marker", ["success"], connected)

        failure_edges = [
            (f"{name} 02 Fetch", ["failure", "not.found", "permission.denied"]),
            (f"{name} 03 SHA-256", ["failure"]),
            (f"{name} 06A Skipped JSON", ["failure"]),
            (f"{name} 06A Put skipped manifest", ["failure"]),
            (f"{name} 06B Put raw", ["failure"]),
            (f"{name} 07 Convert to Parquet", ["failure"]),
            (f"{name} 08 Put bronze", ["failure"]),
            (f"{name} 10 Success JSON", ["failure"]),
            (f"{name} 11 Put success manifest", ["failure"]),
            (f"{name} 12 Put success marker", ["failure"]),
        ]
        for source, relationships in failure_edges:
            connect(client, group_id, ids, source, "99 Mark failure", relationships, connected)

    connect(client, group_id, ids, "99 Mark failure", "99 Failure JSON", ["success"], connected)
    connect(client, group_id, ids, "99 Failure JSON", "99 Put rejected manifest", ["success"], connected)
    connect(
        client,
        group_id,
        ids,
        "99 Put rejected manifest",
        "99 Log failures",
        ["success", "failure"],
        connected,
    )
    connect(client, group_id, ids, "99 Failure JSON", "99 Log failures", ["failure"], connected)
    return connected


def set_auto_terminated(
    client: NifiClient,
    ids: dict[str, str],
    connected: dict[str, set[str]],
) -> None:
    for name, processor_id in ids.items():
        entity = client.get(f"/processors/{processor_id}")
        all_relationships = {
            relationship["name"] for relationship in entity["component"]["relationships"]
        }
        update_processor(
            client,
            processor_id,
            auto_terminated=sorted(all_relationships - connected.get(name, set())),
        )


def run_once(client: NifiClient, group_id: str, timeout_seconds: int) -> dict[str, Any]:
    set_group_state(client, group_id, "RUNNING")
    deadline = time.time() + timeout_seconds
    saw_activity = False
    try:
        while time.time() < deadline:
            snapshot = group_status(client, group_id)
            queued = int(snapshot.get("flowFilesQueued", 0))
            active = int(snapshot.get("activeThreadCount", 0))
            transferred = int(snapshot.get("flowFilesTransferred", 0))
            if transferred > 0:
                saw_activity = True
            print(f"status: queued={queued}, active_threads={active}, transferred={transferred}")
            if saw_activity and queued == 0 and active == 0:
                break
            time.sleep(3)
    finally:
        set_group_state(client, group_id, "STOPPED")
    return group_status(client, group_id)


def export_flow(api_url: str, group_id: str) -> None:
    FLOW_EXPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    url = f"{api_url.rstrip('/')}/process-groups/{group_id}/download"
    with urllib.request.urlopen(url, timeout=30) as response:
        FLOW_EXPORT_PATH.write_bytes(response.read())


def validation_summary(client: NifiClient, group_id: str) -> None:
    flow = group_flow(client, group_id)
    invalid = []
    for processor in sorted(flow.get("processors", []), key=lambda item: item["component"]["name"]):
        detail = client.get(f"/processors/{processor['id']}")
        status = detail["component"].get("validationStatus")
        if status != "VALID":
            invalid.append((processor["component"]["name"], status, detail["component"].get("validationErrors") or []))

    print(f"processors={len(flow.get('processors', []))}")
    print(f"connections={len(flow.get('connections', []))}")
    print(f"invalid_processors={len(invalid)}")
    for name, status, errors in invalid:
        print(f"- {name}: {status}")
        for error in errors:
            print(f"  * {error}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Cria fluxo NiFi para os seis CSVs reais.")
    parser.add_argument("--api", default=API_DEFAULT)
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--start", action="store_true")
    parser.add_argument(
        "--clear-listing-state",
        action="store_true",
        help="Limpa o estado dos ListFile para reexecutar a descoberta dos mesmos arquivos.",
    )
    parser.add_argument("--timeout-seconds", type=int, default=180)
    args = parser.parse_args()

    client = NifiClient(args.api)
    context = ensure_parameter_context(client)
    group = ensure_group(client)
    group_id = group["id"]
    set_group_state(client, group_id, "STOPPED")
    attach_parameter_context(client, group_id, context["id"])

    if args.reset:
        reset_group(client, group_id)

    services = ensure_services(client, group_id)
    ids = create_dataset_processors(client, group_id, services)
    connected = create_connections(client, group_id, ids)
    set_auto_terminated(client, ids, connected)
    if args.clear_listing_state:
        clear_listfile_state(client, group_id)
    validation_summary(client, group_id)

    export_flow(args.api, group_id)
    print(f"flow_exported={FLOW_EXPORT_PATH}")

    if args.start:
        snapshot = run_once(client, group_id, args.timeout_seconds)
        print(
            "run_summary="
            + json.dumps(
                {
                    "flowFilesTransferred": snapshot.get("flowFilesTransferred"),
                    "flowFilesQueued": snapshot.get("flowFilesQueued"),
                    "bytesRead": snapshot.get("bytesRead"),
                    "bytesWritten": snapshot.get("bytesWritten"),
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()
