from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from post.models import Post, Vote, Bookmark
from django.db.models import OuterRef, Subquery, CharField, Value, Count, Q
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator

from django.shortcuts import render, redirect, get_object_or_404

def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("/accounts/login")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})


def viewProfile(request, profileId):
    profileUser = get_object_or_404(
        User.objects.annotate(
            post_count=Count("post", distinct=True),  # số post của user
            vote_count=Count("post__votes", distinct=True),  # tổng vote (up + down)
            bookmark_count=Count("post__bookmarks", distinct=True)  # tổng bookmark
        ),
        id=profileId
    )

    # profileUser.email = "223791873128739128379128371298379223791873128739128379128371222379187312873912837912837129837922379187312873912837912837129837922379187312873912837912837129837998379223791873128739128379128371298379"

    if (profileUser.email is not None) and (len(profileUser.email) > 110):
        profileUser.email = profileUser.email[:(110 - 3)] + "..."

    return render(request, "account.html", {
        "profileUser": profileUser,
    })


# def accountsList(request):
#     if request.user.is_authenticated:
#         users=User.objects.all().order_by('-date_joined')
#         return render(request ,"accountsList.html", {"users": users})
#     else:
#         return redirect("/")

def accountsList(request):
    if not request.user.is_authenticated:
        return redirect("/")
    
    max_len_of_username01 = 130

    users = User.objects.all().order_by('-date_joined')

    # Annotate thêm dữ liệu
    users = users.annotate(
        post_count=Count("post", distinct=True),  # số post của user
        vote_count=Count("post__votes", distinct=True),  # tổng vote (up + down)
        like_count=Count("post__votes", filter=Q(post__votes__voteType="up"), distinct=True),  # tổng like
        dislike_count=Count("post__votes", filter=Q(post__votes__voteType="down"), distinct=True),  # tổng dislike
        bookmark_count=Count("post__bookmarks", distinct=True)  # tổng bookmark
    )

    # Phân trang (10 user/trang)
    paginator = Paginator(users, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    for user in page_obj:
        if len(user.username) > max_len_of_username01:
            user.username = user.username[:(max_len_of_username01 - 3)] + "..."


    return render(request, "accountsList.html", {
        "users": page_obj.object_list,
        "page_obj": page_obj,
    })