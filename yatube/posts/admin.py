from django.contrib import admin

from .models import Comment, Follow, Group, Post


class PostAdmin(admin.ModelAdmin):
    list_display = ("pk", "text", "created", "author", "group",)
    search_fields = ('text', )
    list_filter = ("created",)
    empty_value_display = "-пусто-"
    list_editable = ('group',)


class GroupAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "description")
    search_fields = ("title",)
    list_filter = ("slug",)
    empty_value_display = "-пусто-"


class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'created', 'active')
    list_filter = ('active', 'created')


class FollowAdmin(admin.ModelAdmin):
    list_display = ('pk', 'author', 'user')
    search_fields = ('author__username', 'user__username')
    list_filter = ('user',)
    empty_value_display = '-пусто-'


admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Follow, FollowAdmin)
