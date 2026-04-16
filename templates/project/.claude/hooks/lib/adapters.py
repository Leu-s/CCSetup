from __future__ import annotations

import asyncio
import importlib.util
import os
import pathlib
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from .util import atomic_write_json, now_utc_iso, read_json


@dataclass
class HealthResult:
    ok: bool
    detail: str


def mock_ingest_enabled() -> bool:
    return os.environ.get("GRAPHITI_MOCK_INGEST", "").strip().lower() in {"1", "true", "yes", "on"}


def check_mcp_health(url: str) -> HealthResult:
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            body = response.read(2000).decode("utf-8", errors="replace")
        return HealthResult(True, body or "ok")
    except Exception as exc:
        return HealthResult(False, str(exc))


def _parse_falkordb_uri(value: str) -> dict[str, Any]:
    parsed = urllib.parse.urlparse(value)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 6379
    password = parsed.password or None
    return {"host": host, "port": port, "password": password}


def _engine_state_path(root: pathlib.Path, config: dict[str, Any]) -> pathlib.Path:
    return (root / config["queue"]["engineStatePath"]).resolve()


def _load_engine_state(root: pathlib.Path, config: dict[str, Any]) -> dict[str, Any]:
    return read_json(_engine_state_path(root, config), default={"initialized": False}) or {"initialized": False}


def _save_engine_state(root: pathlib.Path, config: dict[str, Any], state: dict[str, Any]) -> None:
    atomic_write_json(_engine_state_path(root, config), state)


def _openai_clients(config: dict[str, Any]):
    from openai import AsyncOpenAI
    from graphiti_core import Graphiti
    from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient
    from graphiti_core.embedder import OpenAIEmbedder, OpenAIEmbedderConfig
    from graphiti_core.llm_client import LLMConfig, OpenAIClient

    ocfg = config["engine"]["openai"]
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    llm_cfg = LLMConfig(
        api_key=api_key,
        model=ocfg["model"],
        small_model=ocfg.get("smallModel") or ocfg["model"],
    )
    llm_client = OpenAIClient(config=llm_cfg, client=AsyncOpenAI(api_key=api_key, max_retries=3))
    embedder = OpenAIEmbedder(
        config=OpenAIEmbedderConfig(
            api_key=api_key,
            embedding_model=ocfg["embeddingModel"],
        )
    )
    cross_encoder = OpenAIRerankerClient(client=llm_client, config=llm_cfg)
    return Graphiti, llm_client, embedder, cross_encoder


