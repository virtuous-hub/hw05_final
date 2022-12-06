from .core.models import CreatedModel
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.constraints import UniqueConstraint

from .global_constants import LIM_STR


User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200, verbose_name='Группа')
    slug = models.SlugField(unique=True)
    description = models.TextField(verbose_name='Описание')

    def __str__(self):
        return self.title


class Post(CreatedModel):
    text = models.TextField(verbose_name='Текст поста')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор',
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='group_list',
        verbose_name='Имя группы',
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True,
        null=True
    )

    class Meta:
        ordering = ("-created",)

    def __str__(self):
        return self.text[:LIM_STR]


class Comment(CreatedModel):
    post = models.ForeignKey(
        Post,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ("-created",)

    def __str__(self):
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )

    class Meta:
        UniqueConstraint(fields=['user', 'author'], name='unique_follower')
