"""Configuration for the custom LTX-based video generation pipeline."""

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class CustomPipelineConfig:
    """Runtime and model-path settings for custom pipeline components."""

    # Compute
    device: str = "cuda"
    dtype_name: Literal["bfloat16", "float16", "float32"] = "bfloat16"

    # LTX checkpoint (Hugging Face repo or local path)
    ltx_model_id: str = "Lightricks/LTX-Video"
    transformer_subfolder: str = "transformer"
    vae_subfolder: str = "vae"

    # T5-XXL text encoder (used by LTX)
    t5_model_id: str = "google/t5-v1_1-xxl"
    max_sequence_length: int = 256

    # Diffusion sampling
    num_inference_steps: int = 30
    guidance_scale: float = 5.0
    decode_timestep: float = 0.05
    image_cond_noise_scale: float = 0.025

    # Output resolution (before upscaling)
    height: int = 512
    width: int = 768
    num_frames: int = 121
    frame_rate: int = 24

    # Real-ESRGAN 4x upscaler
    realesrgan_model_name: str = "RealESRGAN_x4plus"
    realesrgan_model_path: str = "weights/RealESRGAN_x4plus.pth"
    realesrgan_tile_size: int = 0
    enable_upscaling: bool = True

    # Hugging Face cache / auth
    hf_token: str | None = None
    local_files_only: bool = False

    # Memory optimization
    enable_cpu_offload: bool = False
    enable_vae_slicing: bool = True
    enable_vae_tiling: bool = False

    extra: dict = field(default_factory=dict)

    def resolve_dtype(self):
        """Resolve torch dtype from string name (lazy import)."""
        import torch

        mapping = {
            "bfloat16": torch.bfloat16,
            "float16": torch.float16,
            "float32": torch.float32,
        }
        return mapping[self.dtype_name]
