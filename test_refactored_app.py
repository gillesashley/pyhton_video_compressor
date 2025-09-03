#!/usr/bin/env python3
"""
Basic tests for the refactored video compression application.
This script tests that all modules can be imported and basic functionality works.
"""

import sys
import os

def test_imports():
    """Test that all modules can be imported successfully."""
    print("Testing module imports...")
    
    try:
        import main
        print("✓ main.py imported successfully")
    except Exception as e:
        print(f"✗ Failed to import main.py: {e}")
        return False
    
    try:
        from cli import VideoCompressionCLI, CLIError
        print("✓ cli.py imported successfully")
    except Exception as e:
        print(f"✗ Failed to import cli.py: {e}")
        return False
    
    try:
        from video_processor import VideoProcessor, VideoProcessingError
        print("✓ video_processor.py imported successfully")
    except Exception as e:
        print(f"✗ Failed to import video_processor.py: {e}")
        return False
    
    try:
        from compression_settings import CompressionSettings
        print("✓ compression_settings.py imported successfully")
    except Exception as e:
        print(f"✗ Failed to import compression_settings.py: {e}")
        return False
    
    try:
        from progress_tracker import ProgressTracker, BatchProgressTracker
        print("✓ progress_tracker.py imported successfully")
    except Exception as e:
        print(f"✗ Failed to import progress_tracker.py: {e}")
        return False
    
    try:
        from file_utils import FileUtils
        print("✓ file_utils.py imported successfully")
    except Exception as e:
        print(f"✗ Failed to import file_utils.py: {e}")
        return False
    
    return True

def test_file_utils():
    """Test file utility functions."""
    print("\nTesting file utilities...")
    
    from file_utils import FileUtils
    
    # Test size parsing
    try:
        assert FileUtils.parse_size_string("50MB") == 50.0
        assert FileUtils.parse_size_string("1GB") == 1024.0
        assert FileUtils.parse_size_string("500KB") == 0.48828125
        print("✓ Size parsing works correctly")
    except Exception as e:
        print(f"✗ Size parsing failed: {e}")
        return False
    
    # Test file format validation
    try:
        assert FileUtils.is_supported_format("test.mp4") == True
        assert FileUtils.is_supported_format("test.avi") == True
        assert FileUtils.is_supported_format("test.txt") == False
        print("✓ Format validation works correctly")
    except Exception as e:
        print(f"✗ Format validation failed: {e}")
        return False
    
    # Test file size formatting
    try:
        assert "1.0 KB" in FileUtils.format_file_size(1024)
        assert "1.0 MB" in FileUtils.format_file_size(1024*1024)
        print("✓ File size formatting works correctly")
    except Exception as e:
        print(f"✗ File size formatting failed: {e}")
        return False
    
    return True

def test_compression_settings():
    """Test compression settings functionality."""
    print("\nTesting compression settings...")
    
    from compression_settings import CompressionSettings
    
    try:
        # Test quality validation
        assert CompressionSettings.validate_quality("medium") == True
        assert CompressionSettings.validate_quality("invalid") == False
        print("✓ Quality validation works correctly")
    except Exception as e:
        print(f"✗ Quality validation failed: {e}")
        return False
    
    try:
        # Test codec validation
        assert CompressionSettings.validate_codec("libx264") == True
        assert CompressionSettings.validate_codec("invalid") == False
        print("✓ Codec validation works correctly")
    except Exception as e:
        print(f"✗ Codec validation failed: {e}")
        return False
    
    try:
        # Test available options
        qualities = CompressionSettings.get_available_qualities()
        codecs = CompressionSettings.get_available_codecs()
        assert len(qualities) > 0
        assert len(codecs) > 0
        assert "medium" in qualities
        assert "libx264" in codecs
        print("✓ Available options retrieval works correctly")
    except Exception as e:
        print(f"✗ Available options retrieval failed: {e}")
        return False
    
    return True

def test_cli():
    """Test CLI functionality."""
    print("\nTesting CLI...")
    
    from cli import VideoCompressionCLI, CLIError
    
    try:
        cli = VideoCompressionCLI()
        print("✓ CLI initialization works correctly")
    except Exception as e:
        print(f"✗ CLI initialization failed: {e}")
        return False
    
    try:
        # Test argument parsing with help
        try:
            cli.parse_arguments(['--help'])
        except SystemExit:
            # Help exits with code 0, this is expected
            pass
        print("✓ Help argument parsing works correctly")
    except Exception as e:
        print(f"✗ Help argument parsing failed: {e}")
        return False
    
    return True

def test_progress_tracker():
    """Test progress tracking functionality."""
    print("\nTesting progress tracker...")
    
    from progress_tracker import ProgressTracker
    
    try:
        # Test basic progress tracker creation
        tracker = ProgressTracker(100, "Test")
        assert tracker.total_frames == 100
        assert tracker.current_frame == 0
        assert tracker.progress_percentage == 0.0
        print("✓ Progress tracker creation works correctly")
    except Exception as e:
        print(f"✗ Progress tracker creation failed: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Refactored Video Compression Application")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_file_utils,
        test_compression_settings,
        test_cli,
        test_progress_tracker
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        else:
            print(f"Test {test.__name__} failed!")
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The refactored application is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
