from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Student, Event


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['roll_number', 'name', 'department', 'batch', 'is_active', 'event']
    list_filter = ['event', 'department', 'batch', 'is_active']
    search_fields = ['roll_number', 'name', 'email']
    ordering = ['roll_number']
    
    fieldsets = (
        (None, {
            'fields': ('event', 'roll_number', 'name')
        }),
        (_('Additional Information'), {
            'fields': ('department', 'email', 'batch')
        }),
        (_('Status'), {
            'fields': ('is_active',)
        })
    )
    
    def get_queryset(self, request):
        """Only show students for events the user has access to"""
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(event__organizer__in=request.user.teams.values_list('organizer', flat=True))
        return qs
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filter event choices based on user permissions"""
        if db_field.name == "event" and not request.user.is_superuser:
            kwargs["queryset"] = Event.objects.filter(
                organizer__in=request.user.teams.values_list('organizer', flat=True)
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs) 