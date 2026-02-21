import os

apps = ["hotels","cabs","buses","packages","search","owners"]

template = """
from django.apps import AppConfig

class {name}Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.{lower}"
    label = "{lower}"
"""

for app in apps:
    path = f"apps/{app}/apps.py"
    if not os.path.exists(path):
        with open(path,"w") as f:
            f.write(template.format(name=app.capitalize(),lower=app))
        print("created",path)