"""T5-XXL text encoder initializer for custom LTX video pipelines."""

from __future__ import annotations

import logging
from typing import Self

from app.adapters.video_gen.custom_video_pipeline.base import PipelineComponent
from app.adapters.video_gen.custom_video_pipeline.config import CustomPipelineConfig
from app.adapters.video_gen.custom_video_pipeline.types import TextEncoderOutput

logger = logging.getLogger(__name__)


class T5XXLTextEncoder(PipelineComponent):
    """
    Initialize and run the T5-XXL text encoder used by LTX-Video.

    Default model: ``google/t5-v1_1-xxl`` (T5EncoderModel + T5TokenizerFast).

    Example::

        config = CustomPipelineConfig(device="cuda")
        encoder = T5XXLTextEncoder(config).load()
        outputs = encoder.encode("A cinematic drone shot over the ocean")
    """

    def __init__(self, config: CustomPipelineConfig) -> None:
        super().__init__(config)
        self._text_encoder = None
        self._tokenizer = None

    def load(self) -> Self:
        if self._is_loaded:
            return self

        import torch
        from transformers import T5EncoderModel, T5TokenizerFast

        dtype = self._config.resolve_dtype()
        load_kwargs = {
            "torch_dtype": dtype,
            "local_files_only": self._config.local_files_only,
        }
        if self._config.hf_token:
            load_kwargs["token"] = self._config.hf_token

        logger.info("Loading T5-XXL text encoder from %s", self._config.t5_model_id)
        self._tokenizer = T5TokenizerFast.from_pretrained(
            self._config.t5_model_id,
            **load_kwargs,
        )
        self._text_encoder = T5EncoderModel.from_pretrained(
            self._config.t5_model_id,
            **load_kwargs,
        )
        self._text_encoder.to(self._config.device)
        self._text_encoder.eval()
        self._is_loaded = True
        return self

    def unload(self) -> None:
        self._text_encoder = None
        self._tokenizer = None
        self._is_loaded = False

        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

    def encode(
        self,
        prompt: str,
        negative_prompt: str = "",
        num_videos_per_prompt: int = 1,
    ) -> TextEncoderOutput:
        """Encode positive and optional negative prompts into embeddings."""
        self._require_loaded()

        import torch

        prompt_embeds, prompt_mask = self._encode_single(
            prompt,
            num_videos_per_prompt=num_videos_per_prompt,
        )
        negative_embeds = None
        negative_mask = None
        if negative_prompt:
            negative_embeds, negative_mask = self._encode_single(
                negative_prompt,
                num_videos_per_prompt=num_videos_per_prompt,
            )

        return TextEncoderOutput(
            prompt_embeds=prompt_embeds,
            negative_prompt_embeds=negative_embeds,
            attention_mask=prompt_mask,
            negative_attention_mask=negative_mask,
        )

    def _encode_single(self, text: str, num_videos_per_prompt: int = 1):
        import torch

        text_inputs = self._tokenizer(
            text,
            padding="max_length",
            max_length=self._config.max_sequence_length,
            truncation=True,
            add_special_tokens=True,
            return_tensors="pt",
        )
        text_input_ids = text_inputs.input_ids.to(self._config.device)
        attention_mask = text_inputs.attention_mask.to(self._config.device)

        with torch.no_grad():
            prompt_embeds = self._text_encoder(
                text_input_ids,
                attention_mask=attention_mask,
            )[0]

        batch_size, seq_len, hidden_dim = prompt_embeds.shape
        prompt_embeds = prompt_embeds.repeat(1, num_videos_per_prompt, 1)
        prompt_embeds = prompt_embeds.view(batch_size * num_videos_per_prompt, seq_len, hidden_dim)

        return prompt_embeds, attention_mask
