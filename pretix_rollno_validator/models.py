from django.db import models
from django.utils.translation import gettext_lazy as _
from pretix.base.models import Event


class Student(models.Model):
    """Model to store student information"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='valid_students')
    roll_number = models.CharField(
        max_length=20,
        verbose_name=_('Roll Number'),
        help_text=_('Student roll number (e.g., CSE001)')
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_('Student Name'),
        help_text=_('Full name of the student')
    )
    department = models.CharField(
        max_length=50,
        verbose_name=_('Department'),
        help_text=_('Department or branch of the student')
    )
    email = models.EmailField(
        verbose_name=_('Email'),
        help_text=_('Student email address'),
        blank=True
    )
    batch = models.CharField(
        max_length=10,
        verbose_name=_('Batch'),
        help_text=_('Student batch/year'),
        blank=True
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Active'),
        help_text=_('Whether this student is active and allowed to purchase tickets')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('event', 'roll_number')
        ordering = ['roll_number']
        verbose_name = _('Student')
        verbose_name_plural = _('Students')

    def __str__(self):
        return f"{self.roll_number} - {self.name}"

    def save(self, *args, **kwargs):
        # Update the event settings when student data changes
        super().save(*args, **kwargs)
        self._update_event_settings()

    def delete(self, *args, **kwargs):
        # Update the event settings when student is deleted
        super().delete(*args, **kwargs)
        self._update_event_settings()

    def _update_event_settings(self):
        """Update the event settings with current student data"""
        # Get all active students for this event
        students = Student.objects.filter(
            event=self.event,
            is_active=True
        ).values('roll_number', 'name', 'department', 'batch')
        
        # Convert to list of dictionaries
        valid_students = list(students)
        
        # Update event settings
        self.event.settings.set('valid_roll_numbers', valid_students) 