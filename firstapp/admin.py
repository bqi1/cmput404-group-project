from django.contrib import admin
from .models import Author, Setting, PublicImage, Post, Comment, Node, Like, Inbox



class PostSearch(admin.ModelAdmin):
    search_fields = ('user_id',)

    def get_search_results(self,request,queryset,search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        try:
            user_id = Author.objects.get(username=search_term).consistent_id
            queryset = Post.objects.filter(user_id=user_id)
        except Author.DoesNotExist:
            queryset = Author.objects.none()
        return queryset,use_distinct


# Register your models here.
admin.site.register(Author)
admin.site.register(Setting)
admin.site.register(PublicImage)
admin.site.register(Post,PostSearch)
admin.site.register(Comment)
admin.site.register(Node)
admin.site.register(Like)
admin.site.register(Inbox)