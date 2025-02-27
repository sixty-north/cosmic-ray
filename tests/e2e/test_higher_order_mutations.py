"""End-to-end tests for higher-order mutations."""

import os
import pathlib
import subprocess
import sys
import tempfile

import pytest

from cosmic_ray.work_db import WorkDB, use_db
from cosmic_ray.work_item import WorkItem


@pytest.fixture(scope="session")
def higher_order_project_root():
    """Path to the higher-order test project."""
    # Use the absolute path to the project
    return pathlib.Path("/home/andre/Repos/cosmic-ray/tests/resources/higher_order_test")
    
@pytest.fixture
def session_file():
    """Create a temporary session file for each test."""
    with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as f:
        session_path = f.name
    
    try:
        yield pathlib.Path(session_path)
    finally:
        # Clean up after test
        if os.path.exists(session_path):
            os.unlink(session_path)


def test_first_order_mutations(higher_order_project_root, session_file):
    """Test that first-order mutations work correctly."""
    config = "cosmic-ray.conf"  # This has mutation-order = 1
    
    # Initialize the session
    subprocess.check_call(
        [sys.executable, "-m", "cosmic_ray.cli", "init", config, str(session_file)],
        cwd=str(higher_order_project_root),
    )
    
    # Run the mutations
    subprocess.check_call(
        [sys.executable, "-m", "cosmic_ray.cli", "exec", config, str(session_file)],
        cwd=str(higher_order_project_root),
    )
    
    # Analyze the results
    with use_db(str(session_file), WorkDB.Mode.open) as work_db:
        # Count the number of work items
        work_items = list(work_db.work_items)
        
        # Verify we only have first-order mutations (each with exactly one mutation)
        assert all(len(item.mutations) == 1 for item in work_items)
        
        # Make sure we have some mutations (at least 10)
        assert len(work_items) >= 10


@pytest.mark.slow
def test_second_order_mutations(higher_order_project_root, session_file):
    """Test that second-order mutations work correctly."""
    config = "cosmic-ray-order-2.conf"  # This has mutation-order = 2
    
    # Initialize the session
    subprocess.check_call(
        [sys.executable, "-m", "cosmic_ray.cli", "init", config, str(session_file)],
        cwd=str(higher_order_project_root),
    )
    
    # Run the mutations
    subprocess.check_call(
        [sys.executable, "-m", "cosmic_ray.cli", "exec", config, str(session_file)],
        cwd=str(higher_order_project_root),
    )
    
    # Analyze the results
    with use_db(str(session_file), WorkDB.Mode.open) as work_db:
        # Count the number of work items
        work_items = list(work_db.work_items)
        
        # Count first-order and second-order mutations
        first_order_count = sum(1 for item in work_items if len(item.mutations) == 1)
        second_order_count = sum(1 for item in work_items if len(item.mutations) == 2)
        
        # We should have both first-order and second-order mutations
        assert first_order_count > 0
        assert second_order_count > 0
        
        # Total should be first + second order
        assert len(work_items) == first_order_count + second_order_count
        
        # The combined total should be greater than just the first-order count
        # This proves we're actually generating higher-order mutants
        assert len(work_items) > first_order_count
        
@pytest.mark.slow
def test_specific_order_mutations(higher_order_project_root, session_file):
    """Test that specific-order mutations work correctly."""
    import toml
    from pathlib import Path
    
    # Create a temporary configuration file with specific-order set
    temp_config_path = Path(higher_order_project_root) / "temp-specific-order.conf"
    
    # Start with the order-2 config
    order2_config_path = Path(higher_order_project_root) / "cosmic-ray-order-2.conf"
    with open(order2_config_path) as f:
        config_data = toml.load(f)
    
    # Add specific-order = 2 to only generate second-order mutants
    config_data["cosmic-ray"]["specific-order"] = 2
    
    with open(temp_config_path, "w") as f:
        toml.dump(config_data, f)
    
    try:
        # Initialize the session
        subprocess.check_call(
            [sys.executable, "-m", "cosmic_ray.cli", "init", str(temp_config_path), str(session_file)],
            cwd=str(higher_order_project_root),
        )
        
        # Run the mutations
        subprocess.check_call(
            [sys.executable, "-m", "cosmic_ray.cli", "exec", str(temp_config_path), str(session_file)],
            cwd=str(higher_order_project_root),
        )
        
        # Analyze the results
        with use_db(str(session_file), WorkDB.Mode.open) as work_db:
            # Count the number of work items
            work_items = list(work_db.work_items)
            
            # Verify all are second-order mutations (each with exactly two mutations)
            assert all(len(item.mutations) == 2 for item in work_items)
            
            # Make sure we have some mutations
            assert len(work_items) > 0
    
    finally:
        # Clean up the temporary config file
        if temp_config_path.exists():
            temp_config_path.unlink()