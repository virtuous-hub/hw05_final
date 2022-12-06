import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms

from ..models import Follow, Group, Post
from ..global_constants import LIM_POSTS_PAGE

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Длинный тестовый пост',
            group=cls.group,
            image=cls.uploaded
        )
        cls.post_2 = Post.objects.create(
            author=cls.user,
            text='Длинный тестовый пост',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_name = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:profile', kwargs={'username': self.user.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}
            ): 'posts/create_post.html',
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
        }
        for reverse_name, template in templates_pages_name.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_show_correct_context(self):
        """Шаблоны сформированы с правильным контекстом. """
        reverse_names = {
            reverse('posts:index'),
            reverse('posts:profile',
                    kwargs={'username': self.user.username}),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
        }
        for reverse_name in reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                first_object = response.context['page_obj'][0]
                self.assertEqual(first_object.author.username, 'auth')
                self.assertEqual(first_object.text, 'Длинный тестовый пост')
                self.assertTrue(response.context['post'].image)

    def test_group_list_show_correct_posts_len(self):
        """В группе показаывается верное кол-во постов"""
        response = self.guest_client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug}
        ))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.group.title, 'Тестовая группа')
        self.assertEqual(first_object.group.slug, 'test-slug')
        self.assertEqual(
            first_object.group.description, 'Тестовое описание')
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_profile_show_correct_posts_len(self):
        """В profile показывается верное кол-во постов"""
        response = self.authorized_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.user.username}
        ))
        self.assertEqual(len(response.context['page_obj']), 2)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        post_page = reverse(
            'posts:post_detail', kwargs={'post_id': PostPagesTests.post.id})
        response = (self.authorized_client.get(post_page))
        detail_object = response.context['post']
        post_author = detail_object.author.username
        post_text = detail_object.text
        post_group = detail_object.group.title
        self.assertEqual(post_author, 'auth')
        self.assertEqual(post_group, 'Тестовая группа')
        self.assertEqual(post_text, 'Длинный тестовый пост')
        self.assertTrue(response.context['post'].image)
        self.assertEqual(
            response.context.get('post').id, PostPagesTests.post.id)

    def test_create_and_edit_post_show_correct_context(self):
        """Проверка форм редактирования и создания поста"""
        post_page = {
            reverse(
                'posts:post_edit', kwargs={'post_id': PostPagesTests.post.id}),
            reverse('posts:post_create'),
        }
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        for page in post_page:
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    response = (self.authorized_client.get(page))
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_post_add_show_correct(self):
        """Проверяем, пост добавлен на страницы"""
        post = Post.objects.create(
            text='Текст',
            author=self.user,
            group=self.group
        )
        templates_pages_name = [
            self.authorized_client.get(reverse('posts:index')),
            self.authorized_client.get(reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            )),
            self.authorized_client.get(reverse(
                'posts:profile', kwargs={'username': self.user.username}
            ))
        ]
        for i in templates_pages_name:
            self.assertIn(post, i.context['page_obj'])


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание',
        )
        bilk_post: list = []
        for i in range(1, 14):
            bilk_post.append(Post(text=f'Длинный тестовый пост {i}',
                                  group=cls.group,
                                  author=cls.user))
        Post.objects.bulk_create(bilk_post)

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_paginator(self):
        """Проверяем, что паджинатор работает корректно"""
        test_posts = {
            reverse('posts:index'): LIM_POSTS_PAGE,
            reverse('posts:index') + '?page=2': 3,
            reverse('posts:profile',
                    kwargs={'username': self.user.username}): LIM_POSTS_PAGE,
            reverse('posts:profile',
                    kwargs={'username': self.user.username}) + '?page=2': 3,
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}): LIM_POSTS_PAGE,
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}) + '?page=2': 3
        }
        for reverse_name, posts in test_posts.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), posts)


class CacheViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test-author')
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.author
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_cache_for_index_page(self):
        """Проверка добавления и очищения кэша для index"""
        response_one = self.authorized_client.get(reverse('posts:index'))
        response_two = self.authorized_client.get(
            reverse('posts:index')
        )
        page = response_one.content
        old_page = response_two.content
        Post.objects.create(
            text='Еще тестовый пост',
            author=CacheViewsTest.author,
        )
        self.assertEqual(old_page, page)
        cache.clear()
        response_new = self.authorized_client.get(reverse('posts:index'))
        new_page = response_new.content
        self.assertNotEqual(old_page, new_page)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Test_Leo')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.authorized_user = User.objects.create_user(username='Auth-User')
        cls.client_user = Client()
        cls.client_user.force_login(cls.authorized_user)
        cls.guest_client = Client()
        cls.post = Post.objects.create(
            text='Тестовый пост для follow',
            author=cls.author,
        )

    def test_guest_client_and_author_for_follow(self):
        """Неавторизованный пользователь и автор не могут подписаться"""
        followers = Follow.objects.count()
        reverse_names = {
            self.author_client.get(reverse(
                'posts:profile_follow',
                kwargs={'username': self.author.username}
            )),
            self.guest_client.get(reverse(
                'posts:profile_follow',
                kwargs={'username': self.author.username}
            ))
        }
        for value in reverse_names:
            with self.subTest(value=value):
                self.assertNotEqual(Follow.objects.count(), followers + 1)

    def test_for_follow_myself(self):
        """Пользователь не сможет подписаться на автора, если уже подписан"""
        client = self.client_user
        user = self.authorized_user
        author = self.author
        client.get(reverse(
            'posts:profile_follow', kwargs={'username': self.author.username}))
        followers = Follow.objects.count()
        follower = Follow.objects.filter(
            user=user,
            author=author
        ).exists()
        self.assertTrue(follower)
        client.get(reverse(
            'posts:profile_follow', kwargs={'username': self.author.username}))
        self.assertNotEqual(Follow.objects.count(), followers + 1)

    def test_follow_and_unfollow(self):
        """Авторизир. пользователь может подписаться и отписаться от автора"""
        client = self.client_user
        user = self.authorized_user
        author = self.author
        client.get(reverse(
            'posts:profile_follow', kwargs={'username': self.author.username}))
        follower = Follow.objects.filter(
            user=user,
            author=author
        ).exists()
        self.assertTrue(follower)
        client.get(reverse(
            'posts:profile_unfollow', kwargs={'username': self.author.username}
        ))
        follower = Follow.objects.filter(
            user=user,
            author=author
        ).exists()
        self.assertFalse(follower)

    def test_new_post_for_followers(self):
        """Новая запись появляется в ленте подписчиков"""
        client = self.client_user
        author = self.author
        client.get(reverse(
            'posts:profile_follow', kwargs={'username': self.author.username}))
        response = client.get(reverse(
            'posts:follow_index'
        ))
        posts_list_one = response.context.get('page_obj')
        new_post = Post.objects.create(
            text='пост для follow',
            author=author
        )
        response_new = client.get(reverse(
            'posts:follow_index'
        ))
        posts_list_two = response_new.context.get('page_obj')
        self.assertEqual(len(response.context.get('page_obj')), 1)
        self.assertIn(self.post, posts_list_one)
        self.assertEqual(len(response_new.context.get('page_obj')), 2)
        self.assertIn(new_post, posts_list_two)

    def test_new_post_for_unfollower(self):
        """Новая запись не появится в ленте не подписанных пользователей"""
        client = self.client_user
        author = self.author
        response = client.get(reverse(
            'posts:follow_index'
        ))
        posts_list = response.context.get('page_obj')
        self.assertEqual(len(response.context.get('page_obj')), 0)
        self.assertNotIn(FollowViewsTest.post, posts_list)
        new_post = Post.objects.create(
            text='Новый пост для follow',
            author=author
        )
        response_new = client.get(reverse('posts:follow_index'))
        new_posts_list = response_new.context.get('page_obj')
        self.assertEqual(len(response_new.context.get('page_obj')), 0)
        self.assertNotIn(new_post, new_posts_list)
