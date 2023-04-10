from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import filters, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from reviews.models import Review, Comment, Category, Genre, Title
from users.models import User

from .permissions import IsAdmin, IsAuthorOrModerator, IsAdminOrReadOnly
from .filters import TitleFilter
from .mixins import GetListCreateDeleteMixin
from .serializers import (
    AuthSerializer,
    ProfileSerializer,
    SignUpSerializer,
    UserSerializer,
    CategorySerializer,
    CommentSerializer,
    GenreSerializer,
    ReviewSerializer,
    TitleRetrieveSerializer,
    TitleWriteSerializer,
)


@api_view(["POST"])
@permission_classes((AllowAny,))
def sign_up(request):
    serializer = SignUpSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    username = serializer.validated_data.get("username")
    user = User.objects.get(username=username)
    send_mail(
        subject=settings.DEFAULT_EMAIL_SUBJECT,
        message=str(user.confirmation_code),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=(user.email,),
    )
    return Response(serializer.validated_data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes((AllowAny,))
def get_token(request):
    serializer = AuthSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    username = serializer.validated_data["username"]
    user = get_object_or_404(User, username=username)

    refresh = RefreshToken.for_user(user)
    return Response(
        {"token": str(refresh.access_token)}, status=status.HTTP_200_OK
    )


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAdmin,)
    lookup_field = "username"
    filter_backends = (filters.SearchFilter,)
    search_fields = ("username",)
    http_method_names = [
        "get",
        "post",
        "patch",
        "delete",
    ]

    @action(
        methods=("get", "patch"),
        detail=False,
        url_path="me",
        permission_classes=(IsAuthenticated,),
        serializer_class=ProfileSerializer,
    )
    def set_profile(self, request, pk=None):
        user = get_object_or_404(User, pk=request.user.id)
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class CommentViewSet(viewsets.ModelViewSet):
    """Вьюсет для обьектов модели Comment."""
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = (IsAuthorOrModerator,)

    def perform_create(self, serializer):
        review_id = self.kwargs.get("review_id")
        review = get_object_or_404(Review, pk=review_id)
        serializer.save(author=self.request.user, review=review)

    def get_queryset(self):
        review_id = self.kwargs.get("review_id")
        review = get_object_or_404(Review, pk=review_id)
        return review.comments.all()


class ReviewViewSet(viewsets.ModelViewSet):
    """Вьюсет для обьектов модели Review."""
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = (IsAuthorOrModerator,)

    def perform_create(self, serializer):
        title_id = self.kwargs.get("title_id")
        title = get_object_or_404(Title, id=title_id)
        serializer.save(author=self.request.user, title=title)

    def get_queryset(self):
        title_id = self.kwargs.get("title_id")
        title = get_object_or_404(Title, id=title_id)
        return title.reviews.all()


class TitleViewSet(viewsets.ModelViewSet):
    """Вьюсет для произведения."""

    queryset = Title.objects.annotate(rating=Avg('reviews__score')).all()
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitleFilter

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return TitleRetrieveSerializer
        return TitleWriteSerializer


class CategoryViewSet(GetListCreateDeleteMixin):
    """Вьюсет для категории."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ("name",)
    lookup_field = "slug"


class GenreViewSet(GetListCreateDeleteMixin):
    """Вьюсет для жанра."""

    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ("name",)
    lookup_field = "slug"
