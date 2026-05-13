"""Integration test for multi-tool pipeline.

Tests a chain of tool operations: read → edit → write → search verification.
"""

import os
import tempfile

import pytest

from src.tools.read import read_file
from src.tools.write import write_file
from src.tools.edit import edit_file
from src.tools.grep import grep_search


class TestToolPipeline:
    """Integration tests for tool composition."""

    def test_read_edit_read_workflow(self):
        """Read a file, edit it, and verify the change."""
        # Create a temporary file
        content = "def hello():\n    print('hello')\n\ndef world():\n    print('world')\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            tmp_path = f.name

        try:
            # Read the file
            result = read_file(tmp_path)
            assert "def hello()" in result

            # Edit the file
            edit_result = edit_file(
                tmp_path,
                old_string="print('hello')",
                new_string="print('Hello, World!')",
            )
            assert "Edited" in edit_result

            # Read again to verify
            result2 = read_file(tmp_path)
            assert "print('Hello, World!')" in result2
            assert "print('hello')" not in result2
        finally:
            os.unlink(tmp_path)

    def test_write_and_search_workflow(self):
        """Write a file, then search for its content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test_search.py")

            # Write file
            write_result = write_file(file_path, "# TODO: add auth\n# FIXME: broken\nprint('ok')\n")
            assert "Created" in write_result or "Updated" in write_result

            # Search for TODO
            search_result = grep_search("TODO", path_str=tmpdir)
            assert "TODO" in search_result
            assert "test_search.py" in search_result
