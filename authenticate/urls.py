from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("signup/", views.signup),
    path("changepassword/", auth_views.PasswordChangeView.as_view(template_name="registration/password_change.html"), name="password_change"), #using the default template name lead to the site using the admin site template for some reason
    path("passwordchangedone/", auth_views.PasswordChangeDoneView.as_view(template_name="registration/change_password_done.html"), name="password_change_done"),
    path("<int:profileId>", views.viewProfile),
    path("", views.accountsList),
]