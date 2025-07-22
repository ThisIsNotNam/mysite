from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.postsList),
    path("new/", views.newPost),
    path("<int:postId>/", views.postsDetail),
    path("<int:postId>/delete/", views.deletePost),
    path("vote/", views.votePost, name='votePost'),
]