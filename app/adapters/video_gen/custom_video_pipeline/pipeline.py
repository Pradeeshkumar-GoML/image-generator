"""End-to-end custom text-to-video pipeline orchestrator."""

from __future__ import annotations

import io
import logging
from typing import Self

from app.adapters.video_gen.custom_video_pipeline.config import CustomPipelineConfig
from app.adapters.video_gen.custom_video_pipeline.ltx_transformer import LTXDiffusionTransformer
from app.adapters.video_gen.custom_video_pipeline.ltx_vae_decoder import LTXVAEDecoder
from app.adapters.video_gen.custom_video_pipeline.realesrgan_upscaler import RealESRGAN4xUpscaler
from app.adapters.video_gen.custom_video_pipeline.t5_text_encoder import T5XXLTextEncoder

logger = logging.getLogger(__name__)


class CustomVideoPipeline:
    """
    Compose T5-XXL, LTX transformer, LTX VAE decoder, and Real-ESRGAN into
    a user-extensible text-to-video pipeline.

    Example::

        pipeline = CustomVideoPipeline().load_all()
        video_bytes = pipeline.generate("A cat walking through a sunlit garden")
        pipeline.unload_all()
    """

    def __init__(self, config: CustomPipelineConfig | None = None) -> None:
        self.config = config or CustomPipelineConfig()
        self.text_encoder = T5XXLTextEncoder(self.config)
        self.transformer = LTXDiffusionTransformer(self.config)
        self.vae_decoder = LTXVAEDecoder(self.config)
        self.upscaler = RealESRGAN4xUpscaler(self.config)

    def load_all(self) -> Self:
        """Load every pipeline component."""
        logger.info("Loading custom video pipeline components")
        self.text_encoder.load()
        self.transformer.load()
        self.vae_decoder.load()
        if self.config.enable_upscaling:
            self.upscaler.load()
        return self

    def unload_all(self) -> None:
        """Unload every pipeline component and free GPU memory."""
        self.text_encoder.unload()
        self.transformer.unload()
        self.vae_decoder.unload()
        self.upscaler.unload()

    def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        seed: int | None = None,
    ) -> bytes:
        """
        Run the full text-to-video pipeline and return MP4 bytes.

        Steps:
        1. T5-XXL text encoding
        2. LTX diffusion transformer denoising loop
        3. LTX VAE decoding
        4. Optional Real-ESRGAN 4x upscaling
        5. Export to MP4
        """
        import torch

        generator = None
        if seed is not None:
            generator = torch.Generator(device=self.config.device).manual_seed(seed)

        text_output = self.text_encoder.encode(prompt, negative_prompt=negative_prompt)
        latents = self.transformer.prepare_latents(batch_size=1, generator=generator)

        scheduler = self.transformer.scheduler
        scheduler.set_timesteps(self.config.num_inference_steps, device=self.config.device)

        for t in scheduler.timesteps:
            step_output = self.transformer.denoise(
                latents,
                text_output,
                timestep=t,
                guidance_scale=self.config.guidance_scale,
            )
            latents = scheduler.step(step_output.latents, t, latents).prev_sample

        decoded = self.vae_decoder.decode(latents)
        frames = decoded.frames

        if self.config.enable_upscaling and self.upscaler.is_loaded:
            frames = self.upscaler.upscale(frames).frames

        return self._export_mp4(frames)

    def _export_mp4(self, frames) -> bytes:
        """Convert decoded frames tensor/array to MP4 bytes."""
        import numpy as np

        try:
            import imageio.v3 as iio
        except ImportError as exc:
            raise ImportError(
                "imageio is required to export MP4. Install with: pip install imageio[ffmpeg]"
            ) from exc

        data = frames
        if hasattr(data, "detach"):
            data = data.detach().cpu()

        if data.ndim == 5:
            data = data[0].permute(1, 2, 3, 0)
        elif data.ndim == 4 and data.shape[0] in {1, 3}:
            data = data.permute(1, 2, 3, 0)

        if hasattr(data, "numpy"):
            data = data.numpy()

        data = np.asarray(data)
        if data.dtype != np.uint8:
            data = ((data.clip(-1, 1) + 1) / 2 * 255).astype(np.uint8)

        buffer = io.BytesIO()
        iio.imwrite(
            buffer,
            data,
            extension=".mp4",
            fps=self.config.frame_rate,
            codec="libx264",
        )
        return buffer.getvalue()
