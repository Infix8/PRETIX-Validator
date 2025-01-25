from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView
from pretix.control.permissions import EventPermissionRequiredMixin
from .forms import StudentBulkImportForm


class StudentBulkImportView(LoginRequiredMixin, EventPermissionRequiredMixin, FormView):
    template_name = 'pretix_rollno_validator/import.html'
    form_class = StudentBulkImportForm
    permission = 'can_change_event_settings'
    success_url = reverse_lazy('plugins:pretix_rollno_validator:import')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        result = form.save()
        
        # Show success message
        if result['created'] or result['updated']:
            messages.success(
                self.request,
                _('Successfully imported {created} new students and updated {updated} existing students.').format(
                    created=len(result['created']),
                    updated=len(result['updated'])
                )
            )
        
        # Show errors if any
        if result['errors']:
            messages.error(
                self.request,
                _('Encountered {count} errors during import:\n{errors}').format(
                    count=len(result['errors']),
                    errors='\n'.join(result['errors'])
                )
            )
        
        return super().form_valid(form) 