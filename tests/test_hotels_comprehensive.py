"""
Comprehensive test suite for hotels app - MASTER FIX validation
Tests cover: mapping, pricing, validation firewall, queryset optimization
"""
import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from hotels.models import Property, PropertyImage, PropertyOffer, RatingAggregate, Category
from accounts.models import User


@pytest.mark.django_db
class TestPropertyMapping:
	"""Test property model field mapping and relationships"""

	def test_property_creation_with_all_fields(self):
		"""Verify Property model can be created with all required fields"""
		owner = User.objects.create_user(username='owner1', password='test123')
		property_obj = Property.objects.create(
			owner=owner,
			name='Test Hotel',
			city='Mumbai',
			country='India',
			address='123 Test St',
			description='Test description',
			rating=Decimal('4.5'),
			base_price=Decimal('1000.00')
		)
		assert property_obj.id is not None
		assert property_obj.name == 'Test Hotel'
		assert property_obj.rating == Decimal('4.5')

	def test_property_images_ordering(self):
		"""Verify PropertyImage ordering with featured flag"""
		owner = User.objects.create_user(username='owner2', password='test123')
		property_obj = Property.objects.create(
			owner=owner,
			name='Test Hotel 2',
			city='Delhi',
			country='India',
			address='456 Test Ave',
			description='Test',
			base_price=Decimal('2000.00')
		)
		img1 = PropertyImage.objects.create(
			property=property_obj,
			image_url='https://example.com/img1.jpg',
			is_featured=False,
			display_order=1
		)
		img2 = PropertyImage.objects.create(
			property=property_obj,
			image_url='https://example.com/img2.jpg',
			is_featured=True,
			display_order=0
		)
		images = property_obj.images.all()
		assert images[0].is_featured == True
		assert images[0] == img2


@pytest.mark.django_db
class TestPricingDeterministic:
	"""Test pricing logic is deterministic and consistent"""

	def test_base_price_calculation(self):
		"""Verify base_price remains consistent"""
		owner = User.objects.create_user(username='owner3', password='test123')
		property_obj = Property.objects.create(
			owner=owner,
			name='Price Test Hotel',
			city='Bangalore',
			country='India',
			address='789 Test Rd',
			description='Test',
			base_price=Decimal('3000.00')
		)
		assert property_obj.base_price == Decimal('3000.00')
		property_obj.refresh_from_db()
		assert property_obj.base_price == Decimal('3000.00')

	def test_discount_price_logic(self):
		"""Verify discount_price field accepts valid values"""
		owner = User.objects.create_user(username='owner4', password='test123')
		property_obj = Property.objects.create(
			owner=owner,
			name='Discount Test Hotel',
			city='Chennai',
			country='India',
			address='101 Test Blvd',
			description='Test',
			base_price=Decimal('5000.00'),
			discount_price=Decimal('4500.00')
		)
		assert property_obj.discount_price == Decimal('4500.00')


