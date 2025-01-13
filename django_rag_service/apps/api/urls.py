from django.urls import include, path

urlpatterns = [
    path('v1/', include('apps.api.v1.urls')),

    # Default API Version
    path('', include('apps.api.v1.urls')),
]
