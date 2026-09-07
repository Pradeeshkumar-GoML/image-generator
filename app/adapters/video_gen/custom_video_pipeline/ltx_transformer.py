"""LTX diffusion transformer initializer for custom video pipelines."""

from __future__ import annotations

import logging
from typing import Any, Self

from app.adapters.video_gen.custom_video_pipeline.base import PipelineComponent
from app.adapters.video_gen.custom_video_pipeline.config import CustomPipelineConfig
from app.adapters.video_gen.custom_video_pipeline.types import TextEncoderOutput, TransformerOutput

logger = logging.getLogger(__name__)


class LTXDiffusionTransformer(PipelineComponent):
    """
    Initialize and run the LTX diffusion transformer (denoising backbone).

    Loads ``LTXVideoTransformer3DModel`` from the configured LTX checkpoint
    (default: ``Lightricks/LTX-Video``, subfolder ``transformer``).

    Example::

        config = CustomPipelineConfig()
        transformer = LTXDiffusionTransformer(config).load()
        output = transformer.denoise(latents, text_output, timestep=500)
    """

    def __init__(self, config: CustomPipelineConfig) -> None:
        super().__init__(config)
        self._transformer = None
        self._scheduler = None

    def load(self) -> Self:
        if self._is_loaded:
            return self

        from diffusers import FlowMatchEulerDiscreteScheduler, LTXVideoTransformer3DModel

        dtype = self._config.resolve_dtype()
        load_kwargs = {
            "torch_dtype": dtype,
            "local_files_only": self._config.local_files_only,
        }
        if self._config.hf_token:
            load_kwargs["token"] = self._config.hf_token

        model_path = self._config.ltx_model_id
        logger.info(
            "Loading LTX diffusion transformer from %s/%s",
            model_path,
            self._config.transformer_subfolder,
        )
        self._transformer = LTXVideoTransformer3DModel.from_pretrained(
            model_path,
            subfolder=self._config.transformer_subfolder,
            **load_kwargs,
        )
        self._transformer.to(self._config.device)
        self._transformer.eval()

        self._scheduler = FlowMatchEulerDiscreteScheduler.from_pretrained(
            model_path,
            subfolder="scheduler",
            **{k: v for k, v in load_kwargs.items() if k != "torch_dtype"},
        )

        self._is_loaded = True
        return self

    def unload(self) -> None:
        self._transformer = None
        self._scheduler = None
        self._is_loaded = False

        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

    @property
    def scheduler(self):
        self._require_loaded()
        return self._scheduler

    def prepare_latents(self, batch_size: int = 1, generator: Any | None = None):
        """Create initial noise latents matching LTX transformer input shape."""
        self._require_loaded()

        import torch

        vae_scale = getattr(self._transformer.config, "patch_size", 1)
        latent_frames = (self._config.num_frames - 1) // 8 + 1
        latent_height = self._config.height // 32
        latent_width = self._config.width // 32
        in_channels = self._transformer.config.in_channels

        shape = (
            batch_size,
            in_channels,
            latent_frames,
            latent_height,
            latent_width,
        )
        latents = torch.randn(shape, generator=generator, device=self._config.device)
        return latents * vae_scale

    def denoise(
        self,
        latents: Any,
        text_output: TextEncoderOutput,
        timestep: int | float,
        guidance_scale: float | None = None,
    ) -> TransformerOutput:
        """
        Run a single denoising step with the LTX transformer.

        For full sampling loops, use :class:`CustomVideoPipeline` which
        orchestrates scheduler timesteps end-to-end.
        """
        self._require_loaded()

        import torch

        guidance = guidance_scale if guidance_scale is not None else self._config.guidance_scale
        prompt_embeds = text_output.prompt_embeds
        encoder_hidden_states = prompt_embeds

        if guidance > 1.0 and text_output.negative_prompt_embeds is not None:
            negative_embeds = text_output.negative_prompt_embeds
            encoder_hidden_states = torch.cat([negative_embeds, prompt_embeds], dim=0)
            latents = torch.cat([latents, latents], dim=0)

        t = torch.tensor([timestep], device=self._config.device, dtype=latents.dtype)
        with torch.no_grad():
            noise_pred = self._transformer(
                hidden_states=latents,
                encoder_hidden_states=encoder_hidden_states,
                timestep=t,
                return_dict=False,
            )[0]

        if guidance > 1.0 and text_output.negative_prompt_embeds is not None:
            noise_pred_uncond, noise_pred_text = noise_pred.chunk(2)
            noise_pred = noise_pred_uncond + guidance * (noise_pred_text - noise_pred_uncond)

        return TransformerOutput(latents=noise_pred)
