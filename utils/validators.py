"""
RadheFoundation HRA - Input Validators
Industry-Level Human Resource Management System

This module provides validation functions for various input types.
"""

from typing import Optional, Tuple, List, Callable
import re
from datetime import date, datetime


class ValidationResult:
    """Container for validation results."""

    def __init__(self, is_valid: bool, error_message: str = ""):
        self.is_valid = is_valid
        self.error_message = error_message

    def __bool__(self):
        return self.is_valid

    def __str__(self):
        return self.error_message


class Validator:
    """Base validator class."""

    @staticmethod
    def validate(value, required: bool = False) -> ValidationResult:
        """Validate a value."""
        return ValidationResult(True)


class StringValidator(Validator):
    """Validator for string inputs."""

    def __init__(
        self,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        pattern_name: str = None,
        allow_numbers: bool = True,
        allow_special: bool = True,
        special_chars: str = "_-.",
    ):
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = pattern
        self.pattern_name = pattern_name
        self.allow_numbers = allow_numbers
        self.allow_special = allow_special
        self.special_chars = special_chars

    def validate(self, value: str, required: bool = False) -> ValidationResult:
        """Validate a string value."""
        if not value or not value.strip():
            if required:
                return ValidationResult(False, "This field is required")
            return ValidationResult(True)

        value = value.strip()

        if self.min_length is not None and len(value) < self.min_length:
            return ValidationResult(
                False, f"Must be at least {self.min_length} characters"
            )

        if self.max_length is not None and len(value) > self.max_length:
            return ValidationResult(
                False, f"Must be at most {self.max_length} characters"
            )

        if self.pattern:
            if not re.match(self.pattern, value):
                msg = f"Invalid format" if not self.pattern_name else self.pattern_name
                return ValidationResult(False, msg)

        return ValidationResult(True)


class EmailValidator(Validator):
    """Validator for email addresses."""

    def __init__(self, allow_empty: bool = False):
        self.allow_empty = allow_empty

    def validate(self, value: str, required: bool = False) -> ValidationResult:
        """Validate an email address."""
        if not value or not value.strip():
            if required or not self.allow_empty:
                return ValidationResult(False, "Email is required")
            return ValidationResult(True)

        value = value.strip().lower()

        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(pattern, value):
            return ValidationResult(False, "Invalid email format")

        return ValidationResult(True)


class PhoneValidator(Validator):
    """Validator for phone numbers."""

    def __init__(self, allow_empty: bool = False, formats: List[str] = None):
        self.allow_empty = allow_empty
        self.formats = formats or [
            r"^[0-9]{10}$",
            r"^[0-9]{3}-[0-9]{3}-[0-9]{4}$",
            r"^\+[0-9]{1,3}[0-9]{10}$",
            r"^[0-9\s\-\+\(\)]{10,15}$",
        ]

    def validate(self, value: str, required: bool = False) -> ValidationResult:
        """Validate a phone number."""
        if not value or not value.strip():
            if required or not self.allow_empty:
                return ValidationResult(False, "Phone number is required")
            return ValidationResult(True)

        value = value.strip()

        for pattern in self.formats:
            if re.match(pattern, value):
                return ValidationResult(True)

        return ValidationResult(
            False, "Invalid phone number format"
        )


class PasswordValidator(Validator):
    """Validator for passwords."""

    def __init__(
        self,
        min_length: int = 8,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_digit: bool = True,
        require_special: bool = False,
        special_chars: str = "!@#$%^&*()_+-=[]{}|;:,.<>?",
    ):
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digit = require_digit
        self.require_special = require_special
        self.special_chars = special_chars

    def validate(self, value: str, required: bool = True) -> ValidationResult:
        """Validate a password."""
        if not value:
            if required:
                return ValidationResult(False, "Password is required")
            return ValidationResult(True)

        errors = []

        if len(value) < self.min_length:
            errors.append(f"at least {self.min_length} characters")

        if self.require_uppercase and not any(c.isupper() for c in value):
            errors.append("one uppercase letter")

        if self.require_lowercase and not any(c.islower() for c in value):
            errors.append("one lowercase letter")

        if self.require_digit and not any(c.isdigit() for c in value):
            errors.append("one number")

        if self.require_special:
            if not any(c in self.special_chars for c in value):
                errors.append("one special character")

        if errors:
            return ValidationResult(
                False,
                "Password must contain: " + ", ".join(errors)
            )

        return ValidationResult(True)


class UsernameValidator(Validator):
    """Validator for usernames."""

    def __init__(self, min_length: int = 3, max_length: int = 50):
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, value: str, required: bool = True) -> ValidationResult:
        """Validate a username."""
        if not value or not value.strip():
            if required:
                return ValidationResult(False, "Username is required")
            return ValidationResult(True)

        value = value.strip()

        if len(value) < self.min_length:
            return ValidationResult(
                False, f"Username must be at least {self.min_length} characters"
            )

        if len(value) > self.max_length:
            return ValidationResult(
                False, f"Username must be at most {self.max_length} characters"
            )

        if not re.match(r"^[a-zA-Z0-9_]+$", value):
            return ValidationResult(
                False, "Username can only contain letters, numbers, and underscores"
            )

        return ValidationResult(True)


