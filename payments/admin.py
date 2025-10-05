from django.contrib import admin
from .models import Transaction, AuditLog

# Register your models here.
admin.site.register(Transaction)
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("reference_no", "chama", "action_type", "amount", "timestamp")
    readonly_fields = [f.name for f in AuditLog._meta.get_fields()]
    search_fields = ("reference_no", "chama__name", "action_type")
    list_filter = ("action_type", "chama")
