#!/usr/bin/env python3
"""
Progress tracking for video compression operations.

This module provides progress tracking functionality using tqdm
for visual feedback during video compression operations.
"""

import re
import logging
from typing import Optional, Dict, Any
from tqdm import tqdm

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Handles progress tracking for video compression operations."""
    
    def __init__(self, total_frames: int, description: str = "Processing"):
        """
        Initialize progress tracker.
        
        Args:
            total_frames: Total number of frames to process
            description: Description to display in progress bar
        """
        self.total_frames = total_frames
        self.description = description
        self.progress_bar: Optional[tqdm] = None
        self.current_frame = 0
        
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def start(self) -> None:
        """Start the progress bar."""
        self.progress_bar = tqdm(
            total=self.total_frames,
            unit='frames',
            desc=self.description,
            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} frames [{elapsed}<{remaining}]'
        )
        logger.debug(f"Started progress tracking for {self.total_frames} frames")
    
    def update_from_ffmpeg_output(self, output_line: str) -> bool:
        """
        Update progress based on FFmpeg output line.
        
        Args:
            output_line: Line of output from FFmpeg stderr
            
        Returns:
            True if progress was updated, False otherwise
        """
        if not self.progress_bar:
            return False
        
        # Look for frame information in FFmpeg output
        # Example: "frame= 1234 fps=25.0 q=23.0 size=    1024kB time=00:00:49.36 bitrate= 170.1kbits/s speed=1.0x"
        frame_match = re.search(r'frame=\s*(\d+)', output_line)
        if frame_match:
            try:
                frame_num = int(frame_match.group(1))
                # Ensure we don't exceed total frames
                frame_num = min(frame_num, self.total_frames)
                
                if frame_num > self.current_frame:
                    self.progress_bar.n = frame_num
                    self.progress_bar.refresh()
                    self.current_frame = frame_num
                    return True
            except (ValueError, IndexError):
                pass
        
        return False
    
    def set_progress(self, current: int) -> None:
        """
        Set progress to specific value.
        
        Args:
            current: Current progress value
        """
        if self.progress_bar:
            current = min(current, self.total_frames)
            self.progress_bar.n = current
            self.progress_bar.refresh()
            self.current_frame = current
    
    def increment(self, amount: int = 1) -> None:
        """
        Increment progress by specified amount.
        
        Args:
            amount: Amount to increment progress
        """
        if self.progress_bar:
            new_progress = min(self.current_frame + amount, self.total_frames)
            self.progress_bar.n = new_progress
            self.progress_bar.refresh()
            self.current_frame = new_progress
    
    def complete(self) -> None:
        """Mark progress as complete."""
        if self.progress_bar:
            self.progress_bar.n = self.total_frames
            self.progress_bar.refresh()
            self.current_frame = self.total_frames
    
    def close(self) -> None:
        """Close the progress bar."""
        if self.progress_bar:
            self.progress_bar.close()
            self.progress_bar = None
            logger.debug("Progress tracking closed")
    
    def update_description(self, description: str) -> None:
        """
        Update progress bar description.
        
        Args:
            description: New description
        """
        if self.progress_bar:
            self.progress_bar.set_description(description)
    
    @property
    def is_complete(self) -> bool:
        """Check if progress is complete."""
        return self.current_frame >= self.total_frames
    
    @property
    def progress_percentage(self) -> float:
        """Get current progress as percentage."""
        if self.total_frames == 0:
            return 0.0
        return (self.current_frame / self.total_frames) * 100


class BatchProgressTracker:
    """Tracks progress for batch operations with multiple files."""
    
    def __init__(self, total_files: int):
        """
        Initialize batch progress tracker.
        
        Args:
            total_files: Total number of files to process
        """
        self.total_files = total_files
        self.current_file = 0
        self.file_progress_bar: Optional[tqdm] = None
        self.current_file_tracker: Optional[ProgressTracker] = None
        
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def start(self) -> None:
        """Start batch progress tracking."""
        self.file_progress_bar = tqdm(
            total=self.total_files,
            unit='files',
            desc='Overall Progress',
            position=0,
            leave=True
        )
        logger.debug(f"Started batch progress tracking for {self.total_files} files")
    
    def start_file(self, filename: str, total_frames: int) -> ProgressTracker:
        """
        Start tracking progress for a specific file.
        
        Args:
            filename: Name of the file being processed
            total_frames: Total frames in the file
            
        Returns:
            ProgressTracker instance for the file
        """
        if self.current_file_tracker:
            self.current_file_tracker.close()
        
        self.current_file_tracker = ProgressTracker(
            total_frames, 
            f"Processing {filename}"
        )
        self.current_file_tracker.start()
        return self.current_file_tracker
    
    def complete_file(self) -> None:
        """Mark current file as complete and update batch progress."""
        if self.current_file_tracker:
            self.current_file_tracker.complete()
            self.current_file_tracker.close()
            self.current_file_tracker = None
        
        if self.file_progress_bar:
            self.current_file += 1
            self.file_progress_bar.n = self.current_file
            self.file_progress_bar.refresh()
    
    def close(self) -> None:
        """Close all progress tracking."""
        if self.current_file_tracker:
            self.current_file_tracker.close()
            self.current_file_tracker = None
        
        if self.file_progress_bar:
            self.file_progress_bar.close()
            self.file_progress_bar = None
        
        logger.debug("Batch progress tracking closed")
