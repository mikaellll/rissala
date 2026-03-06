from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from apps.search.models import Book, BookChunk
from apps.ai_engine.models import QueryHistory


# ---------------------------------------------------------------------------
# Custom User Admin
# ---------------------------------------------------------------------------
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "is_active", "date_joined")
    list_filter = ("is_staff", "is_active", "date_joined")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("-date_joined",)

    fieldsets = UserAdmin.fieldsets + (
        ("Shamela IA Info", {"fields": ()}),
    )

    actions = ["activate_users", "deactivate_users"]

    def activate_users(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} utilisateurs activés.")
    activate_users.short_description = "Activer les utilisateurs sélectionnés"

    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} utilisateurs désactivés.")
    deactivate_users.short_description = "Désactiver les utilisateurs sélectionnés"


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# ---------------------------------------------------------------------------
# Book Admin
# ---------------------------------------------------------------------------
@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("shamela_id", "title", "author", "subject", "indexed_at")
    list_filter = ("subject",)
    search_fields = ("title", "author", "shamela_id")
    ordering = ("-indexed_at",)


@admin.register(BookChunk)
class BookChunkAdmin(admin.ModelAdmin):
    list_display = ("book", "page_number", "created_at")
    list_filter = ("book",)
    search_fields = ("book__title", "content")


# ---------------------------------------------------------------------------
# Query History Admin
# ---------------------------------------------------------------------------
@admin.register(QueryHistory)
class QueryHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "query_preview", "ai_backend", "created_at", "duration_ms")
    list_filter = ("ai_backend", "created_at")
    search_fields = ("user__username", "query")
    readonly_fields = ("user", "query", "response", "sources", "ai_backend", "duration_ms", "created_at")
    ordering = ("-created_at",)

    def query_preview(self, obj):
        return obj.query[:60] + "..." if len(obj.query) > 60 else obj.query
    query_preview.short_description = "Requête"


# ---------------------------------------------------------------------------
# Admin site branding
# ---------------------------------------------------------------------------
admin.site.site_header = "Shamela IA Wrapper — Administration"
admin.site.site_title = "Shamela IA Admin"
admin.site.index_title = "Tableau de bord"
