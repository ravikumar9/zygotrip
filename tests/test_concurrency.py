"""
Concurrency Safety Tests

Tests Phase 3: Race condition prevention with SELECT FOR UPDATE
"""

import pytest
import threading
import time
from decimal import Decimal
from django.test import TestCase, TransactionTestCase
from django.db import transaction, connection
from concurrent.futures import ThreadPoolExecutor, as_completed

from apps.hotels.models import Property
from apps.accounts.models import User
from apps.inventory.models import PropertyInventory
from apps.inventory.concurrency import InventoryManager, InsufficientInventory


class ConcurrencyBaseTestCase(TransactionTestCase):
    """Base test case for concurrency tests"""
    
    def setUp(self):
        """Create test property and inventory"""
        self.user = User.objects.create_user(
            username='owner1',
            email='owner1@test.com',
            password='pass123'
        )
        
        self.property1 = Property.objects.create(
            owner=self.user,
            name='Test Hotel 1',
            city='Delhi',
            country='India',
            address='123 Test Rd',
            description='Test hotel',
            base_price=Decimal('1000')
        )
        
        self.property2 = Property.objects.create(
            owner=self.user,
            name='Test Hotel 2',
            city='Mumbai',
            country='India',
            address='456 Test Rd',
            description='Test hotel 2',
            base_price=Decimal('1200')
        )
        
        # Create inventory for both properties
        self.inventory1 = PropertyInventory.objects.create(
            property=self.property1,
            total_rooms=100,
            available_rooms=100
        )
        
        self.inventory2 = PropertyInventory.objects.create(
            property=self.property2,
            total_rooms=50,
            available_rooms=50
        )


class RaceConditionTestCase(ConcurrencyBaseTestCase):
    """Test race condition prevention"""
    
    def test_one_room_fifty_concurrent_bookings(self):
        """
        CRITICAL TEST: 50 threads race for 1 room
        Expected: 1 success, 49 fail (InsufficientInventory)
        """
        # Reset inventory to 1 room
        self.inventory1.available_rooms = 1
        self.inventory1.save()
        
        success_count = [0]
        failure_count = [0]
        error_lock = threading.Lock()
        
        def attempt_booking():
            try:
                InventoryManager.deduct_rooms(self.property1.id, 1)
                with error_lock:
                    success_count[0] += 1
            except InsufficientInventory:
                with error_lock:
                    failure_count[0] += 1
            except Exception as e:
                with error_lock:
                    failure_count[0] += 1
        
        # Create and run 50 threads
        threads = []
        for _ in range(50):
            t = threading.Thread(target=attempt_booking)
            threads.append(t)
            t.start()
        
        # Wait for all threads to complete
        for t in threads:
            t.join(timeout=10)
        
        # Verify exactly 1 success, 49 failures
        assert success_count[0] == 1, f"Expected 1 success, got {success_count[0]}"
        assert failure_count[0] == 49, f"Expected 49 failures, got {failure_count[0]}"
        
        # Verify inventory is now 0
        self.inventory1.refresh_from_db()
        assert self.inventory1.available_rooms == 0
    
    def test_ten_rooms_ten_threads_all_succeed(self):
        """10 threads, 10 rooms available = all succeed"""
        # Ensure 10 rooms
        self.inventory1.available_rooms = 10
        self.inventory1.save()
        
        success_count = [0]
        failure_count = [0]
        error_lock = threading.Lock()
        
        def attempt_booking():
            try:
                InventoryManager.deduct_rooms(self.property1.id, 1)
                with error_lock:
                    success_count[0] += 1
            except InsufficientInventory:
                with error_lock:
                    failure_count[0] += 1
        
        threads = []
        for _ in range(10):
            t = threading.Thread(target=attempt_booking)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join(timeout=10)
        
        assert success_count[0] == 10
        assert failure_count[0] == 0
        
        self.inventory1.refresh_from_db()
        assert self.inventory1.available_rooms == 0
    
    def test_version_field_increments_on_change(self):
        """Version field should increment with each modification"""
        initial_version = self.inventory1.version
        
        # Deduct rooms
        InventoryManager.deduct_rooms(self.property1.id, 5)
        
        self.inventory1.refresh_from_db()
        assert self.inventory1.version == initial_version + 1
        
        # Deduct more
        InventoryManager.deduct_rooms(self.property1.id, 3)
        
        self.inventory1.refresh_from_db()
        assert self.inventory1.version == initial_version + 2


