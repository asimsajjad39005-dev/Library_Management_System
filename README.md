# Library Management System

A fully object-oriented Library Management System built in Python.

## Features
- Add, remove, and search books (by title, author, or genre)
- Register basic and premium members
- Borrow and return books with due dates
- Automatic overdue fine calculation (Rs. 10/day after 14 days)
- JSON file persistence (data survives restarts)
- Command-line interface (CLI) menu
- 10 unit tests using pytest

## How to Run

### Run the application
python Library.py

### Run the unit tests
python -m pytest Test.py -v

## Classes
- Book — title, author, isbn, genre, copies_total, copies_available, published_year
- Member — basic member (max 2 books)
- PremiumMember(Member) — inherits Member, allows up to 5 books
- Librarian — staff record
- Transaction — tracks each borrow/return event and fines
- Library — main class with all core logic

## Requirements
- Python 3.x
- pytest (pip install pytest)

## Approach & Design Decisions

**Why one main file?**
I kept all classes (`Book`, `Member`, `PremiumMember`, `Librarian`, `Transaction`, `Library`) in a single `Library.py` file to keep the project simple and easy to navigate, since the project size didn't require splitting into multiple modules.

**Why inheritance for PremiumMember?**
Instead of duplicating logic, `PremiumMember` inherits from `Member` and only overrides the `borrow_limit()` and `validate_borrow()` methods. This follows the OOP principle of code reuse — both member types share the same core attributes and behavior, differing only in their borrowing limit (2 vs 5 books).

**Why a custom LibraryError class?**
A single custom exception (`LibraryError`) is used for all error cases (duplicate books, member not found, borrow limit exceeded, etc.) instead of Python's generic exceptions. This makes errors easier to catch and handle consistently throughout the CLI.

**Why JSON for persistence?**
JSON was chosen over a database because it's lightweight, human-readable, and requires no extra setup or dependencies — ideal for a small-scale system like this. Every write operation (`add_book`, `borrow_book`, `return_book`, etc.) immediately saves to `library_data.json`, so data is never lost even if the program closes unexpectedly.

**Why a separate Transaction class?**
Rather than tracking borrow history inside the `Member` or `Book` class, a dedicated `Transaction` class records each borrow/return event with its own dates and fine amount. This keeps a clean audit trail and makes it easy to calculate overdue fines and generate reports without modifying the core Book/Member objects.

**Why unit tests with pytest?**
Pytest was used because it's simple, requires minimal boilerplate, and integrates well with Python. The 10 tests cover the core business logic (adding/searching books, borrow limits, overdue fines, and JSON persistence) to ensure the system behaves correctly even after future changes.
