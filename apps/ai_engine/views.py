import json
import logging
from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.cache import cache

from .forms import AiQueryForm
from .models import QueryHistory
from .tasks import run_ai_query

logger = logging.getLogger(__name__)

RATE_LIMIT_WINDOW = 3600  # 1 hour in seconds


def _check_rate_limit(request) -> bool:
    """Return True if request is within rate limit, False if exceeded."""
    if request.user.is_authenticated:
        key = f"rl_ai_{request.user.pk}"
    else:
        key = f"rl_ai_anon_{request.META.get('REMOTE_ADDR', 'unknown')}"

    count = cache.get(key, 0)
    limit = getattr(settings, "AI_RATE_LIMIT", 20)

    if count >= limit:
        return False

    cache.set(key, count + 1, RATE_LIMIT_WINDOW)
    return True


def ai_search(request):
    """Main AI search page (form + results)."""
    form = AiQueryForm(request.GET or None)
    result = None
    error = None

    if request.GET.get("query") and form.is_valid():
        if not _check_rate_limit(request):
            error = "Vous avez dépassé la limite de requêtes (20/heure). Réessayez plus tard."
        else:
            query = form.cleaned_data["query"]
            language = form.cleaned_data["language"]

            try:
                result = run_ai_query(query, language=language)

                # Save to history
                user = request.user if request.user.is_authenticated else None
                QueryHistory.objects.create(
                    user=user,
                    query=query,
                    response=result["answer"],
                    sources=result["sources"],
                    ai_backend=result["backend"],
                    duration_ms=result["duration_ms"],
                )
            except Exception as e:
                logger.error(f"AI query error: {e}", exc_info=True)
                error = "Une erreur inattendue s'est produite. Veuillez réessayer."

    context = {
        "form": form,
        "result": result,
        "error": error,
        "ai_backend": getattr(settings, "AI_BACKEND", "openai"),
    }
    return render(request, "ai_engine/ai_search.html", context)


@require_http_methods(["POST"])
def ai_query_ajax(request):
    """AJAX endpoint for IA queries (JSON response)."""
    if not _check_rate_limit(request):
        return JsonResponse(
            {"error": "Limite de requêtes atteinte. Réessayez dans 1 heure."},
            status=429,
        )

    try:
        data = json.loads(request.body)
        query = data.get("query", "").strip()
        language = data.get("language", "fr")

        if not query or len(query) < 5:
            return JsonResponse({"error": "La question est trop courte."}, status=400)

        if len(query) > 1000:
            return JsonResponse({"error": "La question est trop longue (max 1000 car.)."}, status=400)

        result = run_ai_query(query, language=language)

        user = request.user if request.user.is_authenticated else None
        QueryHistory.objects.create(
            user=user,
            query=query,
            response=result["answer"],
            sources=result["sources"],
            ai_backend=result["backend"],
            duration_ms=result["duration_ms"],
        )

        return JsonResponse(result)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Corps de requête JSON invalide."}, status=400)
    except Exception as e:
        logger.error(f"AJAX AI error: {e}", exc_info=True)
        return JsonResponse({"error": "Erreur interne du serveur."}, status=500)
