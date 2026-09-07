from __future__ import annotations

import asyncio
import base64
import json
import os
from typing import Any, Dict, List, Optional, Tuple, Union

import boto3
from botocore.config import Config

from app.core.model_gateway.schemas import Choices, Message, ModelResponse, Usage

# Converse request fields callers may pass through verbatim. Model-specific knobs
# that Converse does not model natively (e.g. top_k) go in additionalModelRequestFields.
_CONVERSE_PASSTHROUGH_PARAMS = (
    "toolConfig",
    "guardrailConfig",
    "additionalModelRequestFields",
    "additionalModelResponseFieldPaths",
    "performanceConfig",
    "promptVariables",
    "requestMetadata",
)

# Anthropic models accept only one of temperature/topP; Claude 4.x rejects the
# request when both are set, so temperature (the explicit knob) wins.
_SINGLE_SAMPLING_PARAM_MARKERS = ("anthropic.", "claude")

_STOP_REASON_TO_FINISH_REASON = {
    "end_turn": "stop",
    "stop_sequence": "stop",
    "max_tokens": "length",
    "tool_use": "tool_calls",
    "content_filtered": "content_filter",
    "guardrail_intervened": "content_filter",
}

_CONVERSE_BLOCK_KEYS = frozenset(
    {
        "text",
        "image",
        "document",
        "video",
        "toolUse",
        "toolResult",
        "guardContent",
        "reasoningContent",
        "cachePoint",
    }
)

_IMAGE_FORMATS = {"png": "png", "jpeg": "jpeg", "jpg": "jpeg", "gif": "gif", "webp": "webp"}

_client_cache: Dict[Tuple[str, Optional[int]], Any] = {}


def _bedrock_client(timeout: Optional[Any] = None) -> Any:
    region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"
    read_timeout = int(timeout) if isinstance(timeout, (int, float)) else None
    cache_key = (region, read_timeout)
    client = _client_cache.get(cache_key)
    if client is None:
        config = Config(
            retries={"max_attempts": 3, "mode": "adaptive"},
            **({} if read_timeout is None else {"read_timeout": read_timeout}),
        )
        client = boto3.client("bedrock-runtime", region_name=region, config=config)
        _client_cache[cache_key] = client
    return client


def bedrock_embedding(
    *,
    model: str,
    input: Union[str, List[str]],
    timeout: Optional[Any] = None,
    **kwargs: Any,
) -> Any:
    """
    Minimal embedding wrapper for Bedrock Titan embedding models.

    Returns an OpenAI-like dict: {"data": [{"embedding": [...]}, ...]}
    """

    client = _bedrock_client(timeout)
    model_id = model.replace("bedrock/", "")

    if isinstance(input, list):
        vectors: List[List[float]] = []
        for text in input:
            body = json.dumps({"inputText": text})
            resp = client.invoke_model(modelId=model_id, body=body)
            payload = json.loads(resp["body"].read().decode("utf-8"))
            vec = payload.get("embedding") or payload.get("vector") or []
            vectors.append([float(x) for x in vec])
        return {"data": [{"embedding": v} for v in vectors]}

    body = json.dumps({"inputText": input})
    resp = client.invoke_model(modelId=model_id, body=body)
    payload = json.loads(resp["body"].read().decode("utf-8"))
    vec = payload.get("embedding") or payload.get("vector") or []
    return {"data": [{"embedding": [float(x) for x in vec]}]}


def _image_block(data: Any, media_type: Optional[str]) -> Optional[Dict[str, Any]]:
    """Build a Converse image block from base64 or raw image bytes."""

    if not data:
        return None
    fmt = _IMAGE_FORMATS.get(str(media_type or "image/png").rsplit("/", 1)[-1].lower())
    if fmt is None:
        return None
    try:
        raw = base64.b64decode(data) if isinstance(data, str) else bytes(data)
    except (ValueError, TypeError):
        return None
    return {"image": {"format": fmt, "source": {"bytes": raw}}}


def _image_block_from_url(url: str) -> Optional[Dict[str, Any]]:
    if not url.startswith("data:"):
        return None
    header, _, payload = url.partition(",")
    return _image_block(payload, header[len("data:") :].split(";", 1)[0])


def _content_blocks(content: Any) -> List[Dict[str, Any]]:
    """Normalize OpenAI/Anthropic-style content into Converse content blocks."""

    if content is None:
        return []
    if isinstance(content, str):
        return [{"text": content}] if content else []

    blocks: List[Dict[str, Any]] = []
    for part in content if isinstance(content, list) else [content]:
        if isinstance(part, str):
            if part:
                blocks.append({"text": part})
            continue
        if not isinstance(part, dict):
            blocks.append({"text": str(part)})
            continue

        part_type = part.get("type")
        if part_type is None and _CONVERSE_BLOCK_KEYS & set(part.keys()):
            blocks.append(part)
        elif part_type in (None, "text") and part.get("text") is not None:
            blocks.append({"text": str(part["text"])})
        elif part_type == "image":
            source = part.get("source") or {}
            block = _image_block(source.get("data"), source.get("media_type"))
            if block:
                blocks.append(block)
        elif part_type == "image_url":
            image_url = part.get("image_url")
            url = image_url.get("url") if isinstance(image_url, dict) else image_url
            block = _image_block_from_url(str(url or ""))
            if block:
                blocks.append(block)
    return blocks


