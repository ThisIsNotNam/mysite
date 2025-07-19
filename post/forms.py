from django import forms
from . import models

class postCreationForm(forms.ModelForm):
    class Meta:
        model=models.Post
        fields=['title', 'body']