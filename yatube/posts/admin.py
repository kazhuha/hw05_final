from django.contrib import admin

from .models import Follow, Group, Post, Comment


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'text',
        'pub_date',
        'author',
        'group',
        'image',
    )
    list_editable = ('group', 'image',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'text',
        'created',
        'post'
    )
    search_fields = ('text',)
    list_filter = ('created',)


admin.site.register(Post, PostAdmin)
admin.site.register(Group)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Follow)
