"""LTX VAE decoder initializer for custom video pipelines."""

from __future__ import annotations

import logging
from typing import Any, Self

from app.adapters.video_gen.custom_video_pipeline.base import PipelineComponent
from app.adapters.video_gen.custom_video_pipeline.config import CustomPipelineConfig
from app.adapters.video_gen.custom_video_pipeline.types import VAEDecoderOutput

logger = logging.getLogger(__name__)


class LTXVAEDecoder(PipelineComponent):
    """
    Initialize and run the LTX Video-VAE decoder.

    Loads ``AutoencoderKLLTXVideo`` from the configured LTX checkpoint
    (default: ``Lightricks/LTX-Video``, subfolder ``vae``).

    The LTX VAE decoder performs latent-to-pixel conversion and the final
    denoising step in pixel space.

    Example::

        config = CustomPipelineConfig()
        vae = LTXVAEDecoder(config).load()
        frames = vae.decode(latents)
    """

    def __init__(self, config: CustomPipelineConfig) -> None:
        super().__init__(config)
        self._vae = None

    def load(self) -> Self:
        if self._is_loaded:
            return self

        from diffusers import AutoencoderKLLTXVideo

        dtype = self._config.resolve_dtype()
        load_kwargs = {
            "torch_dtype": dtype,
            "local_files_only": self._config.local_files_only,
        }
        if self._config.hf_token:
            load_kwargs["token"] = self._config.hf_token

        model_path = self._config.ltx_model_id
        logger.info(
            "Loading LTX VAE decoder from %s/%s",
            model_path,
            self._config.vae_subfolder,
        )
        self._vae = AutoencoderKLLTXVideo.from_pretrained(
            model_path,
            subfolder=self._config.vae_subfolder,
            **load_kwargs,
        )
        self._vae.to(self._config.device)
        self._vae.eval()

        if self._config.enable_vae_slicing:
            self._vae.enable_slicing()
        if self._config.enable_vae_tiling:
            self._vae.enable_tiling()

        self._is_loaded = True
        return self

    def unload(self) -> None:
        self._vae = None
        self._is_loaded = False

        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

    def decode(
        self,
        latents: Any,
        decode_timestep: float | None = None,
        image_cond_noise_scale: float | None = None,
    ) -> VAEDecoderOutput:
        """Decode latent tensors into video frames."""
        self._require_loaded()

        import torch

        timestep = decode_timestep if decode_timestep is not None else self._config.decode_timestep
        noise_scale = (
            image_cond_noise_scale
            if image_cond_noise_scale is not None
            else self._config.image_cond_noise_scale
        )

        scaling = getattr(self._vae.config, "scaling_factor", 1.0)
        latents = latents / scaling

        decode_kwargs = {}
        if hasattr(self._vae, "decode"):
            sig = self._vae.decode.__code__.co_varnames
            if "timestep" in sig:
                decode_kwargs["timestep"] = timestep
            if "image_cond_noise_scale" in sig:
                decode_kwargs["image_cond_noise_scale"] = noise_scale

        with torch.no_grad():
            decoded = self._vae.decode(latents, **decode_kwargs)
            frames = decoded.sample if hasattr(decoded, "sample") else decoded

        return VAEDecoderOutput(frames=frames)

    def encode(self, frames: Any) -> Any:
        """Encode pixel-space frames into latent representations."""
        self._require_loaded()

        import torch

        with torch.no_grad():
            posterior = self._vae.encode(frames)
            latents = posterior.latent_dist.sample()
        scaling = getattr(self._vae.config, "scaling_factor", 1.0)
        return latents * scaling
