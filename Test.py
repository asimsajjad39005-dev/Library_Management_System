
import sys, os, pytest, json
from datetime import date, timedelta
sys.path.insert(0, os.path.dirname(__file__))

from Library import Library, Book, Member, PremiumMember, Transaction, Librarian, LibraryError

def make_lib():
    l = Library("Test Library", "1 Test St")
    l._save = lambda: None
    return l

def make_book(isbn="B001", copies=3):
    return Book("Clean Code", "Robert Martin", isbn, "Technology", copies, copies, 2008)

def make_member(mid="M001"):
    return Member(mid, "Alice", "alice@test.com", "0300-000")

def make_premium(mid="M002"):
    return PremiumMember(mid, "Bob", "bob@test.com", "0300-111")


# 1 — Add book
def test_add_book():
    l = make_lib()
    l.add_book(make_book())
    assert len(l.books) == 1
    assert l.books[0].isbn == "B001"

# 2 — Duplicate ISBN raises LibraryError
def test_duplicate_book_raises():
    l = make_lib()
    l.add_book(make_book())
    with pytest.raises(LibraryError):
        l.add_book(make_book())

# 3 — Search by title, author, genre
def test_search_books():
    l = make_lib()
    l.add_book(make_book())
    l.add_book(Book("Dune", "Frank Herbert", "B002", "Sci-Fi", 2, 2, 1965))
    assert len(l.search_books("Robert"))     == 1   # by author
    assert len(l.search_books("Sci-Fi"))     == 1   # by genre
    assert len(l.search_books("Clean Code")) == 1   # by title
    assert len(l.search_books("xyz"))        == 0   # no match

# 4 — Borrow creates transaction, decrements copies
def test_borrow_creates_transaction():
    l = make_lib()
    l.books.append(make_book())
    l.members.append(make_member())
    txn = l.borrow_book("M001", "B001")
    assert txn.status == "borrowed"
    assert l.books[0].copies_available == 2
    assert "B001" in l.members[0].borrowed_books

# 5 — Basic member borrow limit = 2
def test_basic_member_limit():
    l = make_lib()
    for i in range(3): l.books.append(make_book(isbn=f"B00{i}"))
    l.members.append(make_member())
    l.borrow_book("M001", "B000")
    l.borrow_book("M001", "B001")
    with pytest.raises(LibraryError):
        l.borrow_book("M001", "B002")

# 6 — Premium member borrow limit = 5
def test_premium_member_limit():
    l = make_lib()
    for i in range(6): l.books.append(make_book(isbn=f"B00{i}"))
    l.members.append(make_premium())
    for i in range(5):
        l.borrow_book("M002", f"B00{i}")
    with pytest.raises(LibraryError):
        l.borrow_book("M002", "B005")

# 7 — Return book restores availability, marks transaction returned
def test_return_book():
    l = make_lib()
    l.books.append(make_book())
    l.members.append(make_member())
    l.borrow_book("M001", "B001")
    txn = l.return_book("M001", "B001")
    assert txn.status == "returned"
    assert txn.return_date == date.today().isoformat()
    assert l.books[0].copies_available == 3
    assert "B001" not in l.members[0].borrowed_books

# 8 — Fine = Rs. 10 per overdue day after 14 days
def test_overdue_fine():
    t = Transaction("T1", "M1", "B1",
        (date.today() - timedelta(days=20)).isoformat(),
        (date.today() - timedelta(days=6)).isoformat())
    assert t.is_overdue() is True
    overdue_days = (date.today() - date.fromisoformat(t.due_date)).days
    assert overdue_days * 10 == 60   # 6 days overdue × Rs. 10

# 9 — get_overdue_books returns only open, past-due transactions
def test_get_overdue_books():
    l = make_lib()
    t_overdue = Transaction("T1", "M1", "B1",
        (date.today() - timedelta(20)).isoformat(),
        (date.today() - timedelta(6)).isoformat())
    t_ok = Transaction("T2", "M2", "B2",
        date.today().isoformat(),
        (date.today() + timedelta(14)).isoformat())
    t_returned = Transaction("T3", "M3", "B3",
        (date.today() - timedelta(20)).isoformat(),
        (date.today() - timedelta(6)).isoformat())
    t_returned.return_date = date.today().isoformat()
    l.transactions = [t_overdue, t_ok, t_returned]
    result = l.get_overdue_books()
    assert len(result) == 1
    assert result[0].txn_id == "T1"

# 10 — JSON round-trip reconstructs correct types
def test_json_round_trip(tmp_path):
    import Library as ls
    filepath = str(tmp_path / "data.json")
    l = Library("Persist Library", "42 Save Ave")
    l.books.append(make_book())
    l.members.append(make_premium())
    l.librarians.append(Librarian("E001", "Sara", "sara@lib.com", "morning"))
    data = {
        "name": l.name, "address": l.address, "counter": 0,
        "books":       [b.to_dict() for b in l.books],
        "members":     [m.to_dict() for m in l.members],
        "librarians":  [lib.to_dict() for lib in l.librarians],
        "transactions": []
    }
    with open(filepath, "w") as f: json.dump(data, f)
    ls.DATA_FILE = filepath
    restored = ls.Library.load()
    assert restored.name == "Persist Library"
    assert restored.books[0].published_year == 2008
    assert isinstance(restored.members[0], PremiumMember)
    assert restored.members[0].borrow_limit() == 5
    assert restored.librarians[0].employee_id == "E001"