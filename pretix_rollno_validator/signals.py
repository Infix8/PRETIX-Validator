import re
import logging
from functools import lru_cache
from typing import Tuple, Optional, Dict, Any

from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.cache import cache
from django.db import transaction
from django.db.models import Q

from pretix.base.signals import order_placed, validate_cart_addons
from pretix.base.models import QuestionAnswer, Order, OrderPosition, Question, Event
from pretix.base.services.orders import OrderError

from .constants import (
    MIN_ROLL_NUMBER_LENGTH,
    MAX_ROLL_NUMBER_LENGTH,
    ROLL_NUMBER_PATTERN,
    DEPARTMENT_CODE_PATTERN,
    VALID_DEPARTMENT_CODES,
    DUPLICATE_CHECK_ORDER_STATUSES,
    VALID_CHARS_PATTERN,
    ERROR_MESSAGES,
    get_cache_key
)
from .exceptions import DuplicateRollNumberError, InvalidRollNumberError

logger = logging.getLogger(__name__)

@lru_cache(maxsize=128)
def get_department_code(roll_number: str) -> Optional[str]:
    """Extract department code from roll number"""
    match = re.match(DEPARTMENT_CODE_PATTERN, roll_number)
    return match.group(0) if match else None

def get_valid_department_codes(event: Event) -> set:
    """Get valid department codes for the event"""
    cache_key = get_cache_key(event.id, 'department_codes')
    codes = cache.get(cache_key)
    
    if codes is None:
        # Try to get from event settings
        codes = set(event.settings.get('valid_department_codes', []))
        if not codes:
            # Fall back to default codes
            codes = VALID_DEPARTMENT_CODES
        cache.set(cache_key, codes, timeout=3600)
    
    return codes

def clean_roll_number(roll_number: str) -> str:
    """Remove invalid characters from roll number"""
    if not isinstance(roll_number, str):
        roll_number = str(roll_number)
    # Only keep alphanumeric and hyphen characters
    return re.sub(VALID_CHARS_PATTERN, '', roll_number)

def normalize_roll_number(roll_number: str) -> str:
    """Normalize roll number by removing invalid chars and converting to uppercase"""
    if not roll_number:
        return ''
    # Clean and normalize
    roll_number = clean_roll_number(roll_number)
    return roll_number.strip().upper()

def validate_department_code(roll_number: str, event: Event) -> None:
    """Validate that the department code is valid"""
    dept_code = get_department_code(roll_number)
    if not dept_code:
        raise InvalidRollNumberError(ERROR_MESSAGES['invalid_format'])
        
    valid_codes = get_valid_department_codes(event)
    if dept_code not in valid_codes:
        raise InvalidRollNumberError(
            ERROR_MESSAGES['invalid_department'].format(
                codes=', '.join(sorted(valid_codes))
            )
        )

def validate_roll_number_format(roll_number: str, event: Event, raise_exception: bool = True) -> Tuple[bool, str]:
    """
    Validate roll number format
    Args:
        roll_number: The roll number to validate
        event: The event context for validation
        raise_exception: Whether to raise exception on invalid format
    Returns:
        (bool, str): (is_valid, normalized_roll_number) if raise_exception is False
        str: normalized_roll_number if raise_exception is True
    Raises:
        InvalidRollNumberError: If roll number is invalid and raise_exception is True
    """
    try:
        if not roll_number:
            raise InvalidRollNumberError(ERROR_MESSAGES['empty'])
        
        # Normalize roll number
        roll_number = normalize_roll_number(roll_number)
        
        # Length validation
        if len(roll_number) < MIN_ROLL_NUMBER_LENGTH:
            raise InvalidRollNumberError(
                ERROR_MESSAGES['too_short'].format(length=MIN_ROLL_NUMBER_LENGTH)
            )
        if len(roll_number) > MAX_ROLL_NUMBER_LENGTH:
            raise InvalidRollNumberError(
                ERROR_MESSAGES['too_long'].format(length=MAX_ROLL_NUMBER_LENGTH)
            )
        
        # Format validation
        if not re.match(ROLL_NUMBER_PATTERN, roll_number):
            raise InvalidRollNumberError(ERROR_MESSAGES['invalid_format'])
        
        # Department code validation
        validate_department_code(roll_number, event)
        
        return roll_number if raise_exception else (True, roll_number)
        
    except InvalidRollNumberError as e:
        if raise_exception:
            raise
        return False, str(e)

def check_existing_roll_number(question_id: int, roll_number: str, event: Event, exclude_order: Optional[Order] = None) -> Tuple[bool, Optional[str]]:
    """
    Check if roll number already exists in the event
    Returns:
        (bool, str): (exists, error_message)
    """
    try:
        # Normalize roll number first
        roll_number = normalize_roll_number(roll_number)
        
        # Use select_related to optimize query
        query = QuestionAnswer.objects.select_related(
            'orderposition__order'
        ).filter(
            question_id=question_id,
            answer__iexact=roll_number,
            orderposition__order__event=event,
            orderposition__order__status__in=DUPLICATE_CHECK_ORDER_STATUSES
        )
        
        if exclude_order:
            query = query.exclude(orderposition__order=exclude_order)
        
        exists = query.exists()
        if exists:
            error_msg = ERROR_MESSAGES['duplicate'].format(number=roll_number)
            logger.warning(
                f"Duplicate roll number detected: {roll_number}",
                extra={
                    'event_id': event.id,
                    'roll_number': roll_number,
                    'question_id': question_id
                }
            )
            return True, error_msg
            
        return False, None
        
    except Exception as e:
        error_msg = f"Error checking roll number: {str(e)}"
        logger.error(
            error_msg,
            extra={
                'event_id': event.id,
                'roll_number': roll_number,
                'question_id': question_id
            },
            exc_info=True
        )
        return True, error_msg

