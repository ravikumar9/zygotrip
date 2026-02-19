from django.db import migrations, models


class Migration(migrations.Migration):

	dependencies = [
		("hotels", "0003_category_alter_propertyamenity_options_and_more"),
	]

	operations = [
		migrations.AddField(
			model_name="property",
			name="slug",
			field=models.SlugField(blank=True, null=True, unique=True),
		),
		migrations.AddField(
			model_name="property",
			name="property_type",
			field=models.CharField(default="Hotel", max_length=80),
		),
		migrations.AddField(
			model_name="property",
			name="area",
			field=models.CharField(blank=True, max_length=120),
		),
		migrations.AddField(
			model_name="property",
			name="landmark",
			field=models.CharField(blank=True, max_length=120),
		),
	]
