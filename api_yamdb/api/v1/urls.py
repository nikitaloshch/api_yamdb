from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .views import (
    CommentViewSet, get_token, ReviewViewSet, sign_up, UserViewSet
)

router = DefaultRouter()
router.register("users", UserViewSet)
router.register(r'titles/(?P<title_id>\d+)/reviews', ReviewViewSet)
router.register(
    r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
    CommentViewSet
)


urlpatterns = [
    path("", include(router.urls)),
    path("auth/signup/", sign_up),
    path("auth/token/", get_token),
]
