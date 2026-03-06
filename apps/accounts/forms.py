from django import forms
from django.contrib.auth.models import User
from .models import UserProfile


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=100, required=False, label="Prénom")
    last_name = forms.CharField(max_length=100, required=False, label="Nom")

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]

    def clean_email(self):
        email = self.cleaned_data.get("email")
        qs = User.objects.filter(email=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Cet email est déjà utilisé.")
        return email


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["bio", "preferred_language", "avatar"]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "bio": "Biographie",
            "preferred_language": "Langue préférée",
            "avatar": "Photo de profil",
        }
