"""
ASGI-конфигурация проекта Quizsite.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Quizsite.settings')

application = get_asgi_application()
