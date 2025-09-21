from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.postsList),
    path("new/", views.newPost),
    path("<int:postId>/", views.postsDetail),
    path("<int:postId>/edit/", views.postEdit),
    path("<int:postId>/delete/", views.deletePost),
    path("<int:postId>/edit/", views.editPost),
    path("vote/", views.votePost, name='votePost'),
    path("bookmark/", views.bookmarkPost, name="bookmarkPost"),
    path("bookmarksview/", views.postsList, name="bookmarked_posts"),
]