class DateValidator(Validator):
    """Validator for dates."""

    def __init__(
        self,
        allow_future: bool = False,
        allow_past: bool = True,
        min_date: Optional[date] = None,
        max_date: Optional[date] = None,
    ):
        self.allow_future = allow_future
        self.allow_past = allow_past
        self.min_date = min_date
        self.max_date = max_date

    def validate(self, value: date, required: bool = False) -> ValidationResult:
        """Validate a date."""
        if not value:
            if required:
                return ValidationResult(False, "Date is required")
            return ValidationResult(True)

        today = date.today()

        if not self.allow_future and value > today:
            return ValidationResult(False, "Date cannot be in the future")

        if not self.allow_past and value < today:
            return ValidationResult(False, "Date cannot be in the past")

        if self.min_date and value < self.min_date:
            return ValidationResult(
                False, f"Date cannot be before {self.min_date}"
            )

        if self.max_date and value > self.max_date:
            return ValidationResult(
                False, f"Date cannot be after {self.max_date}"
            )

        return ValidationResult(True)


class NumberValidator(Validator):
    """Validator for numeric inputs."""

    def __init__(
        self,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        allow_decimal: bool = True,
        integer_only: bool = False,
        positive_only: bool = False,
    ):
        self.min_value = min_value
        self.max_value = max_value
        self.allow_decimal = allow_decimal
        self.integer_only = integer_only
        self.positive_only = positive_only

    def validate(self, value: any, required: bool = False) -> ValidationResult:
        """Validate a number."""
        if value is None or value == "":
            if required:
                return ValidationResult(False, "This field is required")
            return ValidationResult(True)

        try:
            if self.integer_only:
                num = int(value)
            else:
                num = float(value)
        except (ValueError, TypeError):
            return ValidationResult(False, "Must be a valid number")

        if self.positive_only and num < 0:
            return ValidationResult(False, "Must be a positive number")

        if self.min_value is not None and num < self.min_value:
            return ValidationResult(
                False, f"Must be at least {self.min_value}"
            )

        if self.max_value is not None and num > self.max_value:
            return ValidationResult(
                False, f"Must be at most {self.max_value}"
            )

        return ValidationResult(True)


class URLValidator(Validator):
    """Validator for URLs."""

    def __init__(self, protocols: List[str] = None, allow_empty: bool = True):
        self.protocols = protocols or ["http", "https"]
        self.allow_empty = allow_empty

    def validate(self, value: str, required: bool = False) -> ValidationResult:
        """Validate a URL."""
        if not value or not value.strip():
            if required or not self.allow_empty:
                return ValidationResult(False, "URL is required")
            return ValidationResult(True)

        value = value.strip()

        pattern = r"^(https?://)?(www\.)?[\w\-]+\.\w{2,}(/[\w\-]*)*$"
        if not re.match(pattern, value):
            return ValidationResult(False, "Invalid URL format")

        return ValidationResult(True)


class FileValidator(Validator):
    """Validator for file uploads."""

    def __init__(
        self,
        allowed_extensions: List[str] = None,
        max_size_mb: float = 10,
    ):
        self.allowed_extensions = allowed_extensions or [
            ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
            ".jpg", ".jpeg", ".png", ".gif", ".webp",
        ]
        self.max_size_mb = max_size_mb

    def validate(self, file_info: dict, required: bool = False) -> ValidationResult:
        """Validate a file."""
        if not file_info:
            if required:
                return ValidationResult(False, "File is required")
            return ValidationResult(True)

        filename = file_info.get("name", "")
        size = file_info.get("size", 0)

        ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
        if ext not in self.allowed_extensions:
            return ValidationResult(
                False, f"File type not allowed. Allowed: {', '.join(self.allowed_extensions)}"
            )

        size_mb = size / (1024 * 1024) if size else 0
        if size_mb > self.max_size_mb:
            return ValidationResult(
                False, f"File too large. Maximum size: {self.max_size_mb}MB"
            )

        return ValidationResult(True)


def get_username_validator() -> UsernameValidator:
    """Get the standard username validator."""
    return UsernameValidator(min_length=3, max_length=50)


def get_email_validator() -> EmailValidator:
    """Get the standard email validator."""
    return EmailValidator()


def get_password_validator() -> PasswordValidator:
    """Get the standard password validator."""
    return PasswordValidator(
        min_length=8,
        require_uppercase=True,
        require_lowercase=True,
        require_digit=True,
        require_special=False,
    )


def get_phone_validator() -> PhoneValidator:
    """Get the standard phone validator."""
    return PhoneValidator()


class CompositeValidator(Validator):
    """Validator that chains multiple validators."""

    def __init__(self, validators: List[Validator]):
        self.validators = validators

    def validate(self, value, required: bool = False) -> ValidationResult:
        """Validate using all composed validators."""
        for validator in self.validators:
            result = validator.validate(value, required)
            if not result.is_valid:
                return result
        return ValidationResult(True)
