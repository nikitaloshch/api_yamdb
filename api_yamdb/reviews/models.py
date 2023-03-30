from datetime import datetime

from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator
from django.db import models

ADMIN = 'admin'
MODERATOR = 'moderator'
USER = 'user'

CHOICES = (
    (ADMIN, ADMIN),
    (MODERATOR, MODERATOR),
    (USER, USER),
)


class User(AbstractUser):
    first_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(
        'email',
        unique=True,
        max_length=254
    )
    bio = models.TextField(
        'Биография',
        blank=True,
        null=True,
    )
    role = models.CharField(
        'Статус пользователя',
        max_length=20,
        choices=CHOICES,
        default=USER
    )
    confirmation_code = models.CharField(max_length=255)

    @property
    def is_admin(self):
        return self.is_superuser or self.is_staff or (self.role == ADMIN)

    @property
    def is_moderator(self):
        return self.role == MODERATOR

    def __str__(self):
        return self.username

    class Meta:
        ordering = ['username', ]


class Category(models.Model):
    name = models.CharField(max_length=256)
    slug = models.SlugField(max_length=50, unique=True)

    class Meta:
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.slug


class Genre(models.Model):
    name = models.CharField(max_length=256)
    slug = models.SlugField(max_length=50, unique=True)

    class Meta:
        verbose_name_plural = "Жанры"

    def __str__(self):
        return self.slug


class Title(models.Model):
    name = models.CharField(max_length=256)
    year = models.IntegerField(
        blank=True,
        validators=[MaxValueValidator(int(datetime.now().year))],
    )
    description = models.TextField(blank=True)
    genre = models.ManyToManyField(
        Genre,
        related_name="titles",
    )
    category = models.ForeignKey(
        Category,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="titles",
    )

    class Meta:
        verbose_name_plural = "Произведения"

    def __str__(self):
        return self.name
