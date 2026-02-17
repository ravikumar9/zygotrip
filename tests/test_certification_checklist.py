"""
Production Certification Checklist Tests
"""

import threading
import time
from decimal import Decimal
from datetime import timedelta

import pytest
from django.test import TestCase, TransactionTestCase
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.core.cache import cache
from django.core.exceptions import ValidationError

from accounts.models import User
from hotels.models import Property
from rooms.models import RoomType, RoomInventory
from inventory.models import SupplierPropertyMap, PropertyInventory, PriceHistory
from inventory.matching_engine import match_supplier_property
from pricing.core_engine import UnifiedPricingEngine
from security.pricing_guard import PricingGuard, FraudDetection, RateLimitExceeded
from core.validators import InputValidator
from core.models import OperationLog
from core.observability import PerformanceLog
from booking.services import create_booking


class DataIntegrityCertificationTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='owner@test.com',
            full_name='Owner',
            password='pass123'
        )
        self.property = Property.objects.create(
            owner=self.user,
            name='Test Hotel',
            city='Delhi',
            country='India',
            address='123 Test Rd',
            description='Test',
            latitude=28.6139,
            longitude=77.2090,
        )

    def test_duplicate_supplier_mapping_db_constraint(self):
        SupplierPropertyMap.objects.create(
            property=self.property,
            supplier_name='booking',
            external_id='dup_001',
            supplier_property_name='Test Hotel',
            supplier_city='Delhi',
            confidence_score=0.9,
            verified=True,
        )
        with pytest.raises(IntegrityError):
            SupplierPropertyMap.objects.create(
                property=self.property,
                supplier_name='booking',
                external_id='dup_001',
                supplier_property_name='Test Hotel Copy',
                supplier_city='Delhi',
                confidence_score=0.9,
                verified=True,
            )

    def test_foreign_key_enforced(self):
        with pytest.raises(IntegrityError):
            SupplierPropertyMap.objects.create(
                property_id=999999,
                supplier_name='booking',
                external_id='fk_001',
                supplier_property_name='No Property',
                supplier_city='Delhi',
                confidence_score=0.9,
                verified=True,
            )

    def test_not_null_enforced(self):
        with pytest.raises(IntegrityError):
            SupplierPropertyMap.objects.create(
                property=self.property,
                supplier_name=None,
                external_id='null_001',
                supplier_property_name='Null Supplier',
                supplier_city='Delhi',
                confidence_score=0.9,
                verified=True,
            )

    def test_price_precision_rounding(self):
        entry = PriceHistory.objects.create(
            property=self.property,
            base_price=Decimal('100.12345'),
            final_price=Decimal('200.98765'),
            demand_score=60,
            price_change_percent=5.0,
        )
        entry.refresh_from_db()
        assert entry.base_price == Decimal('100.12')
        assert entry.final_price == Decimal('200.99')


class DeterministicPricingCertificationTestCase(TestCase):
    def test_same_inputs_1000_times(self):
        engine = UnifiedPricingEngine()
        results = set()
        for _ in range(1000):
            result = engine.calculate_price(
                base_price=Decimal('1000'),
                demand_score=75,
                competitor_price=Decimal('950')
            )
            results.add(result['final_price'])
        assert len(results) == 1


class ConcurrencySafetyCertificationTestCase(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='owner2@test.com',
            full_name='Owner Two',
            password='pass123'
        )
        self.property = Property.objects.create(
            owner=self.user,
            name='Concurrency Hotel',
            city='Delhi',
            country='India',
            address='456 Test Rd',
            description='Test',
        )
        self.inventory = PropertyInventory.objects.create(
            property=self.property,
            total_rooms=1,
            available_rooms=1,
        )

    def test_200_threads_booking_last_room(self):
        success = [0]
        failures = [0]
        lock = threading.Lock()

        def attempt():
            from inventory.concurrency import InventoryManager, InsufficientInventory
            try:
                InventoryManager.deduct_rooms(self.property.id, 1)
                with lock:
                    success[0] += 1
            except InsufficientInventory:
                with lock:
                    failures[0] += 1

        threads = [threading.Thread(target=attempt) for _ in range(200)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert success[0] == 1
        assert failures[0] == 199

    def test_transaction_rollback_consistency(self):
        self.inventory.available_rooms = 5
        self.inventory.save()

        try:
            with transaction.atomic():
                inv = PropertyInventory.objects.select_for_update().get(property=self.property)
                inv.available_rooms = 0
                inv.save(update_fields=['available_rooms'])
                raise RuntimeError('simulate crash')
        except RuntimeError:
            pass

        self.inventory.refresh_from_db()
        assert self.inventory.available_rooms == 5


class MappingAccuracyCertificationTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='owner3@test.com',
            full_name='Owner Three',
            password='pass123'
        )
        self.property = Property.objects.create(
            owner=self.user,
            name='Royal Suites',
            city='Delhi',
            country='India',
            address='789 Test Rd',
            description='Test',
        )

    def test_similar_names_same_city_not_auto_map(self):
        matched, confidence, status = match_supplier_property(
            supplier_name='booking',
            external_id='sim_001',
            supplier_property_name='Royal Suite',
            supplier_city='Delhi',
            supplier_lat=None,
            supplier_lng=None,
        )
        assert status != 'approved'

    def test_same_name_different_city_rejects(self):
        matched, confidence, status = match_supplier_property(
            supplier_name='booking',
            external_id='city_001',
            supplier_property_name='Royal Suites',
            supplier_city='Mumbai',
            supplier_lat=None,
            supplier_lng=None,
        )
        assert matched is None
        assert 'No properties found' in status


