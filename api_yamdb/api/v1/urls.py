from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .views import UserViewSet, get_token, sign_up

router = DefaultRouter()
router.register("users", UserViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("auth/signup/", sign_up),
    path("auth/token/", get_token),
]
