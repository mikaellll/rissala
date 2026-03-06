from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from apps.ai_engine.models import QueryHistory
from .forms import UserUpdateForm, ProfileUpdateForm
from .models import UserProfile


def _get_or_create_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


@login_required
def profile(request):
    """User profile view with edit forms and query history."""
    user_profile = _get_or_create_profile(request.user)

    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=user_profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Votre profil a été mis à jour avec succès.")
            return redirect("accounts:profile")
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=user_profile)

    # Paginated query history
    history_qs = QueryHistory.objects.filter(user=request.user).order_by("-created_at")
    paginator = Paginator(history_qs, 10)
    page_number = request.GET.get("page")
    history_page = paginator.get_page(page_number)

    context = {
        "user_form": user_form,
        "profile_form": profile_form,
        "history_page": history_page,
        "user_profile": user_profile,
    }
    return render(request, "accounts/profile.html", context)


@login_required
def delete_history_item(request, pk):
    """Delete a single query from history."""
    if request.method == "POST":
        QueryHistory.objects.filter(pk=pk, user=request.user).delete()
        messages.success(request, "Entrée supprimée.")
    return redirect("accounts:profile")
