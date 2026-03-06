import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shamela_ia_wrapper.settings")
application = get_wsgi_application()
