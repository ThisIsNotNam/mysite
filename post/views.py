from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.db.models import OuterRef, Subquery, Q, Count, CharField, Value, BooleanField, Exists
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator
import json
from datetime import timedelta
from django.utils import timezone
from . import forms
from .models import Post, Vote, Bookmark

def deletePost(request, postId):
    if request.method=='POST':
        if request.user.is_authenticated:
            post=get_object_or_404(Post, id=postId)
            if request.user==post.author or request.user.is_staff:
                post.delete()
        else:
            return render(request, "permissionDenied.html", {'action': 'not-logged-in'})
        next=request.POST.get("next", "/posts/")
        return redirect(next)
    post=get_object_or_404(Post, id=postId)
    return render(request, "permissionDenied.html", {'post': post, 'action': 'delete'})

def editPost(request, postId):
    if not request.user.is_authenticated:
        return render(request, "permissionDenied.html", {'action': 'not-logged-in'})

    post = get_object_or_404(Post, id=postId)

    if request.user != post.author and not request.user.is_staff:
        return render(request, "permissionDenied.html", {'post': post, 'action': 'edit'})
    
    if request.method == 'POST':
        form = forms.postCreationForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect(f"/posts/{postId}/")
    else:
        form = forms.postCreationForm(instance=post)

    return render(request, "editPost.html", {'form': form, 'post': post})

def postsList(request):
    if not request.user.is_authenticated:
        return redirect("/")

    user_posts_id = request.GET.get("user")
    user_status_post_show = "0"
    user_name_post_show = ""
    canShowAll = False  # default
    maxLen01 = 16

    if user_posts_id is not None:
        try:
            selected_user = User.objects.get(id=int(user_posts_id))
            postsQuery = Post.objects.filter(author=selected_user)
            user_name_post_show = selected_user.username
            user_status_post_show = "1"
            canShowAll = False  # khi có user thì bỏ qua show_all
        except (User.DoesNotExist, ValueError):
            postsQuery = Post.objects.none()
            user_name_post_show = ""
            user_status_post_show = "2"
            canShowAll = False
    else:
        canShowAll = request.GET.get("show_all") == "1"
        postsQuery = Post.objects.all() if canShowAll else Post.objects.filter(author=request.user)

    if len(user_name_post_show) > maxLen01:
        maxLen01 = (maxLen01 - len("..")) // 2
        user_name_post_show = user_name_post_show[:(maxLen01)] + ".." + user_name_post_show[-(maxLen01):]

    # Subquery to get user's vote
    user_vote_subquery = Vote.objects.filter(
        post=OuterRef('pk'),
        user=request.user
    ).values('voteType')[:1]

    # subquery để lấy user bookmark
    user_bookmark_subquery = Bookmark.objects.filter(
        post=OuterRef("pk"),
        user=request.user
    )

    # Annotate
    postsQuery = postsQuery.annotate(
        upvotes=Count('votes', filter=Q(votes__voteType='up'), distinct=True),
        downvotes=Count('votes', filter=Q(votes__voteType='down'), distinct=True),
        userVote=Subquery(user_vote_subquery, output_field=CharField()),
        bookmarkscount=Count('bookmarks', distinct=True),  # số lượng bookmark
        userBookmarked=Exists(user_bookmark_subquery)  # True/False
    )

    selectedSortOption = ( request.POST.get('selectedSortOption') or request.GET.get('sS') ) or 'time'
    selectedFilterOption = ( request.POST.get('selectedFilterOption') or request.GET.get('sF')) or 'all'

    # Sort
    if request.method == 'POST' or request.method == 'GET':
        if selectedSortOption == 'upVote':
            postsQuery = postsQuery.order_by('-upvotes', 'downvotes')
        elif selectedSortOption == 'downVote':
            postsQuery = postsQuery.order_by('-downvotes', 'upvotes')
        else:
            postsQuery = postsQuery.order_by('-date')

        # Filter
        if selectedFilterOption == 'day':
            postsQuery = postsQuery.filter(date__gte=timezone.now() - timedelta(days=1))
        elif selectedFilterOption == 'week':
            postsQuery = postsQuery.filter(date__gte=timezone.now() - timedelta(weeks=1))
        elif selectedFilterOption == 'month':
            postsQuery = postsQuery.filter(date__gte=timezone.now() - timedelta(days=30))
    else:
        postsQuery = postsQuery.order_by('-date')

    paginator = Paginator(postsQuery, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "postsList.html", {
        'page_obj': page_obj,   # dùng page_obj thay vì posts
        'canShowAll': canShowAll,
        'selectedSortOption': selectedSortOption,
        'selectedFilterOption': selectedFilterOption,
        'userIdPostShow': user_posts_id,
        'userStatusPostShow': user_status_post_show,
        'userNamePostShow': user_name_post_show
    })

