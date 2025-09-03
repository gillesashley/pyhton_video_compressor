#!/usr/bin/env python3
"""
Compression settings and configuration management.

This module handles video compression settings, quality presets,
and bitrate calculations for the video compression application.
"""

from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class CompressionSettings:
    """Manages video compression settings and quality presets."""
    
    # Quality presets with CRF values, encoding presets, and bitrate factors
    QUALITY_PRESETS: Dict[str, Dict] = {
        'ultra': {
            'crf': 15,
            'preset': 'slow',
            'bitrate_factor': 0.9,
            'description': 'Highest quality, largest file size'
        },
        'high': {
            'crf': 18,
            'preset': 'medium',
            'bitrate_factor': 0.8,
            'description': 'High quality, good for archival'
        },
        'medium': {
            'crf': 23,
            'preset': 'medium',
            'bitrate_factor': 0.6,
            'description': 'Balanced quality and size'
        },
        'low': {
            'crf': 28,
            'preset': 'fast',
            'bitrate_factor': 0.4,
            'description': 'Lower quality, smaller file size'
        }
    }
    
    # Supported video codecs
    SUPPORTED_CODECS: Dict[str, Dict] = {
        'libx264': {
            'name': 'H.264/AVC',
            'description': 'Widely compatible, good quality',
            'file_extension': 'mp4'
        },
        'libx265': {
            'name': 'H.265/HEVC',
            'description': 'Better compression, newer standard',
            'file_extension': 'mp4'
        }
    }
    
    # Minimum bitrate to prevent extremely low quality
    MIN_BITRATE_KBPS = 100
    
    @classmethod
    def get_available_qualities(cls) -> list:
        """Get list of available quality preset names."""
        return list(cls.QUALITY_PRESETS.keys())
    
    @classmethod
    def get_available_codecs(cls) -> list:
        """Get list of available codec names."""
        return list(cls.SUPPORTED_CODECS.keys())
    
    @classmethod
    def validate_quality(cls, quality: str) -> bool:
        """
        Validate if quality preset exists.
        
        Args:
            quality: Quality preset name
            
        Returns:
            True if quality preset exists, False otherwise
        """
        return quality in cls.QUALITY_PRESETS
    
    @classmethod
    def validate_codec(cls, codec: str) -> bool:
        """
        Validate if codec is supported.
        
        Args:
            codec: Codec name
            
        Returns:
            True if codec is supported, False otherwise
        """
        return codec in cls.SUPPORTED_CODECS
    
    @classmethod
    def calculate_target_bitrate(cls, video_info: Dict, 
                               target_size_mb: Optional[float] = None,
                               compression_ratio: Optional[float] = None) -> int:
        """
        Calculate target bitrate based on file size or compression ratio.
        
        Args:
            video_info: Dictionary containing video information (duration, bitrate, etc.)
            target_size_mb: Target file size in megabytes
            compression_ratio: Compression ratio (0.5 = 50% of original size)
            
        Returns:
            Target bitrate in bits per second
            
        Raises:
            ValueError: If video_info is missing required fields
        """
        try:
            duration = video_info['duration']
            original_bitrate = video_info['bitrate']
        except KeyError as e:
            raise ValueError(f"Missing required video info field: {e}") from e
        
        if target_size_mb:
            # Convert MB to bits and calculate bitrate
            target_size_bits = target_size_mb * 8 * 1024 * 1024
            # Reserve 10% for audio and container overhead
            video_bitrate = int((target_size_bits * 0.9) / duration)
            logger.debug(f"Calculated bitrate for {target_size_mb}MB target: {video_bitrate} bps")
        elif compression_ratio:
            video_bitrate = int(original_bitrate * compression_ratio)
            logger.debug(f"Calculated bitrate for {compression_ratio} ratio: {video_bitrate} bps")
        else:
            video_bitrate = original_bitrate
        
        # Ensure minimum bitrate
        min_bitrate_bps = cls.MIN_BITRATE_KBPS * 1000
        return max(video_bitrate, min_bitrate_bps)
    
    @classmethod
    def get_compression_settings(cls, quality: str, codec: str, video_info: Dict,
                               target_size_mb: Optional[float] = None,
                               compression_ratio: Optional[float] = None) -> Dict:
        """
        Get complete compression settings based on parameters.
        
        Args:
            quality: Quality preset name
            codec: Video codec name
            video_info: Dictionary containing video information
            target_size_mb: Optional target file size in megabytes
            compression_ratio: Optional compression ratio
            
        Returns:
            Dictionary containing compression settings
            
        Raises:
            ValueError: If quality or codec is invalid
        """
        if not cls.validate_quality(quality):
            raise ValueError(f"Invalid quality preset: {quality}. "
                           f"Available: {cls.get_available_qualities()}")
        
        if not cls.validate_codec(codec):
            raise ValueError(f"Invalid codec: {codec}. "
                           f"Available: {cls.get_available_codecs()}")
        
        preset = cls.QUALITY_PRESETS[quality]
        settings = {
            'codec': codec,
            'crf': preset['crf'],
            'preset': preset['preset'],
            'quality_name': quality,
            'codec_name': cls.SUPPORTED_CODECS[codec]['name']
        }
        
        # Calculate bitrate if target size or ratio specified
        if target_size_mb or compression_ratio:
            if not compression_ratio:
                compression_ratio = preset['bitrate_factor']
            
            target_bitrate = cls.calculate_target_bitrate(
                video_info, target_size_mb, compression_ratio
            )
            settings['bitrate'] = f"{target_bitrate // 1000}k"
            settings['target_bitrate_bps'] = target_bitrate
            
            logger.info(f"Using bitrate-based encoding: {settings['bitrate']}")
        else:
            logger.info(f"Using CRF-based encoding: CRF {settings['crf']}")
        
        return settings
    
    @classmethod
    def get_codec_specific_params(cls, codec: str) -> Dict:
        """
        Get codec-specific parameters for FFmpeg.
        
        Args:
            codec: Video codec name
            
        Returns:
            Dictionary of codec-specific parameters
        """
        codec_params = {}
        
        if codec == 'libx265':
            codec_params['extra_params'] = ['-x265-params', 'log-level=error']
        elif codec == 'libx264':
            codec_params['extra_params'] = ['-movflags', '+faststart']
        
        return codec_params
