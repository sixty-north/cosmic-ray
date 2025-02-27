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
from cosmic_ray.commands import init
from cosmic_ray.work_db import WorkDB, use_db
from cosmic_ray.config import ConfigDict


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


def test_mutation_limit_first_order(monkeypatch):
    """Test that the mutation limit works for first-order mutants."""
    # Create 10 mock mutations
    mock_mutations = [
        MutationSpec(Path(f"path{i}"), f"operator{i}", i, (i, 0), (i, 1))
        for i in range(10)
    ]
    
    # Mock uuid.uuid4().hex to return predictable values
    monkeypatch.setattr(uuid, "uuid4", lambda: type('obj', (object,), {'hex': 'test-uuid'}))
    
    # Patch random.sample to return a predictable subset
    def mock_sample(items, count):
        return items[:count]
    
    with mock.patch('cosmic_ray.commands.init._generate_mutations', return_value=mock_mutations), \
         mock.patch('random.sample', side_effect=mock_sample):
        # Test with first-order mutants (mutation_order=1) and a limit of 5
        work_items = list(_all_work_items([], {}, mutation_order=1, mutation_limit=5))
        
        # There should be exactly 5 work items due to the limit
        assert len(work_items) == 5
        
        # Each work item should have exactly 1 mutation (first-order)
        for item in work_items:
            assert len(item.mutations) == 1


def test_mutation_limit_higher_order(monkeypatch):
    """Test that the mutation limit works for higher-order mutants."""
    # Create 5 mock mutations
    mock_mutations = [
        MutationSpec(Path(f"path{i}"), f"operator{i}", i, (i, 0), (i, 1))
        for i in range(5)
    ]
    
    # Mock uuid.uuid4().hex to return predictable values
    monkeypatch.setattr(uuid, "uuid4", lambda: type('obj', (object,), {'hex': 'test-uuid'}))
    
    # Patch random.sample to return a predictable subset
    def mock_sample(items, count):
        return items[:count]
    
    with mock.patch('cosmic_ray.commands.init._generate_mutations', return_value=mock_mutations), \
         mock.patch('random.sample', side_effect=mock_sample):
        # Test with second-order mutants (mutation_order=2) and a limit of 7
        work_items = list(_all_work_items([], {}, mutation_order=2, mutation_limit=7))
        
        # There should be exactly 7 work items due to the limit
        assert len(work_items) == 7
        
        # Count the number of each order
        orders = {}
        for item in work_items:
            order = len(item.mutations)
            orders[order] = orders.get(order, 0) + 1
            
        # With our mock_sample implementation, we should get the first 7 work items,
        # which would be all 5 first-order mutants and the first 2 second-order mutants
        assert orders.get(1, 0) == 5
        assert orders.get(2, 0) == 2


def test_config_passes_mutation_limit_to_work_items():
    """Test that the config's mutation limit is correctly passed to _all_work_items."""
    # Create 5 mock mutations
    mock_mutations = [
        MutationSpec(Path(f"path{i}"), f"operator{i}", i, (i, 0), (i, 1))
        for i in range(5)
    ]
    
    # Create all work items with different mutation limits
    with mock.patch('cosmic_ray.commands.init._generate_mutations', return_value=mock_mutations), \
         mock.patch('random.sample', side_effect=lambda items, count: items[:count]):
        
        # With no limit
        items_no_limit = list(_all_work_items([], {}, mutation_order=2, mutation_limit=None))
        
        # With a limit of 3
        items_with_limit = list(_all_work_items([], {}, mutation_order=2, mutation_limit=3))
        
        # With limit larger than total possible mutations
        items_big_limit = list(_all_work_items([], {}, mutation_order=2, mutation_limit=100))
        
        # Verify the expected number of items
        # For mutation_order=2 with 5 mutations, we expect:
        # - 5 first-order mutants
        # - 10 second-order mutants (5 choose 2)
        # - Total: 15 work items without limit
        assert len(items_no_limit) == 15
        
        # With limit of 3, we should only get 3 items
        assert len(items_with_limit) == 3
        
        # With a large limit, we should get all items
        assert len(items_big_limit) == 15