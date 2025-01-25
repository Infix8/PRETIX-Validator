import logging
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from pretix.base.settings import SettingsSandbox
from pretix.base.signals import event_copy_data, event_settings_panel
from django.core.cache import cache
from django import forms

logger = logging.getLogger(__name__)

CACHE_TIMEOUT = 3600  # 1 hour

class RollNumberSettingsHolder(SettingsSandbox):
    def get_roll_number_question(self):
        """Get roll number question with caching"""
        cache_key = f'rollno_question_{self.event.pk}'
        cached_value = cache.get(cache_key)
        
        if cached_value is not None:
            return cached_value
            
        value = self.settings.get('rollno_question_id', None)
        cache.set(cache_key, value, CACHE_TIMEOUT)
        return value

    def set_roll_number_question(self, value):
        """Set roll number question and update cache"""
        cache_key = f'rollno_question_{self.event.pk}'
        self.settings.set('rollno_question_id', value)
        cache.set(cache_key, value, CACHE_TIMEOUT)


class RollNumberSettingsForm(forms.Form):
    rollno_question_id = forms.ModelChoiceField(
        queryset=None,  # Set in __init__
        required=False,
        label=_('Roll Number Question'),
        help_text=_('Select which question should be validated for uniqueness. '
                   'The question must be required and of type text or number.')
    )

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super().__init__(*args, **kwargs)
        
        try:
            # Only show text questions that are required and active
            self.fields['rollno_question_id'].queryset = self.event.questions.filter(
                type__in=['T', 'N'],  # Text or Number type questions
                required=True,
                active=True
            ).select_related('event')  # Optimize query
            
            # Set initial value
            self.fields['rollno_question_id'].initial = self.event.settings.get('rollno_question_id')
            
        except Exception as e:
            logger.error(f"Error initializing RollNumberSettingsForm for event {self.event.pk}: {str(e)}")
            self.fields['rollno_question_id'].queryset = self.event.questions.none()

    def clean(self):
        cleaned_data = super().clean()
        question = cleaned_data.get('rollno_question_id')
        
        if question:
            if not question.required:
                raise forms.ValidationError(
                    _('The selected question must be marked as required')
                )
                
            if question.type not in ['T', 'N']:
                raise forms.ValidationError(
                    _('The selected question must be of type text or number')
                )
                
            # Check if question belongs to the correct event
            if question.event_id != self.event.pk:
                raise forms.ValidationError(
                    _('The selected question does not belong to this event')
                )
            
        return cleaned_data

    def save(self):
        """Save the form data with proper error handling"""
        try:
            question = self.cleaned_data.get('rollno_question_id')
            holder = RollNumberSettingsHolder(self.event)
            holder.set_roll_number_question(question.pk if question else None)
            
            logger.info(f"Roll number settings updated for event {self.event.pk}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving roll number settings for event {self.event.pk}: {str(e)}")
            return False


@receiver(event_settings_panel, dispatch_uid='rollno_settings_panel')
def register_settings_panel(sender, request, **kwargs):
    return [
        ('rollno', _('Roll Number Settings'), RollNumberSettingsForm, 'pretix_rollno_validator/settings.html')
    ]


@receiver(event_copy_data, dispatch_uid='rollno_copy_data')
def copy_settings(sender, other, **kwargs):
    """Copy roll number settings when duplicating an event"""
    try:
        question_id = other.settings.get('rollno_question_id')
        if question_id:
            # Check if the question was also copied
            if sender.questions.filter(pk=question_id).exists():
                sender.settings.set('rollno_question_id', question_id)
                logger.info(f"Roll number settings copied from event {other.pk} to {sender.pk}")
            else:
                logger.warning(f"Question {question_id} not found in target event {sender.pk}")
                
    except Exception as e:
        logger.error(f"Error copying roll number settings from event {other.pk} to {sender.pk}: {str(e)}") 