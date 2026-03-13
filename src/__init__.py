"""
Shared Python package for the EV charging pipeline.

Currently exposes configuration helpers used by scripts and notebooks.
"""

from .config import S3Config, get_s3_config  # noqa: F401


