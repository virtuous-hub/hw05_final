from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from http import HTTPStatus

from ..models import Group, Post

User = get_user_model()


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Длинный тестовый пост'
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_static_page_for_anonymous_guest(self):
        """Страницы доступны неавторизированным клиентам"""
        pages: tuple = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse(
                'posts:profile', kwargs={'username': self.user.username}
            ),
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}),
        )
        for address in pages:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

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
            '/unexisting_page/': 'core/404.html'
        }
        for reverse_name, template in templates_pages_name.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_urls_redirect_guest_client(self):
        """Неавторизованный пользователь не может создавать и править посты"""
        url1 = reverse('users:login') + '?next=' + reverse('posts:post_create')
        url2 = reverse('users:login') + '?next=' + reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id})
        pages = {
            reverse('posts:post_create'): url1,
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}): url2
        }
        for page, value in pages.items():
            response = self.guest_client.get(page)
            self.assertRedirects(response, value)

    def test_404(self):
        """Неизвестная страница получает статус 404"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