def get_valid_students(event: Event) -> list:
    """Get valid students list with caching"""
    cache_key = get_cache_key(event.id, 'valid_students')
    students = cache.get(cache_key)
    
    if students is None:
        students = event.settings.get('valid_roll_numbers', [])
        cache.set(cache_key, students, timeout=3600)
    
    return students

def validate_against_predefined_list(roll_number: str, event: Event) -> Tuple[bool, Optional[str]]:
    """
    Validate roll number against predefined list
    Returns:
        (bool, str): (is_valid, error_message)
    """
    try:
        valid_students = get_valid_students(event)
        if not valid_students:
            return True, None
            
        roll_number = normalize_roll_number(roll_number)
        valid_roll_numbers = {
            normalize_roll_number(s['roll_number']): s 
            for s in valid_students
        }
        
        if roll_number not in valid_roll_numbers:
            student_list = '\n'.join(
                f"- {s['roll_number']}: {s['name']} ({s.get('department', '')})"
                for s in valid_students
            )
            error_msg = ERROR_MESSAGES['not_in_list'].format(list=student_list)
            logger.warning(
                f"Invalid roll number not in predefined list: {roll_number}",
                extra={
                    'event_id': event.id,
                    'roll_number': roll_number
                }
            )
            return False, error_msg
            
        return True, None
        
    except Exception as e:
        error_msg = f"Error validating against predefined list: {str(e)}"
        logger.error(
            error_msg,
            extra={'event_id': event.id, 'roll_number': roll_number},
            exc_info=True
        )
        return False, error_msg

def validate_roll_number_answer(answer: str, event: Event, question_id: int, exclude_order: Optional[Order] = None) -> str:
    """
    Validate roll number answer
    Returns:
        str: Normalized roll number if valid
    Raises:
        InvalidRollNumberError: If roll number is invalid
        DuplicateRollNumberError: If roll number is duplicate
    """
    # Validate format
    roll_number = validate_roll_number_format(answer, event)
    
    # Validate against predefined list
    is_valid, error_msg = validate_against_predefined_list(roll_number, event)
    if not is_valid:
        raise InvalidRollNumberError(error_msg)
    
    # Check for duplicates
    exists, error_msg = check_existing_roll_number(
        question_id, roll_number, event, exclude_order
    )
    if exists:
        raise DuplicateRollNumberError(roll_number)
    
    return roll_number

@receiver(validate_cart_addons, dispatch_uid="rollno_validate_cart")
def validate_roll_number(sender: Any, **kwargs: Dict[str, Any]) -> None:
    cart_data = kwargs.get('cart_data', {})
    event = kwargs.get('event')
    
    # Get roll number question ID from settings
    question_id = event.settings.get('rollno_question_id')
    if not question_id:
        return
        
    try:
        # Verify question exists and is active
        question = Question.objects.select_related('event').get(
            id=question_id,
            event=event,
            active=True
        )
    except Question.DoesNotExist:
        logger.warning(
            f"Roll number question not found or inactive",
            extra={'event_id': event.id, 'question_id': question_id}
        )
        return
    
    # Get the roll number question from cart data
    for item in cart_data:
        if 'questions' not in item:
            continue
            
        for q_id, answer in item['questions'].items():
            if str(q_id) != str(question_id):
                continue
                
            try:
                # Validate roll number
                roll_number = validate_roll_number_answer(answer, event, question_id)
                
                # Update the answer with normalized roll number
                item['questions'][q_id] = roll_number
                
            except (InvalidRollNumberError, DuplicateRollNumberError) as e:
                logger.info(
                    f"Roll number validation failed: {str(e)}",
                    extra={'event_id': event.id, 'answer': answer}
                )
                raise ValidationError(str(e))


@receiver(order_placed, dispatch_uid="rollno_order_placed")
def on_order_placed(sender: Any, order: Order, **kwargs: Dict[str, Any]) -> None:
    """Double-check validation when order is placed to prevent race conditions"""
    event = order.event
    question_id = event.settings.get('rollno_question_id')
    
    if not question_id:
        return
        
    try:
        question = Question.objects.select_related('event').get(
            id=question_id,
            event=event,
            active=True
        )
    except Question.DoesNotExist:
        logger.warning(
            f"Roll number question not found or inactive",
            extra={'event_id': event.id, 'question_id': question_id}
        )
        return
        
    with transaction.atomic():
        try:
            for position in order.positions.select_related('order').prefetch_related('answers').all():
                answers = position.answers.filter(question_id=question_id)
                
                for answer in answers:
                    try:
                        # Validate roll number
                        roll_number = validate_roll_number_answer(
                            answer.answer,
                            event,
                            question_id,
                            exclude_order=order
                        )
                        
                        # Update answer with normalized version
                        if answer.answer != roll_number:
                            answer.answer = roll_number
                            answer.save(update_fields=['answer'])
                            
                    except (InvalidRollNumberError, DuplicateRollNumberError) as e:
                        order.status = Order.STATUS_CANCELED
                        order.save(update_fields=['status'])
                        logger.warning(
                            f"Roll number validation failed: {str(e)}",
                            extra={
                                'order': order.code,
                                'event_id': event.id,
                                'answer': answer.answer
                            }
                        )
                        raise OrderError(str(e))
                        
        except Exception as e:
            logger.error(
                f"Unexpected error processing order: {str(e)}",
                extra={
                    'order': order.code,
                    'event_id': event.id
                },
                exc_info=True
            )
            order.status = Order.STATUS_CANCELED
            order.save(update_fields=['status'])
            raise 