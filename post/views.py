from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect
# from django.views.decorators.http import require_POST
# from django.contrib.auth.decorators import login_required
from django.db.models import Count
import json
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

def postsList(request):
    if request.user.is_authenticated:

        posts=Post.objects.filter(author=request.user).order_by('-date')
        canShowAll=request.user.is_staff and request.GET.get("show_all")=="1"
        if canShowAll:
            posts=Post.objects.all().order_by('-date')
            
        for post in posts:
            post.userVote = post.get_user_vote(request.user) if request.user.is_authenticated else None

        return render(request, "postsList.html", {'posts': posts, 'canShowAll': canShowAll})
    else:
        return redirect("/")

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
