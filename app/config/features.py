"""Registration and discovery of enabled feature modules."""

from app.api.endpoints.content.api import FEATURE as content_feature

ENABLED_FEATURES = [content_feature]
