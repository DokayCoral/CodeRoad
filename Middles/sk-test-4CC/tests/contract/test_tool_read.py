"""Contract tests for the Read tool."""

import os
import tempfile

import pytest

from src.tools.read import read_file


class TestReadTool:
    """Contract tests for read_file function."""

    def test_reads_existing_file(self):
        """Read an existing file returns content with line numbers."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("line one\nline two\nline three\n")
            tmp_path = f.name

        try:
            result = read_file(tmp_path)
            assert "line one" in result
            assert "1\tline one" in result
            assert "2\tline two" in result
            assert "3\tline three" in result
        finally:
            os.unlink(tmp_path)

    def test_file_not_found(self):
        """Non-existent file returns error."""
        result = read_file("/nonexistent/path/file.txt")
        assert result.startswith("[ERROR]")
        assert "File not found" in result

    def test_offset_and_limit(self):
        """Offset and limit control which lines are returned."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("\n".join(str(i) for i in range(1, 11)) + "\n")
            tmp_path = f.name

        try:
            result = read_file(tmp_path, offset=3, limit=2)
            assert "4\t4" in result
            assert "5\t5" in result
            assert "3\t3" not in result
        finally:
            os.unlink(tmp_path)

    def test_path_is_directory(self):
        """Reading a directory returns error."""
        result = read_file("/")
        assert result.startswith("[ERROR]")
        assert "directory" in result.lower()
