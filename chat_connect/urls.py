"""
URL configuration for chat_connect project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import path, include

from apps.chat.sitemaps import ChatStaticViewSitemap
from chat_connect.views import health_check, robots_txt, multilingual_sitemap

sitemaps = {
    "chat": ChatStaticViewSitemap(),
}

urlpatterns = [
    path("sitemap.xml", multilingual_sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
    path("robots.txt", robots_txt, name="robots_txt"),
    path("health/", health_check),
]

urlpatterns += i18n_patterns(
    path("chatea-admin/", admin.site.urls),
    path("", include("apps.chat.urls")),
)

if settings.DEBUG:
    # Used for auto reload CSS and HTML
    urlpatterns += (path("__reload__/", include("django_browser_reload.urls")),)
