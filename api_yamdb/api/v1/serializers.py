import re
import uuid

from django.db.models import Avg
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from reviews.models import (
    Category, Comment, Genre, Review, Title)
from users.models import User, CHOICES


class ErrorMessage:
    BAD_NAME = "This name cannot be used"
    NO_EMAIL = "Enter email"
    NO_USERNAME = "Enter username"
    NO_CODE = "Enter confirmation code"
    USERNAME_NOT_UNIQUE = "Username is not unique"
    EMAIL_NOT_UNIQUE = "Email is not unique"
    CONF_CODE_NOT_MATCH = "Confirmation code doesnt match the user"


class SignUpSerializer(serializers.ModelSerializer):
    def validate_username(self, name):
        if name == "me" or not re.match(r"^[\w.@+-]+\Z", name):
            raise serializers.ValidationError(ErrorMessage.BAD_NAME)
        return name

    def is_valid(self, *, raise_exception=False):
        if hasattr(self, 'initial_data'):
            username = self.initial_data.get("username")
            email = self.initial_data.get("email")
            if User.objects.filter(username=username, email=email).exists():
                self._validated_data = self.get_initial()
                self._errors = {}
                return True
        return super().is_valid(raise_exception)

    def create(self, validated_data):
        username = validated_data.get("username")
        email = validated_data.get("email")
        if User.objects.filter(username=username, email=email).exists():
            return User.objects.get(**validated_data)
        confirmation_code = uuid.uuid3(uuid.NAMESPACE_X500, email)
        return User.objects.create(
            **validated_data,
            confirmation_code=confirmation_code
        )

    class Meta:
        model = User
        fields = ["email", "username", ]


class AuthSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    confirmation_code = serializers.CharField(max_length=255)

    def validate(self, data):
        username = data.get("username")
        confirmation_code = data.get("confirmation_code")
        if not username:
            raise serializers.ValidationError(ErrorMessage.NO_USERNAME)
        if not confirmation_code:
            raise serializers.ValidationError(ErrorMessage.NO_CODE)

        user = get_object_or_404(User, username=username)
        if confirmation_code != user.confirmation_code:
            raise serializers.ValidationError(ErrorMessage.CONF_CODE_NOT_MATCH)
        return data


class UserSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=CHOICES, default="user")

    class Meta:
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "bio",
            "role",
        )
        model = User

    def create(self, validated_data):
        email = validated_data["email"]
        confirmation_code = str(uuid.uuid3(uuid.NAMESPACE_X500, email))
        return User.objects.create(
            **validated_data, confirmation_code=confirmation_code
        )

    def validate_username(self, name):
        if name == "me":
            raise serializers.ValidationError(ErrorMessage.BAD_NAME)
        if not name:
            raise serializers.ValidationError(ErrorMessage.NO_USERNAME)
        return name


class ProfileSerializer(UserSerializer):
    role = serializers.CharField(read_only=True)


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("name", "slug")
        model = Genre
        lookup_field = "slug"


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("name", "slug")
        model = Category
        lookup_field = "slug"


class TitleRetrieveSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    genre = GenreSerializer(read_only=True, many=True)
    rating = serializers.SerializerMethodField(read_only=True)

    class Meta:
        fields = "__all__"
        model = Title

    def get_rating(self, obj):
        obj = obj.reviews.all().aggregate(rating=Avg("score"))
        return obj["rating"]


class TitleWriteSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(), slug_field="slug"
    )
    genre = serializers.SlugRelatedField(
        queryset=Genre.objects.all(), slug_field="slug", many=True
    )

    class Meta:
        fields = ("id", "name", "description", "year", "category", "genre")
        model = Title


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only='True',
        default=serializers.CurrentUserDefault(),
    )
    title = serializers.SlugRelatedField(
        slug_field='name',
        read_only=True
    )

    class Meta:
        model = Review
        fields = '__all__'

    def validate(self, data):
        request = self.context['request']
        title_id = self.context['view'].kwargs.get('title_id')
        if request.method == 'POST':
            if Review.objects.filter(
                title__id=title_id, author=request.user
            ).exists():
                raise serializers.ValidationError(
                    "Нельзя добавить больше 1 комментария"
                )
        return data


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only='True',
        default=serializers.CurrentUserDefault(),
    )
    review = serializers.SlugRelatedField(
        read_only=True,
        slug_field='text'
    )

    class Meta:
        model = Comment
        fields = '__all__'
