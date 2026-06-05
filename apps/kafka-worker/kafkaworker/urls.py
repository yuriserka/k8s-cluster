"""
URL configuration for kafkaworker project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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

from django.contrib import admin
from django.urls import path, include
from kafkaworker.containers.api.views.hello_world import hello_world_view
from kafkaworker.containers.api.views.fetch_image import fetch_image_view
from kafkaworker.containers.api.views.update_event import update_event_view

urlpatterns = [
    path("", include("django_prometheus.urls")),
    path("admin/", admin.site.urls),
    path("hello-world", hello_world_view),
    path("fetch-image", fetch_image_view),
    path("update-event/<str:event_id>", update_event_view),
]
