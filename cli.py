#!/usr/bin/env python3
"""
Command line interface for video compression utility.

This module handles command line argument parsing and validation
for the video compression application.
"""

import argparse
import os
import sys
import glob
import logging
from typing import List, Optional, Tuple

from file_utils import FileUtils
from compression_settings import CompressionSettings

logger = logging.getLogger(__name__)


class CLIError(Exception):
    """Custom exception for CLI-related errors."""
    pass


class VideoCompressionCLI:
    """Handles command line interface for video compression."""
    
    def __init__(self):
        """Initialize CLI handler."""
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """
        Create and configure argument parser.
        
        Returns:
            Configured ArgumentParser instance
        """
        parser = argparse.ArgumentParser(
            description='Video Compression Utility - Compress videos with configurable quality settings',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python main.py video.mp4 -q medium                    # Compress with medium quality
  python main.py video.mp4 -s 50MB -o small.mp4        # Compress to 50MB target size
  python main.py *.mp4 --batch -d output/               # Batch compress all MP4s
  python main.py video.mov -c h265 -q high              # Use H.265 codec with high quality
  python main.py video.avi -r 0.5                      # Compress to 50%% of original size
            """
        )
        
        # Input arguments
        parser.add_argument(
            'input', 
            nargs='+', 
            help='Input video file(s) or glob pattern'
        )
        parser.add_argument(
            '-o', '--output', 
            help='Output file path (single file mode)'
        )
        parser.add_argument(
            '-d', '--output-dir', 
            default='./compressed',
            help='Output directory (batch mode, default: ./compressed)'
        )
        
        # Compression settings
        parser.add_argument(
            '-q', '--quality',
            choices=['ultra', 'high', 'medium', 'low'],
            default='medium',
            help='Quality preset (default: medium)'
        )
        parser.add_argument(
            '-c', '--codec',
            choices=['libx264', 'libx265'],
            default='libx264',
            help='Video codec (default: libx264)'
        )
        parser.add_argument(
            '-s', '--size',
            help='Target file size (e.g., 50MB, 1GB)'
        )
        parser.add_argument(
            '-r', '--ratio',
            type=float,
            help='Compression ratio (0.5 = 50%% of original size)'
        )
        parser.add_argument(
            '-f', '--format',
            default='mp4',
            help='Output format (default: mp4)'
        )
        
        # Options
        parser.add_argument(
            '--batch',
            action='store_true',
            help='Enable batch processing mode'
        )
        parser.add_argument(
            '--no-metadata',
            action='store_true',
            help='Do not preserve metadata'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Verbose output'
        )
        parser.add_argument(
            '--quiet',
            action='store_true',
            help='Quiet mode - minimal output'
        )
        
        return parser
    
    def parse_arguments(self, args: Optional[List[str]] = None) -> argparse.Namespace:
        """
        Parse command line arguments.
        
        Args:
            args: Optional list of arguments (for testing)
            
        Returns:
            Parsed arguments namespace
            
        Raises:
            CLIError: If argument parsing fails
        """
        try:
            parsed_args = self.parser.parse_args(args)
            self._validate_arguments(parsed_args)
            return parsed_args
        except argparse.ArgumentTypeError as e:
            raise CLIError(f"Invalid argument: {e}") from e
        except SystemExit as e:
            # argparse calls sys.exit on error
            if e.code != 0:
                raise CLIError("Argument parsing failed") from e
            raise
    
    def _validate_arguments(self, args: argparse.Namespace) -> None:
        """
        Validate parsed arguments for consistency.
        
        Args:
            args: Parsed arguments namespace
            
        Raises:
            CLIError: If arguments are invalid or inconsistent
        """
        # Validate size format if provided
        if args.size:
            try:
                FileUtils.parse_size_string(args.size)
            except ValueError as e:
                raise CLIError(f"Invalid size format: {e}") from e
        
        # Validate compression ratio
        if args.ratio is not None:
            if not 0.1 <= args.ratio <= 1.0:
                raise CLIError("Compression ratio must be between 0.1 and 1.0")
        
        # Check for conflicting options
        if args.size and args.ratio:
            raise CLIError("Cannot specify both target size and compression ratio")
        
        # Validate output options
        if args.output and args.batch:
            logger.warning("Output file specified with batch mode - will use batch mode")
        
        # Check quiet and verbose conflict
        if args.quiet and args.verbose:
            raise CLIError("Cannot specify both --quiet and --verbose")
    
    def expand_input_files(self, input_patterns: List[str]) -> List[str]:
        """
        Expand glob patterns and validate input files.
        
        Args:
            input_patterns: List of file patterns or paths
            
        Returns:
            List of valid input file paths
            
        Raises:
            CLIError: If no valid files found
        """
        input_files = []
        
        for pattern in input_patterns:
            matches = glob.glob(pattern)
            if matches:
                input_files.extend(matches)
            else:
                # If no glob matches, treat as literal filename
                input_files.append(pattern)
        
        # Remove duplicates and filter existing files
        valid_files = []
        seen = set()
        
        for filepath in input_files:
            if filepath in seen:
                continue
            seen.add(filepath)
            
            if not os.path.isfile(filepath):
                logger.warning(f"File not found: {filepath}")
                continue
            
            if not FileUtils.is_supported_format(filepath):
                logger.warning(f"Unsupported format: {filepath}")
                continue
            
            valid_files.append(filepath)
        
        if not valid_files:
            raise CLIError("No valid input files found")
        
        logger.info(f"Found {len(valid_files)} valid input file(s)")
        return valid_files
    
    def determine_processing_mode(self, args: argparse.Namespace, 
                                input_files: List[str]) -> Tuple[str, str]:
        """
        Determine processing mode and output path.
        
        Args:
            args: Parsed arguments
            input_files: List of input files
            
        Returns:
            Tuple of (mode, output_path) where mode is 'single' or 'batch'
        """
        if len(input_files) == 1 and args.output and not args.batch:
            return 'single', args.output
        else:
            return 'batch', args.output_dir
    
    def setup_logging(self, verbose: bool = False, quiet: bool = False) -> None:
        """
        Setup logging configuration based on verbosity level.
        
        Args:
            verbose: Enable verbose logging
            quiet: Enable quiet mode (minimal logging)
        """
        if quiet:
            level = logging.WARNING
        elif verbose:
            level = logging.DEBUG
        else:
            level = logging.INFO
        
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Reduce noise from external libraries
        logging.getLogger('ffmpeg').setLevel(logging.WARNING)
    
    def print_processing_info(self, args: argparse.Namespace, 
                            input_files: List[str]) -> None:
        """
        Print processing information to user.
        
        Args:
            args: Parsed arguments
            input_files: List of input files
        """
        if args.quiet:
            return
        
        print(f"Found {len(input_files)} file(s) to process.")
        print(f"Codec: {args.codec}, Quality: {args.quality}")
        
        if args.size:
            target_size = FileUtils.parse_size_string(args.size)
            print(f"Target size: {target_size}MB")
        
        if args.ratio:
            print(f"Compression ratio: {args.ratio}")
        
        print()  # Empty line for better readability
