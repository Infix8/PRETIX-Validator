import pytest
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from pretix.base.models import Event, Organizer, Question, Order, OrderPosition, Item, QuestionAnswer
from pretix_rollno_validator.signals import (
    validate_roll_number_format,
    normalize_roll_number,
    clean_roll_number,
    check_existing_roll_number,
    validate_against_predefined_list
)
from pretix_rollno_validator.exceptions import DuplicateRollNumberError, InvalidRollNumberError
from pretix_rollno_validator.constants import (
    MIN_ROLL_NUMBER_LENGTH,
    MAX_ROLL_NUMBER_LENGTH,
    ROLL_NUMBER_PATTERN
)


@pytest.fixture
def event():
    organizer = Organizer.objects.create(name='Dummy', slug='dummy')
    event = Event.objects.create(
        organizer=organizer,
        name='Dummy',
        slug='dummy',
        date_from='2024-01-01',
        plugins='pretix_rollno_validator'
    )
    
    # Add predefined valid roll numbers
    valid_students = [
        {'roll_number': 'CSE001', 'name': 'John Doe', 'department': 'Computer Science'},
        {'roll_number': 'CSE002', 'name': 'Jane Smith', 'department': 'Computer Science'},
        {'roll_number': 'ECE001', 'name': 'Alice Johnson', 'department': 'Electronics'}
    ]
    event.settings.set('valid_roll_numbers', valid_students)
    return event


@pytest.fixture
def roll_number_question(event):
    return Question.objects.create(
        event=event,
        question='Roll Number',
        type=Question.TYPE_TEXT,
        required=True,
        identifier='roll_number'
    )


@pytest.fixture
def ticket_item(event):
    return Item.objects.create(
        event=event,
        name='Ticket',
        default_price=10
    )


