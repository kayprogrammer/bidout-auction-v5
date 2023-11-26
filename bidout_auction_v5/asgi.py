"""
ASGI config for bidout_auction_v5 project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os, sys
if os.environ.get('SETTINGS') == 'production':
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from django.core.asgi import get_asgi_application
from decouple import config

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    f"bidout_auction_v5.settings.{config('SETTINGS')}",
)

application = get_asgi_application()
app = application