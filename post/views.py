from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.db.models import OuterRef, Subquery, Q, Count, CharField, Value, BooleanField, Exists
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpRequest
from django.db.models import OuterRef, Subquery, Q, Count, CharField
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

def postsList(request:HttpRequest):
    if not request.user.is_authenticated:
        return redirect("/")

    canShowAll = request.GET.get("show_all") == "1"

    inBookmarkView=request.resolver_match.url_name == "bookmarked_posts"

    # Base queryset
    postsQuery = Post.objects.all() if (canShowAll or inBookmarkView) else Post.objects.filter(author=request.user)
    if inBookmarkView:
        postsQuery=postsQuery.filter(bookmarks__user=request.user)

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

    selectedSortOption = request.POST.get('selectedSortOption') or 'time'
    selectedFilterOption = request.POST.get('selectedFilterOption') or 'all'

    # Sort
    if request.method == 'POST':
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

    if inBookmarkView:
        return render(request, "bookmarkedPosts.html", {'page_obj': page_obj})

    return render(request, "postsList.html", {
        'page_obj': page_obj,   # dùng page_obj thay vì posts
        'canShowAll': canShowAll,
        'selectedSortOption': selectedSortOption,
        'selectedFilterOption': selectedFilterOption
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

def postEdit(request: HttpRequest, postId):
    if not request.user.is_authenticated:
        return redirect('/')
    post=get_object_or_404(Post, id=postId)
    if not (request.user==post.author or request.user.is_staff):
        return redirect('/')
    if request.method == "POST":
        form=forms.postCreationForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect(f'/posts/{postId}')
    else:
        form=forms.postCreationForm(instance=post)

    return render(request, "editPost.html", {"form": form, "post": post})
