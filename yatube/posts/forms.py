from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = [
            'text',
            'group',
            'image'
        ]
        labels = {
            "text": "Текст записи:",
            "group": "Группа"
        }
        help_texts = {
            'text': "Введите текст поста",
            'group': "Выберите группу"
        }
        Widget = {
            'text': forms.Textarea(
                attrs={
                    'class': 'form-input',
                }
            ),
            'group': forms.ChoiceField(
                required=False,
            ),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = {
            'text'
        }
        labels = {
            "text": "Ваш комментарий:"
        }