async def _build_graphiti_instance(config: dict[str, Any]):
    from graphiti_core import Graphiti

    backend = config["engine"]["backend"]
    provider = config["engine"]["provider"]

    if backend == "neo4j":
        from graphiti_core.driver.neo4j_driver import Neo4jDriver

        neo = config["engine"]["neo4j"]
        driver = Neo4jDriver(
            uri=neo["uri"],
            user=neo["user"],
            password=neo["password"],
            database=neo.get("database") or "neo4j",
        )
    elif backend == "falkordb":
        from graphiti_core.driver.falkordb_driver import FalkorDriver

        fcfg = config["engine"]["falkordb"]
        parsed = _parse_falkordb_uri(fcfg["uri"])
        driver = FalkorDriver(
            host=parsed["host"],
            port=parsed["port"],
            password=parsed["password"],
            database=fcfg.get("database") or "default_db",
        )
    else:
        raise RuntimeError(f"Unsupported Graphiti backend: {backend}")

    if provider == "openai":
        GraphitiClass, llm_client, embedder, cross_encoder = _openai_clients(config)
        return GraphitiClass(graph_driver=driver, llm_client=llm_client, embedder=embedder, cross_encoder=cross_encoder)

    if provider == "openai_generic":
        from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient
        from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
        from graphiti_core.llm_client.config import LLMConfig
        from graphiti_core.llm_client.openai_generic_client import OpenAIGenericClient

        ocfg = config["engine"]["openai_generic"]
        llm_cfg = LLMConfig(
            api_key=ocfg["apiKey"],
            model=ocfg["model"],
            small_model=ocfg.get("smallModel") or ocfg["model"],
            base_url=ocfg["baseUrl"],
        )
        llm_client = OpenAIGenericClient(config=llm_cfg)
        embedder = OpenAIEmbedder(
            config=OpenAIEmbedderConfig(
                api_key=ocfg["apiKey"],
                embedding_model=ocfg["embeddingModel"],
                embedding_dim=int(ocfg.get("embeddingDim") or 768),
                base_url=ocfg["baseUrl"],
            )
        )
        cross_encoder = OpenAIRerankerClient(client=llm_client, config=llm_cfg)
        return Graphiti(graph_driver=driver, llm_client=llm_client, embedder=embedder, cross_encoder=cross_encoder)

    if provider == "gemini":
        from graphiti_core.cross_encoder.gemini_reranker_client import GeminiRerankerClient
        from graphiti_core.embedder.gemini import GeminiEmbedder, GeminiEmbedderConfig
        from graphiti_core.llm_client.gemini_client import GeminiClient, LLMConfig

        gcfg = config["engine"]["gemini"]
        llm_client = GeminiClient(
            config=LLMConfig(
                api_key=gcfg["apiKey"],
                model=gcfg["model"],
            )
        )
        embedder = GeminiEmbedder(
            config=GeminiEmbedderConfig(
                api_key=gcfg["apiKey"],
                embedding_model=gcfg["embeddingModel"],
            )
        )
        cross_encoder = GeminiRerankerClient(
            config=LLMConfig(
                api_key=gcfg["apiKey"],
                model=gcfg["rerankerModel"],
            )
        )
        return Graphiti(graph_driver=driver, llm_client=llm_client, embedder=embedder, cross_encoder=cross_encoder)

    raise RuntimeError(f"Unsupported Graphiti provider: {provider}")


async def _ingest_async(root: pathlib.Path, config: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    from datetime import datetime, timezone

    graphiti = await _build_graphiti_instance(config)
    init_state = _load_engine_state(root, config)
    try:
        if not init_state.get("initialized"):
            await graphiti.build_indices_and_constraints()
            init_state = {"initialized": True, "initialized_at": now_utc_iso()}
            _save_engine_state(root, config, init_state)

        try:
            from graphiti_core.nodes import EpisodeType

            source_value = {
                "text": EpisodeType.text,
                "json": EpisodeType.json,
                "message": EpisodeType.message,
            }.get(payload.get("source", "text"), EpisodeType.text)
        except Exception:
            source_value = payload.get("source", "text")

        created_at = payload.get("created_at")
        if isinstance(created_at, str):
            try:
                reference_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except ValueError:
                reference_time = datetime.now(timezone.utc)
        else:
            reference_time = datetime.now(timezone.utc)

        result = await graphiti.add_episode(
            name=payload["name"],
            episode_body=payload["episode_body"],
            source=source_value,
            source_description=payload.get("source_description", "Claude Code memory checkpoint"),
            reference_time=reference_time,
            group_id=payload["storage_group_id"],
        )
        return {
            "mode": "graphiti-core",
            "backend": config["engine"]["backend"],
            "provider": config["engine"]["provider"],
            "init_state": init_state,
            "result": str(result),
        }
    finally:
        try:
            await graphiti.close()
        except Exception:
            pass


def ingest_payload(root: pathlib.Path, config: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    if mock_ingest_enabled():
        return {
            "mode": "mock",
            "backend": config["engine"]["backend"],
            "provider": config["engine"]["provider"],
            "payload_id": payload["payload_id"],
            "storage_group_id": payload["storage_group_id"],
            "ingested_at": now_utc_iso(),
        }

    if importlib.util.find_spec("graphiti_core") is None:
        raise RuntimeError(
            "graphiti_core is not installed in the local Python environment used by graphiti_flush.py"
        )

    return asyncio.run(_ingest_async(root, config, payload))
