"""Shared types for custom video pipeline components."""

from dataclasses import dataclass
from typing import Any


@dataclass
class TextEncoderOutput:
    """Encoded prompt tensors produced by T5-XXL."""

    prompt_embeds: Any
    negative_prompt_embeds: Any | None = None
    attention_mask: Any | None = None
    negative_attention_mask: Any | None = None


@dataclass
class TransformerOutput:
    """Denoised latents from the LTX diffusion transformer."""

    latents: Any


@dataclass
class VAEDecoderOutput:
    """Decoded video frames from the LTX VAE decoder."""

    frames: Any
    """Tensor or ndarray shaped (batch, channels, frames, height, width)."""


@dataclass
class UpscalerOutput:
    """Upscaled video frames from Real-ESRGAN."""

    frames: Any
