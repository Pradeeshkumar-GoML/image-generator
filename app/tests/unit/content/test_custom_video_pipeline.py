"""Unit tests for custom video pipeline scaffolding (no GPU / model weights required)."""

from app.adapters.video_gen.custom_video_pipeline import (
    CustomPipelineConfig,
    CustomVideoPipeline,
    LTXDiffusionTransformer,
    LTXVAEDecoder,
    RealESRGAN4xUpscaler,
    T5XXLTextEncoder,
)


def test_custom_pipeline_config_defaults():
    config = CustomPipelineConfig()
    assert config.t5_model_id == "google/t5-v1_1-xxl"
    assert config.ltx_model_id == "Lightricks/LTX-Video"
    assert config.realesrgan_model_name == "RealESRGAN_x4plus"
    assert config.enable_upscaling is True


def test_custom_pipeline_initializes_components():
    config = CustomPipelineConfig(enable_upscaling=False)
    pipeline = CustomVideoPipeline(config)

    assert isinstance(pipeline.text_encoder, T5XXLTextEncoder)
    assert isinstance(pipeline.transformer, LTXDiffusionTransformer)
    assert isinstance(pipeline.vae_decoder, LTXVAEDecoder)
    assert isinstance(pipeline.upscaler, RealESRGAN4xUpscaler)
    assert pipeline.text_encoder.is_loaded is False
    assert pipeline.transformer.is_loaded is False


def test_components_not_loaded_until_load_called():
    config = CustomPipelineConfig()
    encoder = T5XXLTextEncoder(config)

    try:
        encoder.encode("test prompt")
        raised = False
    except RuntimeError as exc:
        raised = True
        assert "not loaded" in str(exc).lower()

    assert raised is True
