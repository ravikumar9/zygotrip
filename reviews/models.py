from django.db import models
from core.models import TimeStampedModel
from accounts.models import User
from hotels.models import Property


class Review(TimeStampedModel):
	STATUS_PENDING = 'pending'
	STATUS_APPROVED = 'approved'
	STATUS_REJECTED = 'rejected'
	
	STATUS_CHOICES = [
		(STATUS_PENDING, 'Pending Review'),
		(STATUS_APPROVED, 'Approved'),
		(STATUS_REJECTED, 'Rejected'),
	]
	
	property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='reviews')
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_written')
	rating = models.PositiveIntegerField(default=5, choices=[(i, f'{i} Star{"s" if i != 1 else ""}') for i in range(1, 6)])
	title = models.CharField(max_length=150, blank=True)
	comment = models.TextField()
	image_url = models.URLField(blank=True)
	image_file = models.ImageField(upload_to='reviews/', null=True, blank=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
	is_verified_booking = models.BooleanField(default=False)
	
	class Meta:
		ordering = ['-created_at']
		unique_together = ('property', 'user')

	def __str__(self):
		return f'{self.user.email} - {self.property.name} ({self.rating}⭐)'

# Create your models here.
