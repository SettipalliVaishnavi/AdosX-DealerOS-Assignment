import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.asgi import get_asgi_application

application = get_asgi_application()

from django.core.management import call_command
from reconcile.models import Location

try:
    call_command("migrate", interactive=False, verbosity=0)

    if not Location.objects.exists():
        call_command("import_data", verbosity=1)

except Exception as error:
    print(f"Database initialization error: {error}")
    raise