class FraudResistanceCertificationTestCase(TestCase):
    def setUp(self):
        cache.clear()

    def test_supplier_100_updates_sec_blocked(self):
        with pytest.raises(RateLimitExceeded):
            for _ in range(100):
                PricingGuard.check_update_rate('booking', 'sup_001', client_ip='1.2.3.4')

    def test_gradual_price_drop_detected(self):
        price = Decimal('1000')
        with pytest.raises(FraudDetection):
            for _ in range(100):
                new_price = price * Decimal('0.99')
                PricingGuard.check_price_change(1, new_price, price)
                price = new_price


class InputValidationCertificationTestCase(TestCase):
    def test_currency_mismatch_rejected(self):
        with pytest.raises(ValidationError):
            InputValidator.validate_currency('USD')

    def test_missing_field_rejected(self):
        payload = {'price': 100}
        with pytest.raises(ValidationError):
            InputValidator.validate_schema(payload, {'price': int, 'currency': str})

    def test_timezone_normalization(self):
        naive = timezone.now().replace(tzinfo=None)
        normalized = InputValidator.normalize_timezone(naive)
        assert timezone.is_aware(normalized)


class ObservabilityCertificationTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='owner4@test.com',
            full_name='Owner Four',
            password='pass123'
        )
        self.property = Property.objects.create(
            owner=self.user,
            name='Audit Hotel',
            city='Delhi',
            country='India',
            address='101 Test Rd',
            description='Test',
        )

    def test_price_calc_logged(self):
        engine = UnifiedPricingEngine()
        engine.calculate_price(base_price=Decimal('1000'))
        assert OperationLog.objects.filter(operation_type='price_calculated').exists()
        assert PerformanceLog.objects.filter(operation_type='price_calculation').exists()

    def test_mapping_logged(self):
        match_supplier_property(
            supplier_name='booking',
            external_id='audit_001',
            supplier_property_name='Audit Hotel',
            supplier_city='Delhi',
        )
        assert OperationLog.objects.filter(operation_type='mapping_decision').exists()

    def test_booking_failure_logged(self):
        room_type = RoomType.objects.create(
            property=self.property,
            name='Standard',
            description='Test room',
            base_price=Decimal('1000'),
            max_guests=2,
        )
        RoomInventory.objects.create(
            room_type=room_type,
            date=timezone.localdate(),
            available_count=1,
        )
        with pytest.raises(ValueError):
            create_booking(
                user=self.user,
                property_obj=self.property,
                room_type=room_type,
                quantity=1,
                meal_plan=None,
                check_in=timezone.localdate(),
                check_out=timezone.localdate(),
                guests=[{'full_name': 'Test', 'age': 30, 'email': 't@test.com'}],
            )
        assert OperationLog.objects.filter(operation_type='booking_failed').exists()


class DisasterSafetyCertificationTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='owner5@test.com',
            full_name='Owner Five',
            password='pass123'
        )
        self.property = Property.objects.create(
            owner=self.user,
            name='Idempotent Hotel',
            city='Delhi',
            country='India',
            address='999 Test Rd',
            description='Test',
        )
        self.room_type = RoomType.objects.create(
            property=self.property,
            name='Standard',
            description='Test room',
            base_price=Decimal('1000'),
            max_guests=2,
        )
        RoomInventory.objects.create(
            room_type=self.room_type,
            date=timezone.localdate() + timedelta(days=1),
            available_count=2,
        )

    def test_idempotency_replay_creates_one_booking(self):
        idempotency_key = 'idem-001'
        booking1 = create_booking(
            user=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            quantity=1,
            meal_plan=None,
            check_in=timezone.localdate() + timedelta(days=1),
            check_out=timezone.localdate() + timedelta(days=2),
            guests=[{'full_name': 'Test', 'age': 30, 'email': 't@test.com'}],
            idempotency_key=idempotency_key,
        )
        booking2 = create_booking(
            user=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            quantity=1,
            meal_plan=None,
            check_in=timezone.localdate() + timedelta(days=1),
            check_out=timezone.localdate() + timedelta(days=2),
            guests=[{'full_name': 'Test', 'age': 30, 'email': 't@test.com'}],
            idempotency_key=idempotency_key,
        )
        assert booking1.id == booking2.id
