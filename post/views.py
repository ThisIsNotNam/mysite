from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from . import forms
from .models import Post

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
        posts=Post.objects.filter(author=request.user)
        if request.user.is_staff and request.GET.get("show_all")=="1":
            posts=Post.objects.all()
        return render(request, "postsList.html", {'posts': posts})
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
