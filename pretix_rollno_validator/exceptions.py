from django.utils.translation import gettext_lazy as _
from pretix.base.services.orders import OrderError


class RollNumberError(OrderError):
    """Base exception for roll number validation errors"""
    pass


class DuplicateRollNumberError(RollNumberError):
    """Exception raised when a duplicate roll number is found"""
    def __init__(self, roll_number):
        self.roll_number = roll_number
        super().__init__(
            _('Roll number "{number}" is already in use.').format(number=roll_number)
        )


class InvalidRollNumberError(RollNumberError):
    """Exception raised when roll number format is invalid"""
    pass


class RollNumberConfigError(RollNumberError):
    """Exception raised when there are configuration issues"""
    pass 