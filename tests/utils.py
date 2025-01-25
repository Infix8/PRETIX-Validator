from typing import Dict, Any, Optional
from pretix.base.models import Event, Order, OrderPosition, QuestionAnswer


def create_test_order(event: Event, roll_number: str, status: str = Order.STATUS_PENDING) -> Order:
    """Create a test order with a roll number answer"""
    order = Order.objects.create(
        event=event,
        status=status,
        total=10,
        code=f'TEST-{roll_number}'
    )
    
    position = OrderPosition.objects.create(
        order=order,
        item=event.items.first(),
        price=10,
        positionid=1
    )
    
    question = event.questions.get(identifier='roll_number')
    QuestionAnswer.objects.create(
        orderposition=position,
        question=question,
        answer=roll_number
    )
    
    return order


def create_test_student(roll_number: str, name: str, department: str, **kwargs: Any) -> Dict[str, Any]:
    """Create a test student dictionary"""
    student = {
        'roll_number': roll_number,
        'name': name,
        'department': department,
        'batch': kwargs.get('batch', '2024'),
        'email': kwargs.get('email', f'{roll_number.lower()}@example.com'),
        'is_active': kwargs.get('is_active', True)
    }
    return student


def add_test_students_to_event(event: Event, students: Optional[list] = None) -> None:
    """Add test students to event settings"""
    if students is None:
        students = [
            create_test_student('CSE001', 'John Doe', 'Computer Science'),
            create_test_student('CSE002', 'Jane Smith', 'Computer Science'),
            create_test_student('ECE001', 'Alice Johnson', 'Electronics')
        ]
    
    event.settings.set('valid_roll_numbers', students)


def clear_caches(event: Event) -> None:
    """Clear all caches for testing"""
    from django.core.cache import cache
    from pretix_rollno_validator.constants import get_cache_key
    
    cache.delete(get_cache_key(event.id, 'department_codes'))
    cache.delete(get_cache_key(event.id, 'valid_students')) 