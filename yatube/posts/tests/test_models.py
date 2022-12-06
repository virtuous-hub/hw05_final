from django.contrib.auth import get_user_model
from django.test import TestCase

from ..global_constants import LIM_STR
from ..forms import PostForm
from ..models import Group, Post


User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Длинный текстовый пост',
        )
        cls.form = PostForm()

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = self.group.__str__()
        post = self.post.__str__()
        expected_object_names = {
            post: self.post.text,
            group: self.group.title,
        }
        for value, objects in expected_object_names.items():
            with self.subTest(value=value):
                self.assertEqual(value, str(objects[:LIM_STR]))

    def test_verbose_name(self):
        """Проверяем verbose_name модели post"""
        self.post = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'author': 'Автор',
            'group': 'Имя группы',
        }
        for field, value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name, value)

    def test_form_help_text(self):
        """Проверяем help_text формы PostForm"""
        text_help_text = PostModelTest.form.fields['text'].help_text
        group_help_text = PostModelTest.form.fields['group'].help_text
        help_texts = {
            text_help_text: 'Введите текст поста',
            group_help_text: 'Выберите группу'
        }
        for field, value in help_texts.items():
            with self.subTest(value=value):
                self.assertTrue(field, value)
