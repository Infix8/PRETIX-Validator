from django.urls import path
from .views import StudentBulkImportView

urlpatterns = [
    path('import/', StudentBulkImportView.as_view(), name='import'),
]

app_name = 'pretix_rollno_validator' 