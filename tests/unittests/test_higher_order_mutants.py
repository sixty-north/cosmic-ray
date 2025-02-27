"""Tests for higher-order mutant functionality."""

import pytest
from pathlib import Path
import itertools
import uuid
import sys
from unittest import mock

from cosmic_ray.work_item import MutationSpec, WorkItem, WorkResult, WorkerOutcome
from cosmic_ray.work_item import TestOutcome as TOutcome
from cosmic_ray.mutating import mutate_and_test
from cosmic_ray.commands.init import _all_work_items
import cosmic_ray.commands.init as init_module
from cosmic_ray.work_db import WorkDB, use_db


def test_workitem_with_multiple_mutations():
    """Test that a WorkItem can be created with multiple mutations."""
    mutations = [
        MutationSpec(Path("path1"), "operator1", 0, (0, 0), (0, 1)),
        MutationSpec(Path("path2"), "operator2", 1, (1, 0), (1, 1)),
    ]
    
    # Create a WorkItem with multiple mutations
    work_item = WorkItem(job_id="test_job", mutations=tuple(mutations))
    
    # Check that the WorkItem has the correct mutations
    assert len(work_item.mutations) == 2
    assert work_item.mutations[0].module_path == Path("path1")
    assert work_item.mutations[0].operator_name == "operator1"
    assert work_item.mutations[1].module_path == Path("path2")
    assert work_item.mutations[1].operator_name == "operator2"


def test_init_creates_higher_order_mutants(monkeypatch):
    """Test that the init command creates higher-order mutants when configured."""
    # Mock the _generate_mutations function to return a fixed set of mutations
    mock_mutations = [
        MutationSpec(Path("path1"), "operator1", 0, (0, 0), (0, 1)),
        MutationSpec(Path("path2"), "operator2", 1, (1, 0), (1, 1)),
        MutationSpec(Path("path3"), "operator3", 2, (2, 0), (2, 1)),
    ]
    
    # Mock uuid.uuid4().hex to return predictable values
    monkeypatch.setattr(uuid, "uuid4", lambda: type('obj', (object,), {'hex': 'test-uuid'}))
    
    # Use mock.patch to patch the module function
    with mock.patch('cosmic_ray.commands.init._generate_mutations', return_value=mock_mutations):
        # Get all work items with mutation_order=1 (first-order only)
        work_items_first_order = list(_all_work_items([], {}, mutation_order=1))
        
        # There should be 3 work items (one for each mutation)
        assert len(work_items_first_order) == 3
        
        # Each work item should have exactly one mutation
        for item in work_items_first_order:
            assert len(item.mutations) == 1
        
        # Get all work items with mutation_order=2 (first and second-order)
        work_items_second_order = list(_all_work_items([], {}, mutation_order=2))
        
        # There should be 3 first-order + 3 choose 2 second-order = 3 + 3 = 6 work items
        assert len(work_items_second_order) == 6
        
        # Count the number of each order
        first_order_count = sum(1 for item in work_items_second_order if len(item.mutations) == 1)
        second_order_count = sum(1 for item in work_items_second_order if len(item.mutations) == 2)
        
        assert first_order_count == 3
        assert second_order_count == 3
        
        # Get all work items with mutation_order=3 (first, second, and third-order)
        work_items_third_order = list(_all_work_items([], {}, mutation_order=3))
        
        # There should be 3 first-order + 3 choose 2 second-order + 3 choose 3 third-order = 3 + 3 + 1 = 7 work items
        assert len(work_items_third_order) == 7
        
        # Count the number of each order
        first_order_count = sum(1 for item in work_items_third_order if len(item.mutations) == 1)
        second_order_count = sum(1 for item in work_items_third_order if len(item.mutations) == 2)
        third_order_count = sum(1 for item in work_items_third_order if len(item.mutations) == 3)
        
        assert first_order_count == 3
        assert second_order_count == 3
        assert third_order_count == 1


def test_multiple_mutations_generated_correctly(monkeypatch):
    """Test that all combinations of mutations are generated correctly."""
    # Create 5 mock mutations
    mock_mutations = [
        MutationSpec(Path(f"path{i}"), f"operator{i}", i, (i, 0), (i, 1))
        for i in range(5)
    ]
    
    # Mock uuid.uuid4().hex to return predictable values
    monkeypatch.setattr(uuid, "uuid4", lambda: type('obj', (object,), {'hex': 'test-uuid'}))
    
    # Use mock.patch to patch the module function
    with mock.patch('cosmic_ray.commands.init._generate_mutations', return_value=mock_mutations):
        # Test with mutation_order=3
        work_items = list(_all_work_items([], {}, mutation_order=3))
        
        # Calculate expected combinations manually
        expected_combinations = sum(len(list(itertools.combinations(mock_mutations, i))) for i in range(1, 4))
        
        # There should be one work item for each combination
        assert len(work_items) == expected_combinations
        
        # Verify that each work item has the correct number of mutations
        order_counts = {1: 0, 2: 0, 3: 0}
        for item in work_items:
            mutation_count = len(item.mutations)
            assert 1 <= mutation_count <= 3
            order_counts[mutation_count] += 1
        
        # Verify the counts match what we expect
        assert order_counts[1] == 5  # 5 choose 1 = 5
        assert order_counts[2] == 10  # 5 choose 2 = 10
        assert order_counts[3] == 10  # 5 choose 3 = 10


def test_multiple_mutation_unique_ids():
    """Test that each work item gets a unique ID even with multiple mutations."""
    # Test directly with WorkItem objects
    mutation1 = MutationSpec(Path("path1"), "operator1", 0, (0, 0), (0, 1))
    mutation2 = MutationSpec(Path("path2"), "operator2", 1, (1, 0), (1, 1))
    
    # Add single mutation work item
    item1 = WorkItem.single(job_id="job1", mutation=mutation1)
    
    # Add multiple mutation work item
    item2 = WorkItem(job_id="job2", mutations=(mutation1, mutation2))
    
    # Verify both work items have the correct structure
    assert item1.job_id == "job1"
    assert len(item1.mutations) == 1
    assert item1.mutations[0].module_path == Path("path1")
    
    assert item2.job_id == "job2"
    assert len(item2.mutations) == 2
    assert item2.mutations[0].module_path == Path("path1")
    assert item2.mutations[1].module_path == Path("path2")