@login_required
def bookmarked_posts(request):
    if not request.user.is_authenticated:
        return redirect("/")
    
    user_posts_id = request.GET.get("user")
    user_status_post_show = "0"
    user_name_post_show = ""
    maxLen01 = 16

    if user_posts_id is not None:
        try:
            selected_user = User.objects.get(id=int(user_posts_id))
            bookmarks = Bookmark.objects.filter(
                user=request.user,
                post__author=selected_user
            ).select_related("post")
            user_name_post_show = selected_user.username
            user_status_post_show = "1"
        except (User.DoesNotExist, ValueError):
            bookmarks = Bookmark.objects.none().select_related("post")
            user_name_post_show = ""
            user_status_post_show = "2"
    else:
        bookmarks = Bookmark.objects.filter(user=request.user).select_related("post")

    if len(user_name_post_show) > maxLen01:
        maxLen01 = (maxLen01 - len("..")) // 2
        user_name_post_show = user_name_post_show[:(maxLen01)] + ".." + user_name_post_show[-(maxLen01):]

    # Subquery to get user's vote (the related post id is post__pk, not pk of Bookmark)
    user_vote_subquery = Vote.objects.filter(
        post=OuterRef('post__pk'),
        user=request.user
    ).values('voteType')[:1]

    # Subquery để lấy user bookmark (cũng dựa trên post__pk)
    user_bookmark_subquery = Bookmark.objects.filter(
        post=OuterRef("post__pk"),
        user=request.user
    )

    bookmarks = bookmarks.annotate(
        upvotes=Count("post__votes", filter=Q(post__votes__voteType="up"), distinct=True),
        downvotes=Count("post__votes", filter=Q(post__votes__voteType="down"), distinct=True),
        userVote=Subquery(user_vote_subquery, output_field=CharField()),
        bookmarkscount=Count("post__bookmarks", distinct=True),
        userBookmarked=Exists(user_bookmark_subquery)
    )

    bookmarks = bookmarks.order_by("-created_at")   # hoặc "post__date" tuỳ bạn muốn mới nhất lên đầu hay ngược lại
    # bookmarks = bookmarks.order_by("post__id")    # nếu muốn giữ nguyên thứ tự id tăng dần

    paginator = Paginator(bookmarks, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "bookmarkedPosts.html", {
        "page_obj": page_obj,
        'userIdPostShow': user_posts_id,
        'userStatusPostShow': user_status_post_show,
        'userNamePostShow': user_name_post_show
    })

def newPost(request):
    if request.user.is_authenticated:
        if request.method=='POST':
            form=forms.postCreationForm(request.POST)
            if form.is_valid():
                newPost=form.save(commit=False)
                newPost.author=request.user
                newPost.save()
                return redirect("/posts/")
        else:
            form=forms.postCreationForm
        return render(request, "newPost.html", {'form':form})
    else:
        return redirect("/")

def votePost(request):
    if not request.user.is_authenticated:
        return redirect('/homepage')

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            postId = data.get('postId')
            voteType = data.get('voteType')

            post = Post.objects.get(id=postId)
            vote, created = Vote.objects.get_or_create(user=request.user, post=post)

            if not created:
                if vote.voteType == voteType:
                    vote.delete()  # Undo vote
                    userVote = None
                else:
                    vote.voteType = voteType  # Change vote
                    vote.save()
                    userVote = voteType
            else:
                vote.voteType = voteType
                vote.save()
                userVote = voteType

            return JsonResponse({
                'up': post.get_upvotes(),
                'down': post.get_downvotes(),
                'userVote': userVote
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)

def bookmarkPost(request):
    if not request.user.is_authenticated:
        return redirect('/homepage')

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            postId = data.get("postId")
            post = get_object_or_404(Post, id=postId)

            bookmark, created = Bookmark.objects.get_or_create(user=request.user, post=post)

            if not created:
                # đã tồn tại → bỏ bookmark
                bookmark.delete()
                isBookmarked = False
            else:
                isBookmarked = True

            return JsonResponse({
                "bookmarks": post.get_bookmarks_count(),
                "isBookmarked": isBookmarked
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)


def postsDetail(request, postId):
    if not request.user.is_authenticated:
        return redirect("/")
    post=get_object_or_404(Post, id=postId)
    post.upvotes=post.get_upvotes()
    post.downvotes=post.get_downvotes()
    post.userVote=post.get_user_vote(request.user)

    return render(request, "postDetail.html", {'post': post})