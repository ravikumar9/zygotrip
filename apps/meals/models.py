from django.db import models


class MealPlan(models.Model):
    """Stub MealPlan model for booking forms."""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    meal_type = models.CharField(max_length=50, blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        app_label = 'meals'

    def __str__(self):
        return self.name