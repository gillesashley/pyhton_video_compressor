#!/usr/bin/env python3
"""
File utilities for video compression.

This module provides utility functions for file handling, size parsing,
and format validation used throughout the video compression application.
"""

import os
import math
from pathlib import Path
from typing import Set


class FileUtils:
    """Utility class for file operations and validations."""
    
    # Supported video formats
    SUPPORTED_FORMATS: Set[str] = {
        '.mp4', '.avi', '.mov', '.mkv', '.wmv', 
        '.flv', '.webm', '.m4v'
    }
    
    @staticmethod
    def is_supported_format(filepath: str) -> bool:
        """
        Check if file format is supported for video compression.
        
        Args:
            filepath: Path to the video file
            
        Returns:
            True if format is supported, False otherwise
        """
        return Path(filepath).suffix.lower() in FileUtils.SUPPORTED_FORMATS
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        Format file size in human-readable format.
        
        Args:
            size_bytes: File size in bytes
            
        Returns:
            Formatted size string (e.g., "1.5 GB", "250 MB")
        """
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"
    
    @staticmethod
    def parse_size_string(size_str: str) -> float:
        """
        Parse size string like '100MB' to float in MB.
        
        Args:
            size_str: Size string with unit (e.g., "100MB", "1.5GB", "500KB")
            
        Returns:
            Size in megabytes as float
            
        Raises:
            ValueError: If size string format is invalid
        """
        try:
            size_str = size_str.upper().replace(' ', '')
            
            if size_str.endswith('GB'):
                return float(size_str[:-2]) * 1024
            elif size_str.endswith('MB'):
                return float(size_str[:-2])
            elif size_str.endswith('KB'):
                return float(size_str[:-2]) / 1024
            elif size_str.endswith('B'):
                return float(size_str[:-1]) / (1024 * 1024)
            else:
                # Assume MB if no unit specified
                return float(size_str)
        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid size format: {size_str}") from e
    
    @staticmethod
    def ensure_directory_exists(directory_path: str) -> None:
        """
        Ensure that a directory exists, creating it if necessary.
        
        Args:
            directory_path: Path to the directory
            
        Raises:
            OSError: If directory cannot be created
        """
        try:
            os.makedirs(directory_path, exist_ok=True)
        except OSError as e:
            raise OSError(f"Cannot create directory {directory_path}: {e}") from e
    
    @staticmethod
    def get_safe_filename(filename: str) -> str:
        """
        Generate a safe filename by removing/replacing problematic characters.
        
        Args:
            filename: Original filename
            
        Returns:
            Safe filename with problematic characters replaced
        """
        # Characters that are problematic in filenames
        unsafe_chars = '<>:"/\\|?*'
        safe_filename = filename
        
        for char in unsafe_chars:
            safe_filename = safe_filename.replace(char, '_')
        
        # Remove multiple consecutive underscores
        while '__' in safe_filename:
            safe_filename = safe_filename.replace('__', '_')
        
        # Remove leading/trailing underscores and dots
        safe_filename = safe_filename.strip('_.')
        
        return safe_filename or 'unnamed'
    
    @staticmethod
    def generate_output_path(input_path: str, output_dir: str, 
                           suffix: str = "_compressed", 
                           output_format: str = "mp4") -> str:
        """
        Generate output file path based on input path and parameters.
        
        Args:
            input_path: Path to input file
            output_dir: Output directory
            suffix: Suffix to add to filename (default: "_compressed")
            output_format: Output file format (default: "mp4")
            
        Returns:
            Generated output file path
        """
        input_name = Path(input_path).stem
        safe_name = FileUtils.get_safe_filename(f"{input_name}{suffix}")
        return os.path.join(output_dir, f"{safe_name}.{output_format}")
    
    @staticmethod
    def calculate_compression_ratio(original_size: int, compressed_size: int) -> float:
        """
        Calculate compression ratio as percentage of space saved.
        
        Args:
            original_size: Original file size in bytes
            compressed_size: Compressed file size in bytes
            
        Returns:
            Compression ratio as percentage (0-100)
        """
        if original_size == 0:
            return 0.0
        return (1 - compressed_size / original_size) * 100
