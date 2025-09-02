"""Tests for the CLI dump command."""

import json
import io
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path

import pytest
from click.testing import CliRunner

from cosmic_ray.cli import dump
from cosmic_ray.work_db import WorkDB, use_db
from cosmic_ray.work_item import MutationSpec, WorkItem, WorkResult, WorkerOutcome


@pytest.fixture
def mock_db_with_no_test_outcome():
    """Create a mock database with a work item that has a NO_TEST worker outcome and None test_outcome."""
    # Create a work item with a mutation
    item = WorkItem.single("job_id", MutationSpec("path", "operator", 0, (0, 0), (0, 1)))

    # Create a result with NO_TEST worker outcome and None test_outcome
    result = WorkResult(worker_outcome=WorkerOutcome.NO_TEST, output="No test was run", test_outcome=None, diff=None)

    # Create a mock database
    mock_db = MagicMock()
    mock_db.completed_work_items = [(item, result)]
    mock_db.pending_work_items = []

    return mock_db


def test_dump_handles_none_test_outcome(mock_db_with_no_test_outcome):
    """Test that the dump command correctly handles None test_outcome values."""
    runner = CliRunner()

    # Create a temporary session file path
    session_file = "test_session.sqlite"

    # Mock the use_db context manager to return our mock database
    with patch("cosmic_ray.cli.use_db") as mock_use_db:
        # Configure the mock to return our mock database when used as a context manager
        mock_use_db.return_value.__enter__.return_value = mock_db_with_no_test_outcome

        # Run the CLI command
        result = runner.invoke(dump, [session_file])

        # Check that the command executed successfully
        assert result.exit_code == 0

        # Parse the output as JSON
        output_line = result.output.strip()
        parsed_output = json.loads(output_line)

        # Verify the result has the correct structure
        assert len(parsed_output) == 2  # Should be a tuple of [work_item, result]
        result_dict = parsed_output[1]

        # Check that worker_outcome is correctly serialized
        assert result_dict["worker_outcome"] == "no-test"

        # Check that test_outcome is None
        assert result_dict["test_outcome"] is None