def _split_messages(
    messages: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Split chat messages into Converse `system` blocks and alternating turns."""

    system_blocks: List[Dict[str, Any]] = []
    converse_messages: List[Dict[str, Any]] = []

    for message in messages:
        role = message.get("role")
        blocks = _content_blocks(message.get("content"))
        if not blocks:
            continue
        if role in ("system", "developer"):
            system_blocks.extend(b for b in blocks if "text" in b)
            continue
        if role not in ("user", "assistant"):
            continue
        # Converse requires roles to alternate, so merge consecutive same-role turns.
        if converse_messages and converse_messages[-1]["role"] == role:
            converse_messages[-1]["content"].extend(blocks)
        else:
            converse_messages.append({"role": role, "content": blocks})

    return system_blocks, converse_messages


def _build_inference_config(model_id: str, optional_params: Dict[str, Any]) -> Dict[str, Any]:
    max_tokens = optional_params.get("max_tokens") or optional_params.get("max_completion_tokens")
    temperature = optional_params.get("temperature")
    top_p = optional_params.get("top_p")
    stop = optional_params.get("stop")

    if (
        temperature is not None
        and top_p is not None
        and any(marker in model_id.lower() for marker in _SINGLE_SAMPLING_PARAM_MARKERS)
    ):
        top_p = None

    config: Dict[str, Any] = {}
    if max_tokens is not None:
        config["maxTokens"] = int(max_tokens)
    if temperature is not None:
        config["temperature"] = float(temperature)
    if top_p is not None:
        config["topP"] = float(top_p)
    if stop:
        config["stopSequences"] = [stop] if isinstance(stop, str) else [str(s) for s in stop]
    return config


def _build_model_response(model: str, resp: Dict[str, Any]) -> ModelResponse:
    blocks = ((resp.get("output") or {}).get("message") or {}).get("content") or []
    text = "".join(
        str(b.get("text", "")) for b in blocks if isinstance(b, dict) and b.get("text")
    )

    raw_usage = resp.get("usage") or {}
    usage: Optional[Usage] = None
    if isinstance(raw_usage, dict) and raw_usage:
        prompt_tokens = raw_usage.get("inputTokens")
        completion_tokens = raw_usage.get("outputTokens")
        total_tokens = raw_usage.get("totalTokens")
        if total_tokens is None and prompt_tokens is not None and completion_tokens is not None:
            total_tokens = int(prompt_tokens) + int(completion_tokens)
        usage = Usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )

    stop_reason = resp.get("stopReason")
    extra: Dict[str, Any] = {}
    if isinstance(raw_usage, dict):
        for src, dst in (
            ("cacheReadInputTokens", "cache_read_input_tokens"),
            ("cacheWriteInputTokens", "cache_write_input_tokens"),
        ):
            if raw_usage.get(src) is not None:
                extra[dst] = int(raw_usage[src])
    latency_ms = (resp.get("metrics") or {}).get("latencyMs")
    if latency_ms is not None:
        extra["latency_ms"] = int(latency_ms)
    if resp.get("additionalModelResponseFields") is not None:
        extra["additional_model_response_fields"] = resp["additionalModelResponseFields"]

    return ModelResponse(
        id=(resp.get("ResponseMetadata") or {}).get("RequestId"),
        object="chat.completion",
        model=model,
        choices=[
            Choices(
                index=0,
                message=Message(role="assistant", content=text),
                finish_reason=_STOP_REASON_TO_FINISH_REASON.get(str(stop_reason), "stop"),
            )
        ],
        usage=usage,
        **extra,
    )


def bedrock_chat_completion(
    *,
    model: str,
    messages: List[Dict[str, Any]],
    optional_params: Dict[str, Any],
    timeout: Optional[Any] = None,
) -> ModelResponse:
    """
    Bedrock chat via the Converse API.

    Returns an OpenAI-chat-compatible `ModelResponse`, matching the shape the
    OpenAI-compatible providers return.
    """

    client = _bedrock_client(timeout)
    model_id = model.replace("bedrock/", "")

    system_blocks, converse_messages = _split_messages(messages)
    if optional_params.get("system"):
        extra_system = optional_params["system"]
        system_blocks = (
            list(extra_system) if isinstance(extra_system, list) else [{"text": str(extra_system)}]
        ) + system_blocks

    inference_config = _build_inference_config(model_id, optional_params)
    request: Dict[str, Any] = {"modelId": model_id, "messages": converse_messages}
    if system_blocks:
        request["system"] = system_blocks
    if inference_config:
        request["inferenceConfig"] = inference_config
    for key in _CONVERSE_PASSTHROUGH_PARAMS:
        if optional_params.get(key) is not None:
            request[key] = optional_params[key]

    resp = client.converse(**request)
    return _build_model_response(model, resp)


async def abedrock_chat_completion(
    *,
    model: str,
    messages: List[Dict[str, Any]],
    optional_params: Dict[str, Any],
    timeout: Optional[Any] = None,
) -> ModelResponse:
    return await asyncio.to_thread(
        bedrock_chat_completion,
        model=model,
        messages=messages,
        optional_params=optional_params,
        timeout=timeout,
    )
