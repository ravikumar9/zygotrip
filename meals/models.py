from django.db import models
from core.models import TimeStampedModel
from hotels.models import Property


class MealPlan(TimeStampedModel):
	MEAL_TYPES = (
		('breakfast', 'Breakfast Only'),
		('half_board', 'Half Board (B+L or B+D)'),
		('full_board', 'Full Board (B+L+D)'),
		('all_inclusive', 'All Inclusive'),
	)
	
	property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='meal_plans')
	name = models.CharField(max_length=120)
	meal_type = models.CharField(max_length=20, choices=MEAL_TYPES, default='breakfast')
	description = models.TextField(blank=True)
	price = models.DecimalField(max_digits=10, decimal_places=2)
	icon = models.CharField(max_length=40, blank=True, help_text="Icon class or emoji")

	class Meta:
		unique_together = ('property', 'meal_type')

	def __str__(self):
		return f"{self.property.name} - {self.get_meal_type_display()}"

# Create your models here.
