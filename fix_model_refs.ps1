$apps = @(
"dashboard_owner","dashboard_admin","dashboard_finance"
)

foreach ($app in $apps) {

$path = "apps/$app"

New-Item -ItemType Directory -Path $path -Force | Out-Null
New-Item "$path/__init__.py" -Force | Out-Null
New-Item "$path/models.py" -Force | Out-Null
New-Item "$path/views.py" -Force | Out-Null
New-Item "$path/admin.py" -Force | Out-Null

@"
from django.apps import AppConfig

class $(($app.Substring(0,1).ToUpper()+$app.Substring(1)))Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.$app'
"@ | Set-Content "$path/apps.py"

}