@pytest.mark.django_db
class TestRollNumberValidator:
    def test_clean_roll_number(self):
        """Test cleaning of roll numbers"""
        test_cases = [
            (' ABC-123 ', 'ABC-123'),  # Basic spaces
            ('CSE@001', 'CSE001'),     # Special character
            ('CSE#001!', 'CSE001'),    # Multiple special chars
            ('CSE  001', 'CSE001'),    # Multiple spaces
            ('CSE/001\\', 'CSE001'),   # Slashes
            ('CSE_001', 'CSE001'),     # Underscore
            ('123', '123'),            # Only numbers
            ('', '')                   # Empty string
        ]
        
        for input_str, expected in test_cases:
            assert clean_roll_number(input_str) == expected

    def test_normalize_roll_number(self):
        """Test roll number normalization"""
        test_cases = [
            (' ABC-123 ', 'ABC-123'),    # Basic normalization
            ('abc123', 'ABC123'),        # Case conversion
            ('cse001', 'CSE001'),        # Department code
            ('CSE  001', 'CSE001'),      # Multiple spaces
            ('cse-001', 'CSE-001'),      # With hyphen
            ('CSE@001', 'CSE001'),       # Special character
            ('123', '123'),              # Only numbers
            ('', ''),                    # Empty string
            (None, ''),                  # None value
            (123, '123')                 # Number input
        ]
        
        for input_val, expected in test_cases:
            assert normalize_roll_number(input_val) == expected

    def test_validate_roll_number_format(self):
        """Test roll number format validation"""
        # Valid roll numbers with different patterns
        valid_numbers = [
            'CSE001',      # Basic format
            'ECE002',      # Different department
            'CSE-001',     # With hyphen
            'ME001',       # Two-letter department
            'MECH101',     # Four-letter department
            'CS999999'     # Maximum digits
        ]
        
        for number in valid_numbers:
            try:
                result = validate_roll_number_format(number)
                assert result == normalize_roll_number(number)
            except ValidationError:
                pytest.fail(f"Roll number {number} should be valid")
        
        # Invalid roll numbers
        invalid_numbers = [
            ('', 'Roll number cannot be empty'),
            ('CS', f'Roll number must be at least {MIN_ROLL_NUMBER_LENGTH} characters long'),
            ('A' * (MAX_ROLL_NUMBER_LENGTH + 1), f'Roll number cannot be longer than {MAX_ROLL_NUMBER_LENGTH} characters'),
            ('123ABC', 'must start with letters'),
            ('CSEXXX', 'must start with letters followed by numbers'),
            ('CS-01', 'must start with letters followed by numbers'),
            ('CSEABC', 'must start with letters followed by numbers'),
            ('CSENG001', 'must start with 2-4 letters'),
            ('C1', 'must start with letters followed by numbers')
        ]
        
        for number, expected_error in invalid_numbers:
            with pytest.raises(ValidationError) as exc:
                validate_roll_number_format(number)
            assert expected_error in str(exc.value)
        
        # Test non-raising mode
        is_valid, _ = validate_roll_number_format('CSE001', raise_exception=False)
        assert is_valid
        
        is_valid, error = validate_roll_number_format('invalid', raise_exception=False)
        assert not is_valid
        assert 'must start with letters followed by numbers' in error

    def test_check_existing_roll_number(self):
        """Test duplicate roll number detection"""
        event = self.event
        question = self.roll_number_question
        
        # Test with non-existent roll number
        exists, _ = check_existing_roll_number(question.pk, 'CSE999', event)
        assert not exists
        
        # Test with existing roll number
        QuestionAnswer.objects.create(
            orderposition=self.order_position,
            question=question,
            answer='CSE001'
        )
        
        exists, error = check_existing_roll_number(question.pk, 'CSE001', event)
        assert exists
        assert 'already in use' in error
        
        # Test with different case
        exists, error = check_existing_roll_number(question.pk, 'cse001', event)
        assert exists
        assert 'already in use' in error

    def test_validate_against_predefined_list(self):
        """Test validation against predefined list"""
        event = self.event
        
        # Test valid roll numbers
        is_valid, _ = validate_against_predefined_list('CSE001', event)
        assert is_valid
        
        is_valid, _ = validate_against_predefined_list('cse001', event)  # Case insensitive
        assert is_valid
        
        # Test invalid roll numbers
        is_valid, error = validate_against_predefined_list('CSE999', event)
        assert not is_valid
        assert 'Invalid roll number' in error
        assert 'CSE001: John Doe' in error
        
        # Test with no predefined list
        event.settings.delete('valid_roll_numbers')
        is_valid, _ = validate_against_predefined_list('CSE999', event)
        assert is_valid

    def test_duplicate_roll_number(self, event, roll_number_question, ticket_item):
        """Test duplicate roll number detection in orders"""
        # Set roll number question in event settings
        event.settings.set('rollno_question_id', roll_number_question.pk)
        
        # Create first order with roll number
        order1 = Order.objects.create(
            event=event,
            status=Order.STATUS_PENDING,
            total=10
        )
        
        pos1 = OrderPosition.objects.create(
            order=order1,
            item=ticket_item,
            price=10
        )
        
        roll_number = 'CSE001'
        QuestionAnswer.objects.create(
            orderposition=pos1,
            question=roll_number_question,
            answer=roll_number
        )
        
        # Try variations of the same roll number
        variations = [
            roll_number,           # Exact match
            roll_number.lower(),   # Lowercase
            f" {roll_number} ",    # With spaces
            f"cse-001"            # With hyphen and different case
        ]
        
        for variant in variations:
            order2 = Order.objects.create(
                event=event,
                status=Order.STATUS_PENDING,
                total=10
            )
            
            pos2 = OrderPosition.objects.create(
                order=order2,
                item=ticket_item,
                price=10
            )
            
            with pytest.raises(ValidationError) as exc:
                QuestionAnswer.objects.create(
                    orderposition=pos2,
                    question=roll_number_question,
                    answer=variant
                )
            
            expected_error = _('Roll number "{number}" is already in use.').format(
                number=normalize_roll_number(variant)
            )
            assert expected_error in str(exc.value)
            
            # Cleanup
            order2.delete()

    def test_edge_cases(self, event, roll_number_question, ticket_item):
        """Test edge cases and special scenarios"""
        event.settings.set('rollno_question_id', roll_number_question.pk)
        
        test_cases = [
            # Special characters that should be removed
            ('CSE@001', 'CSE001'),
            ('CSE#001', 'CSE001'),
            ('CSE_001', 'CSE001'),
            
            # Multiple spaces and formatting
            ('  CSE  001  ', 'CSE001'),
            ('CSE - 001', 'CSE-001'),
            
            # Case variations
            ('cse001', 'CSE001'),
            ('CsE001', 'CSE001'),
            
            # Valid variations
            ('CS001', 'CS001'),
            ('MECH001', 'MECH001')
        ]
        
        for input_roll, expected_roll in test_cases:
            order = Order.objects.create(
                event=event,
                status=Order.STATUS_PENDING,
                total=10
            )
            
            pos = OrderPosition.objects.create(
                order=order,
                item=ticket_item,
                price=10
            )
            
            answer = QuestionAnswer.objects.create(
                orderposition=pos,
                question=roll_number_question,
                answer=input_roll
            )
            
            assert answer.answer == expected_roll
            order.delete() 