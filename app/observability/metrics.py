"""Observability metrics hooks."""

from dataclasses import dataclass, field


@dataclass
class GenerationMetrics:
    """In-memory counters for content generation requests."""

    image_requests: int = 0
    video_requests: int = 0
    image_failures: int = 0
    video_failures: int = 0


metrics = GenerationMetrics()


def record_image_request(*, success: bool = True) -> None:
    metrics.image_requests += 1
    if not success:
        metrics.image_failures += 1


def record_video_request(*, success: bool = True) -> None:
    metrics.video_requests += 1
    if not success:
        metrics.video_failures += 1
