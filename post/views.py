from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
# from django.views.decorators.http import require_POST
# from django.contrib.auth.decorators import login_required
from django.db.models import Count
import json
from datetime import timedelta
from django.utils import timezone
from . import forms
from .models import Post, Vote

def deletePost(request, postId):
    if request.method=='POST':
        if request.user.is_authenticated:
            post=get_object_or_404(Post, id=postId)
            if request.user==post.author or request.user.is_staff:
                post.delete()
        return redirect("/posts/")
    return redirect("/homepage/")

from django.template.loader import render_to_string
from django.http import JsonResponse

from django.db.models import Count, Q
from django.shortcuts import render, redirect

def postsList(request):
    if not request.user.is_authenticated:
        return redirect("/")
    canShowAll = request.user.is_staff and request.GET.get("show_all") == "1"

    # Base queryset
    postsQuery = Post.objects.all() if canShowAll else Post.objects.filter(author=request.user)

    # Annotate upvote/downvote counts for sorting
    postsQuery = postsQuery.annotate(
        upvotes=Count('votes', filter=Q(votes__voteType='up')),
        downvotes=Count('votes', filter=Q(votes__voteType='down'))
    )

    selectedSortOption = request.POST.get('selectedSortOption') or 'time'
    selectedFilterOption = request.POST.get('selectedFilterOption') or 'all'


    # Handle sorting and filtering
    if request.method == 'POST':
        #Sort
        if selectedSortOption == 'upVote':
            postsQuery = postsQuery.order_by('-upvotes', 'downvotes')
        elif selectedSortOption == 'downVote':
            postsQuery = postsQuery.order_by('-downvotes', 'upvotes')
        else:
            postsQuery = postsQuery.order_by('-date')

        #Filter
        if selectedFilterOption == 'day':
            postsQuery = postsQuery.filter(date__gte=timezone.now() - timedelta(days=1))
        elif selectedFilterOption == 'week':
            postsQuery = postsQuery.filter(date__gte=timezone.now() - timedelta(weeks=1))
        elif selectedFilterOption == 'month':
            postsQuery = postsQuery.filter(date__gte=timezone.now() - timedelta(days=30))
        # else: all time

    else:
        postsQuery = postsQuery.order_by('-date')  # Default sort by time

    for post in postsQuery:
        post.userVote = post.get_user_vote(request.user)

    return render(request, "postsList.html", {
        'posts': postsQuery,
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
