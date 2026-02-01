"""Pytest configuration and fixtures for Revibe tests."""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def healthy_project(temp_dir):
    """Create a healthy project fixture with good test coverage."""
    # Main source file
    src_dir = temp_dir / "src"
    src_dir.mkdir()

    (src_dir / "app.py").write_text('''"""Main application module."""

def greet(name: str) -> str:
    """Greet a user by name."""
    if not name:
        raise ValueError("Name cannot be empty")
    return f"Hello, {name}!"


def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


def divide_numbers(a: float, b: float) -> float:
    """Divide a by b with error handling."""
    try:
        return a / b
    except ZeroDivisionError:
        raise ValueError("Cannot divide by zero")
''')

    (src_dir / "utils.py").write_text('''"""Utility functions."""

def validate_email(email: str) -> bool:
    """Validate an email address."""
    return "@" in email and "." in email


def format_date(year: int, month: int, day: int) -> str:
    """Format a date as YYYY-MM-DD."""
    return f"{year:04d}-{month:02d}-{day:02d}"
''')

    # Test files
    tests_dir = temp_dir / "tests"
    tests_dir.mkdir()

    (tests_dir / "test_app.py").write_text('''"""Tests for app module."""

import pytest
from src.app import greet, add_numbers, divide_numbers


def test_greet_valid_name():
    assert greet("World") == "Hello, World!"


def test_greet_empty_name():
    with pytest.raises(ValueError):
        greet("")


def test_add_numbers():
    assert add_numbers(2, 3) == 5


def test_add_numbers_negative():
    assert add_numbers(-1, 1) == 0


def test_divide_numbers():
    assert divide_numbers(10, 2) == 5.0


def test_divide_by_zero():
    with pytest.raises(ValueError):
        divide_numbers(10, 0)
''')

    (tests_dir / "test_utils.py").write_text('''"""Tests for utils module."""

from src.utils import validate_email, format_date


def test_validate_email_valid():
    assert validate_email("test@example.com") is True


def test_validate_email_invalid():
    assert validate_email("notanemail") is False


def test_format_date():
    assert format_date(2026, 1, 31) == "2026-01-31"
''')

    return temp_dir


@pytest.fixture
def bloated_project(temp_dir):
    """Create a bloated project with many issues."""
    src_dir = temp_dir / "src"
    src_dir.mkdir()

    # Verbose naming
    (src_dir / "very_long_module_name_that_handles_user_authentication.py").write_text('''"""A module with overly verbose naming."""

def handle_user_authentication_with_password_and_two_factor_verification(username, password, two_factor_code):
    """This function has an extremely long name that is typical of AI-generated code."""
    # TODO: Implement actual authentication
    pass


def validate_user_input_and_sanitize_before_database_insertion(user_input):
    """Another verbose function name."""
    # FIXME: This needs proper sanitization
    pass


class UserAuthenticationManagerWithSessionHandling:
    """A class with an overly verbose name."""
    
    def __init__(self):
        pass
    
    def authenticate_user_and_create_session_token(self):
        pass
''')

    # Duplicate files
    (src_dir / "helpers.py").write_text('''"""Helper functions."""

def format_name(first, last):
    return f"{first} {last}"

def calculate_total(items):
    return sum(items)
''')

    (src_dir / "helpers_v2.py").write_text('''"""Helper functions."""

def format_name(first, last):
    return f"{first} {last}"

def calculate_total(items):
    return sum(items)
''')

    # Many files with little content
    utils_dir = src_dir / "utils"
    utils_dir.mkdir()

    for i in range(10):
        (utils_dir / f"util_{i}.py").write_text(f'''"""Utility {i}."""

def utility_function_{i}():
    pass

class UtilityClass{i}:
    pass
''')

    # Over-commented file
    (src_dir / "over_commented.py").write_text('''"""This module is over-commented."""

# Import the os module for operating system operations
import os  # os module
# Import the sys module for system operations
import sys  # sys module

# Define a function that prints hello
# This function takes no arguments
# It returns None
def print_hello():
    # Print the word hello
    print("hello")  # prints hello
    # Return nothing
    return None  # returns None
''')

    return temp_dir


@pytest.fixture
def no_tests_project(temp_dir):
    """Create a project with no test files."""
    src_dir = temp_dir / "src"
    src_dir.mkdir()

    (src_dir / "main.py").write_text('''"""Main module without tests."""

def process_payment(amount, card_number):
    """Process a payment - no error handling!"""
    return {"status": "success", "amount": amount}


def authenticate_user(username, password):
    """Authenticate user - no error handling!"""
    return True


def delete_user(user_id):
    """Delete a user from the database."""
    return True
''')

    (src_dir / "api.py").write_text('''"""API endpoints."""

def get_users():
    return []

def create_user(data):
    return {"id": 1, **data}

def update_user(user_id, data):
    return {"id": user_id, **data}

def delete_user(user_id):
    return True
''')

    (src_dir / "models.py").write_text('''"""Data models."""

class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
    
    def to_dict(self):
        return {"name": self.name, "email": self.email}


class Order:
    def __init__(self, user_id, items):
        self.user_id = user_id
        self.items = items
    
    def calculate_total(self):
        return sum(item["price"] for item in self.items)
''')

    return temp_dir


@pytest.fixture
def mixed_languages_project(temp_dir):
    """Create a project with multiple programming languages."""
    # Python
    py_dir = temp_dir / "python"
    py_dir.mkdir()
    (py_dir / "app.py").write_text('''"""Python app."""

def main():
    print("Hello from Python")
''')

    # JavaScript
    js_dir = temp_dir / "javascript"
    js_dir.mkdir()
    (js_dir / "app.js").write_text('''// JavaScript app

function main() {
    console.log("Hello from JavaScript");
}

const greet = (name) => {
    return `Hello, ${name}!`;
};
''')

    # TypeScript
    ts_dir = temp_dir / "typescript"
    ts_dir.mkdir()
    (ts_dir / "app.ts").write_text('''// TypeScript app

function main(): void {
    console.log("Hello from TypeScript");
}

const greet = (name: string): string => {
    return `Hello, ${name}!`;
};
''')

    # Go
    go_dir = temp_dir / "golang"
    go_dir.mkdir()
    (go_dir / "main.go").write_text('''package main

import "fmt"

func main() {
    fmt.Println("Hello from Go")
}

func greet(name string) string {
    return "Hello, " + name + "!"
}
''')

    return temp_dir


@pytest.fixture
def empty_project(temp_dir):
    """Create an empty project directory."""
    return temp_dir
