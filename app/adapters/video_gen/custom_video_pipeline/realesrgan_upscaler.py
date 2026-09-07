"""Real-ESRGAN 4x upscaler initializer for custom video pipelines."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Self

from app.adapters.video_gen.custom_video_pipeline.base import PipelineComponent
from app.adapters.video_gen.custom_video_pipeline.config import CustomPipelineConfig
from app.adapters.video_gen.custom_video_pipeline.types import UpscalerOutput

logger = logging.getLogger(__name__)


class RealESRGAN4xUpscaler(PipelineComponent):
    """
    Initialize and run Real-ESRGAN 4x video frame upscaling.

    Default model: ``RealESRGAN_x4plus`` (4x super-resolution).

    Example::

        config = CustomPipelineConfig(realesrgan_model_path="weights/RealESRGAN_x4plus.pth")
        upscaler = RealESRGAN4xUpscaler(config).load()
        result = upscaler.upscale(frames)
    """

    def __init__(self, config: CustomPipelineConfig) -> None:
        super().__init__(config)
        self._upsampler = None

    def load(self) -> Self:
        if self._is_loaded:
            return self

        import torch

        from basicsr.archs.rrdbnet_arch import RRDBNet
        from realesrgan import RealESRGANer

        model_name = self._config.realesrgan_model_name
        model_path = self._config.realesrgan_model_path

        if model_name == "RealESRGAN_x4plus":
            model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
            netscale = 4
        elif model_name == "RealESRGAN_x4plus_anime_6B":
            model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=6, num_grow_ch=32, scale=4)
            netscale = 4
        else:
            raise ValueError(f"Unsupported Real-ESRGAN model: {model_name}")

        if not Path(model_path).exists():
            logger.warning(
                "Real-ESRGAN weights not found at %s. "
                "Download RealESRGAN_x4plus.pth and place it at the configured path.",
                model_path,
            )

        dtype = self._config.resolve_dtype()
        self._upsampler = RealESRGANer(
            scale=netscale,
            model_path=model_path,
            model=model,
            tile=self._config.realesrgan_tile_size,
            tile_pad=10,
            pre_pad=0,
            half=dtype in {torch.float16, torch.bfloat16},
            device=self._config.device,
        )

        logger.info("Loaded Real-ESRGAN upscaler: %s", model_name)
        self._is_loaded = True
        return self

    def unload(self) -> None:
        self._upsampler = None
        self._is_loaded = False

        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

    def upscale(self, frames: Any) -> UpscalerOutput:
        """
        Upscale video frames by 4x using Real-ESRGAN.

        Accepts a tensor ``(B, C, F, H, W)`` or ``(F, H, W, C)`` numpy array.
        Returns frames in the same layout with 4x spatial resolution.
        """
        self._require_loaded()

        import numpy as np

        tensor_input = hasattr(frames, "detach")
        if tensor_input:
            import torch

            data = frames.detach().cpu()
            if data.ndim == 5:
                batch, channels, num_frames, height, width = data.shape
                data = data.permute(0, 2, 3, 4, 1).reshape(batch * num_frames, height, width, channels)
                data = (data.clamp(-1, 1) + 1) / 2 * 255
                data = data.numpy().astype(np.uint8)
                flat_batch = True
            else:
                flat_batch = False
                data = (data.clamp(-1, 1) + 1) / 2 * 255
                data = data.numpy().astype(np.uint8)
        else:
            data = np.asarray(frames)
            flat_batch = False

        upscaled_frames = []
        for frame in data:
            if frame.ndim == 3 and frame.shape[0] in {1, 3}:
                frame = np.transpose(frame, (1, 2, 0))
            output, _ = self._upsampler.enhance(frame, outscale=4)
            upscaled_frames.append(output)

        result = np.stack(upscaled_frames, axis=0)

        if tensor_input and flat_batch:
            import torch

            batch, channels, num_frames, _, _ = frames.shape
            result = result.reshape(batch, num_frames, result.shape[1], result.shape[2], 3)
            result = torch.from_numpy(result).permute(0, 4, 1, 2, 3).float() / 255.0 * 2 - 1
            return UpscalerOutput(frames=result)

        if tensor_input:
            import torch

            result = torch.from_numpy(result).float() / 255.0 * 2 - 1
            return UpscalerOutput(frames=result)

        return UpscalerOutput(frames=result)
