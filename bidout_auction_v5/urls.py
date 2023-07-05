from django.contrib import admin
from django.http import JsonResponse
from django.urls import path
from apps.api import api


def handler404(request, exception=None):
    response = JsonResponse({"status": "failure", "message": "Not Found"})
    response.status_code = 404
    return response


def handler500(request, exception=None):
    response = JsonResponse({"status": "failure", "message": "Server Error"})
    response.status_code = 500
    return response


handler404 = handler404
handler500 = handler500

urlpatterns = [path("admin/", admin.site.urls), path("", api.urls)]
