import re
import uuid

from django.shortcuts import get_object_or_404
from django.db.models import Avg
from rest_framework import serializers

from reviews.models import Comment, CHOICES, Review, User, Category, Genre, Title


class ErrorMessage:
    BAD_NAME = "This name cannot be used"
    NO_EMAIL = "Enter email"
    NO_USERNAME = "Enter username"
    NO_CODE = "Enter confirmation code"
    USERNAME_NOT_UNIQUE = "Username is not unique"
    EMAIL_NOT_UNIQUE = "Email is not unique"


class SignUpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(max_length=150)

    def validate_email(self, name):
        if len(name) > 254:
            raise serializers.ValidationError(ErrorMessage.BAD_NAME)
        return name

    def validate_username(self, name):
        if name == "me" or not re.match(r"^[\w.@+-]+\Z", name):
            raise serializers.ValidationError(ErrorMessage.BAD_NAME)
        return name

    def validate(self, data):
        username = data.get("username")
        email = data.get("email")
        if (
            User.objects.filter(username=username).exists()
            and User.objects.get(username=username).email != email
        ):
            raise serializers.ValidationError(ErrorMessage.USERNAME_NOT_UNIQUE)
        if (
            User.objects.filter(email=email).exists()
            and User.objects.get(email=email).username != username
        ):
            raise serializers.ValidationError(ErrorMessage.EMAIL_NOT_UNIQUE)
        return data


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

    def validate_email(self, email):
        if not email:
            raise serializers.ValidationError(ErrorMessage.NO_EMAIL)
        return email


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

    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ('title',)

    def validate_review(self, data):
        request = self.context['request']
        title_id = self.kwargs.get("title_id")
        title = get_object_or_404(Title, pk=title_id)
        if Review.objects.filter(title=title, author=request.user).exists():
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

    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ('review',)