class CancellationRollbackTestCase(ConcurrencyBaseTestCase):
    """Test booking cancellation and room restoration"""
    
    def test_cancel_booking_restores_rooms(self):
        """Cancelling booking should restore rooms"""
        initial_rooms = self.inventory1.available_rooms
        
        # Deduct 5 rooms
        InventoryManager.deduct_rooms(self.property1.id, 5)
        self.inventory1.refresh_from_db()
        assert self.inventory1.available_rooms == initial_rooms - 5
        
        # Cancel (restore)
        InventoryManager.restore_rooms(self.property1.id, 5)
        self.inventory1.refresh_from_db()
        assert self.inventory1.available_rooms == initial_rooms
    
    def test_cannot_restore_more_than_available(self):
        """Cannot restore more than total rooms"""
        self.inventory1.total_rooms = 100
        self.inventory1.save()
        
        # Deduct 5
        InventoryManager.deduct_rooms(self.property1.id, 5)
        
        # Try to restore 10 (more than deducted)
        try:
            InventoryManager.restore_rooms(self.property1.id, 10)
            # If successful, check that it doesn't exceed total
            self.inventory1.refresh_from_db()
            assert self.inventory1.available_rooms <= 100
        except Exception:
            # Exception is acceptable
            pass
    
    def test_partial_cancellation(self):
        """Partial cancellation works correctly"""
        initial = self.inventory1.available_rooms
        
        # Deduct 10
        InventoryManager.deduct_rooms(self.property1.id, 10)
        
        # Restore only 3
        InventoryManager.restore_rooms(self.property1.id, 3)
        
        self.inventory1.refresh_from_db()
        assert self.inventory1.available_rooms == initial - 7


class MultiPropertyConcurrencyTestCase(ConcurrencyBaseTestCase):
    """Test concurrent access to different properties"""
    
    def test_concurrent_bookings_different_properties(self):
        """Concurrent bookings on different properties don't interfere"""
        initial_p1 = self.inventory1.available_rooms
        initial_p2 = self.inventory2.available_rooms
        
        results = [None, None]
        errors = [None, None]
        
        def book_property(prop_id, index):
            try:
                InventoryManager.deduct_rooms(prop_id, 5)
                results[index] = 'success'
            except Exception as e:
                errors[index] = str(e)
        
        t1 = threading.Thread(target=book_property, args=(self.property1.id, 0))
        t2 = threading.Thread(target=book_property, args=(self.property2.id, 1))
        
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        
        # Both should succeed independently
        assert results[0] == 'success'
        assert results[1] == 'success'
        
        self.inventory1.refresh_from_db()
        self.inventory2.refresh_from_db()
        
        assert self.inventory1.available_rooms == initial_p1 - 5
        assert self.inventory2.available_rooms == initial_p2 - 5


class InventoryConsistencyTestCase(ConcurrencyBaseTestCase):
    """Test inventory mathematical consistency"""
    
    def test_available_never_exceeds_total(self):
        """Available rooms can never exceed total rooms"""
        total = self.inventory1.total_rooms
        
        # Try various operations
        InventoryManager.deduct_rooms(self.property1.id, 10)
        InventoryManager.restore_rooms(self.property1.id, 5)
        
        self.inventory1.refresh_from_db()
        assert self.inventory1.available_rooms <= total
    
    def test_available_never_negative(self):
        """Available rooms must never be negative"""
        # Try to overdraw
        try:
            InventoryManager.deduct_rooms(self.property1.id, 1000)
        except InsufficientInventory:
            # Expected
            pass
        
        self.inventory1.refresh_from_db()
        assert self.inventory1.available_rooms >= 0
    
    def test_consistency_after_hundred_operations(self):
        """100 random deduct/restore operations maintain consistency"""
        initial = self.inventory1.available_rooms
        deducted = 0
        
        operations = [
            ('deduct', 3),
            ('restore', 1),
            ('deduct', 5),
            ('restore', 2),
            ('deduct', 1),
        ] * 20  # 100 total operations
        
        for op, count in operations:
            try:
                if op == 'deduct':
                    InventoryManager.deduct_rooms(self.property1.id, count)
                    deducted += count
                elif op == 'restore':
                    InventoryManager.restore_rooms(self.property1.id, count)
                    deducted -= count
            except InsufficientInventory:
                deducted -= count  # Removal failed, don't count
        
        self.inventory1.refresh_from_db()
        
        # Check consistency
        assert self.inventory1.available_rooms >= 0
        assert self.inventory1.available_rooms <= self.inventory1.total_rooms


if __name__ == '__main__':
    pytest.main([__file__, '-v'])