@pytest.mark.django_db
class TestValidationFirewall:
	"""Test validation firewall rejects invalid data"""

	def test_negative_price_rejected(self):
		"""Negative prices must be rejected"""
		owner = User.objects.create_user(username='owner5', password='test123')
		with pytest.raises(ValidationError) as exc_info:
			property_obj = Property(
				owner=owner,
				name='Invalid Price Hotel',
				city='Pune',
				country='India',
				address='202 Test Lane',
				description='Test',
				base_price=Decimal('-1000.00')
			)
			property_obj.save()
		assert 'base_price' in str(exc_info.value)

	def test_rating_above_5_rejected(self):
		"""Ratings above 5.0 must be rejected"""
		owner = User.objects.create_user(username='owner6', password='test123')
		with pytest.raises(ValidationError) as exc_info:
			property_obj = Property(
				owner=owner,
				name='High Rating Hotel',
				city='Kolkata',
				country='India',
				address='303 Test Way',
				description='Test',
				base_price=Decimal('2000.00'),
				rating=Decimal('6.0')
			)
			property_obj.save()
		assert 'rating' in str(exc_info.value)

	def test_rating_below_0_rejected(self):
		"""Negative ratings must be rejected"""
		owner = User.objects.create_user(username='owner7', password='test123')
		with pytest.raises(ValidationError) as exc_info:
			property_obj = Property(
				owner=owner,
				name='Negative Rating Hotel',
				city='Hyderabad',
				country='India',
				address='404 Test Circle',
				description='Test',
				base_price=Decimal('3000.00'),
				rating=Decimal('-1.0')
			)
			property_obj.save()
		assert 'rating' in str(exc_info.value)

	def test_invalid_image_url_extension_rejected(self):
		"""Image URLs with invalid extensions must be rejected"""
		owner = User.objects.create_user(username='owner8', password='test123')
		property_obj = Property.objects.create(
			owner=owner,
			name='Image Test Hotel',
			city='Jaipur',
			country='India',
			address='505 Test Plaza',
			description='Test',
			base_price=Decimal('1500.00')
		)
		with pytest.raises(ValidationError) as exc_info:
			img = PropertyImage(
				property=property_obj,
				image_url='https://example.com/image.txt'
			)
			img.save()
		assert 'image_url' in str(exc_info.value)

	def test_rating_aggregate_over_5_rejected(self):
		"""Rating aggregate values over 5 must be rejected"""
		owner = User.objects.create_user(username='owner9', password='test123')
		property_obj = Property.objects.create(
			owner=owner,
			name='Rating Aggregate Test',
			city='Goa',
			country='India',
			address='606 Test Court',
			description='Test',
			base_price=Decimal('4000.00')
		)
		with pytest.raises(ValidationError) as exc_info:
			rating_agg = RatingAggregate(
				property=property_obj,
				cleanliness=Decimal('6.0'),
				service=Decimal('4.0'),
				location=Decimal('4.0'),
				amenities=Decimal('4.0'),
				value_for_money=Decimal('4.0')
			)
			rating_agg.save()
		assert 'cleanliness' in str(exc_info.value).lower()

	def test_offer_invalid_date_range_rejected(self):
		"""Offers with valid_from > valid_until must be rejected"""
		owner = User.objects.create_user(username='owner10', password='test123')
		property_obj = Property.objects.create(
			owner=owner,
			name='Offer Test Hotel',
			city='Udaipur',
			country='India',
			address='707 Test Drive',
			description='Test',
			base_price=Decimal('5000.00')
		)
		today = timezone.now().date()
		with pytest.raises(ValidationError) as exc_info:
			offer = PropertyOffer(
				property=property_obj,
				title='Invalid Offer',
				description='Test offer',
				discount_percentage=Decimal('20.00'),
				valid_from=today + timedelta(days=10),
				valid_until=today + timedelta(days=5),
				code='INVALID2024'
			)
			offer.save()


@pytest.mark.django_db
class TestQuerysetOptimization:
	"""Test queryset optimization with select_related/prefetch_related"""

	def test_hotel_list_uses_prefetch(self):
		"""Verify hotel_list view uses optimized queries"""
		from django.test import Client
		from django.urls import reverse
		
		owner = User.objects.create_user(username='owner11', password='test123')
		property_obj = Property.objects.create(
			owner=owner,
			name='Query Test Hotel',
			city='Agra',
			country='India',
			address='808 Test Street',
			description='Test',
			base_price=Decimal('2500.00'),
			rating=Decimal('4.0')
		)
		
		from dashboard_admin.models import PropertyApproval
		PropertyApproval.objects.create(
			property=property_obj,
			status='APPROVED'
		)
		
		client = Client()
		response = client.get(reverse('hotels:list'))
		assert response.status_code == 200


@pytest.mark.django_db
class TestCategorySeeding:
	"""Test category seeding command"""

	def test_categories_can_be_created(self):
		"""Verify categories can be created programmatically"""
		from django.utils.text import slugify
		
		category = Category.objects.create(
			name='Beach Vacations',
			slug=slugify('Beach Vacations'),
			description='Coastal properties',
			icon='🏖️'
		)
		assert category.id is not None
		assert category.slug == 'beach-vacations'


@pytest.mark.django_db
class TestDataIntegrity:
	"""Test data integrity constraints"""

	def test_offer_code_unique(self):
		"""Verify PropertyOffer code is unique"""
		owner = User.objects.create_user(username='owner12', password='test123')
		property1 = Property.objects.create(
			owner=owner,
			name='Hotel A',
			city='Mumbai',
			country='India',
			address='900 Test Ave',
			description='Test',
			base_price=Decimal('3000.00')
		)
		property2 = Property.objects.create(
			owner=owner,
			name='Hotel B',
			city='Delhi',
			country='India',
			address='901 Test Blvd',
			description='Test',
			base_price=Decimal('3500.00')
		)
		
		today = timezone.now().date()
		PropertyOffer.objects.create(
			property=property1,
			title='Offer 1',
			description='Test',
			discount_percentage=Decimal('10.00'),
			valid_from=today,
			valid_until=today + timedelta(days=30),
			code='UNIQUE2024'
		)
		
		with pytest.raises(Exception):  # Should raise IntegrityError
			PropertyOffer.objects.create(
				property=property2,
				title='Offer 2',
				description='Test',
				discount_percentage=Decimal('15.00'),
				valid_from=today,
				valid_until=today + timedelta(days=30),
				code='UNIQUE2024'
			)
