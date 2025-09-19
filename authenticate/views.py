from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from post.models import Post, Vote
from django.db.models import OuterRef, Subquery, CharField, Value
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
    profileUser = get_object_or_404(User, id=profileId)

    # Subquery to get the current user's vote on each post
    user_vote_subquery = Vote.objects.filter(
        post=OuterRef('pk'),
        user=request.user
    ).values('voteType')[:1]

    # Annotate each post with the user's vote
    posts = Post.objects.filter(author=profileUser).order_by('-date').annotate(
        userVote=Coalesce(
            Subquery(user_vote_subquery, output_field=CharField()),
            Value('none')
        )
    )

    return render(request, "account.html", {
        "profileUser": profileUser,
        "posts": posts
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

    users = User.objects.all().order_by('-date_joined')

    # Phân trang (10 user/trang)
    paginator = Paginator(users, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "accountsList.html", {
        "users": page_obj.object_list,
        "page_obj": page_obj,
    })