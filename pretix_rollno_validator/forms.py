import csv
import io
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Student


class StudentBulkImportForm(forms.Form):
    event = forms.ModelChoiceField(
        queryset=None,  # Set in __init__
        label=_('Event'),
        help_text=_('Select the event to import students for')
    )
    
    csv_file = forms.FileField(
        label=_('CSV File'),
        help_text=_('Upload a CSV file with student data. Required columns: roll_number, name, department')
    )
    
    update_existing = forms.BooleanField(
        required=False,
        initial=True,
        label=_('Update Existing'),
        help_text=_('Update existing students if roll number already exists')
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter events based on user permissions
        if user and not user.is_superuser:
            self.fields['event'].queryset = Event.objects.filter(
                organizer__in=user.teams.values_list('organizer', flat=True)
            )
        else:
            self.fields['event'].queryset = Event.objects.all()

    def clean_csv_file(self):
        csv_file = self.cleaned_data['csv_file']
        required_fields = {'roll_number', 'name', 'department'}
        
        try:
            # Read CSV file
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            
            # Validate headers
            headers = set(reader.fieldnames)
            missing_fields = required_fields - headers
            if missing_fields:
                raise forms.ValidationError(
                    _('Missing required columns: {fields}').format(
                        fields=', '.join(missing_fields)
                    )
                )
            
            # Store rows for later processing
            self.cleaned_data['rows'] = list(reader)
            
            return csv_file
            
        except UnicodeDecodeError:
            raise forms.ValidationError(_('Please upload a valid UTF-8 encoded CSV file'))
        except Exception as e:
            raise forms.ValidationError(_('Error reading CSV file: {error}').format(error=str(e)))

    def save(self):
        event = self.cleaned_data['event']
        rows = self.cleaned_data['rows']
        update_existing = self.cleaned_data['update_existing']
        
        created = []
        updated = []
        errors = []
        
        for row in rows:
            try:
                # Clean and normalize data
                student_data = {
                    'event': event,
                    'roll_number': row['roll_number'].strip().upper(),
                    'name': row['name'].strip(),
                    'department': row['department'].strip(),
                    'email': row.get('email', '').strip(),
                    'batch': row.get('batch', '').strip(),
                    'is_active': row.get('is_active', 'true').lower() == 'true'
                }
                
                # Try to get existing student
                student, created_new = Student.objects.get_or_create(
                    event=event,
                    roll_number=student_data['roll_number'],
                    defaults=student_data
                )
                
                if not created_new and update_existing:
                    # Update existing student
                    for key, value in student_data.items():
                        setattr(student, key, value)
                    student.save()
                    updated.append(student)
                elif created_new:
                    created.append(student)
                    
            except Exception as e:
                errors.append(f"Row {row}: {str(e)}")
        
        return {
            'created': created,
            'updated': updated,
            'errors': errors
        } 