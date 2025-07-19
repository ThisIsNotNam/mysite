from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect

def signup(request):
    if request.method == "POST":
        # print("POST received")
        form = UserCreationForm(request.POST)
        if form.is_valid():
            # print("Form is valid")
            form.save()
            return redirect("/accounts/login")
        # else:
            # print("Form errors:", form.errors)
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})

def accountsRedirect(request):
    return redirect("login/")
