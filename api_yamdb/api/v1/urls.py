from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .views import (
    CommentViewSet,
    get_token,
    ReviewViewSet,
    sign_up,
    UserViewSet,
    CategoryViewSet,
    GenreViewSet,
    TitleViewSet,
)

router = DefaultRouter()
router.register("users", UserViewSet)
router.register('categories', CategoryViewSet)
router.register('genres', GenreViewSet)
router.register('titles', TitleViewSet)
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
