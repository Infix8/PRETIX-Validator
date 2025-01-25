# Cache settings
CACHE_TIMEOUT = 3600  # 1 hour
CACHE_KEY_PREFIX = 'pretix_rollno_validator'

# Roll number validation
MIN_ROLL_NUMBER_LENGTH = 5  # e.g., CS001
MAX_ROLL_NUMBER_LENGTH = 12  # e.g., MECH-123456

# Pattern for valid characters (only letters, numbers, and hyphens)
VALID_CHARS_PATTERN = r'[^A-Za-z0-9-]'

# Pattern components for roll number validation
DEPARTMENT_CODE_PATTERN = r'[A-Z]{2,4}'  # 2-4 uppercase letters
NUMBER_PATTERN = r'\d{3,6}'              # 3-6 digits
OPTIONAL_HYPHEN = r'-?'                  # Optional hyphen

# Complete pattern for roll number format validation
# Must start with 2-4 letters (department code)
# Optionally followed by a hyphen
# Followed by 3-6 numbers
ROLL_NUMBER_PATTERN = f'^{DEPARTMENT_CODE_PATTERN}{OPTIONAL_HYPHEN}{NUMBER_PATTERN}$'

# Department codes (for validation)
VALID_DEPARTMENT_CODES = {
    'CS', 'CSE',    # Computer Science
    'EC', 'ECE',    # Electronics
    'ME', 'MECH',   # Mechanical
    'EE',           # Electrical
    'CE', 'CIVIL',  # Civil
    'IT',           # Information Technology
    'BT', 'BTECH'   # Biotechnology
}

# Question types that can be used for roll numbers
VALID_QUESTION_TYPES = ['T', 'N']  # Text or Number

# Order statuses to check for duplicates
DUPLICATE_CHECK_ORDER_STATUSES = [
    'PENDING',  # Order is awaiting payment
    'PAID',     # Order has been paid
]

# Settings keys
SETTINGS_KEY_QUESTION_ID = 'rollno_question_id'
SETTINGS_KEY_VALID_STUDENTS = 'valid_roll_numbers'
SETTINGS_KEY_DEPARTMENT_CODES = 'valid_department_codes'

# Logging
LOG_PREFIX = '[RollNoValidator]'
LOG_FORMAT = '%(asctime)s %(levelname)s [%(name)s] %(message)s'

# Error messages
ERROR_MESSAGES = {
    'empty': _('Roll number cannot be empty'),
    'too_short': _('Roll number must be at least {length} characters long'),
    'too_long': _('Roll number cannot be longer than {length} characters'),
    'invalid_format': _('Roll number must start with a valid department code (e.g., CSE, ECE) followed by numbers'),
    'invalid_department': _('Invalid department code. Valid codes are: {codes}'),
    'duplicate': _('Roll number "{number}" is already in use'),
    'not_in_list': _('Invalid roll number. Please use one of the following:\n{list}'),
}

# Cache keys
def get_cache_key(event_id, key_type):
    """Generate cache key for different types of data"""
    return f"{CACHE_KEY_PREFIX}:{event_id}:{key_type}" 