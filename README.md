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
