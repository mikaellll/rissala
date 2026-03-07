"""
URL configuration for shamela_ia_wrapper project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    # i18n switcher
    path("i18n/", include("django.conf.urls.i18n")),
]

urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("accounts/", include("apps.accounts.urls", namespace="accounts")),
    path("search/", include("apps.search.urls", namespace="search")),
    path("ai/", include("apps.ai_engine.urls", namespace="ai")),
    path("", include("apps.core.urls", namespace="core")),
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
