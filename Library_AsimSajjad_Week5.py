import json
import os
from datetime import date, timedelta

DATA_FILE = "library_data.json"

class LibraryError(Exception):
    """Base exception for all Library Management System errors."""
    pass

class Book:
    """
    Represents a book in the library.

    Attributes:
        title (str): Title of the book.
        author (str): Author's name.
        isbn (str): Unique ISBN identifier.
        genre (str): Genre/category of the book.
        copies_total (int): Total copies owned by the library.
        copies_available (int): Copies currently on the shelf.
        published_year (int): Year the book was published.
    """

    def __init__(self, title, author, isbn, genre, copies_total, copies_available, published_year):
        self.title = title
        self.author = author
        self.isbn = isbn
        self.genre = genre
        self.copies_total = copies_total
        self.copies_available = copies_available
        self.published_year = published_year

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, d):
        return cls(
            d["title"], d["author"], d["isbn"], d["genre"],
            d["copies_total"], d["copies_available"], d["published_year"]
        )

    def __str__(self):
        return (f"[{self.isbn}] {self.title} by {self.author} ({self.published_year})"
                f" | Genre: {self.genre} | Available: {self.copies_available}/{self.copies_total}")


class Member:
    """
    Represents a basic library member.

    Attributes:
        member_id (str): Unique member identifier.
        name (str): Full name of the member.
        email (str): Email address.
        phone (str): Phone number.
        membership_type (str): 'basic' or 'premium'.
        join_date (str): ISO date string when member joined.
        borrowed_books (list): List of ISBNs currently borrowed.
    """

    def __init__(self, member_id, name, email, phone, membership_type="basic",
                join_date=None, borrowed_books=None):
        self.member_id = member_id
        self.name = name
        self.email = email
        self.phone = phone
        self.membership_type = membership_type
        self.join_date = join_date or date.today().isoformat()
        self.borrowed_books = borrowed_books or []

    def borrow_limit(self):
        """Return the maximum number of books this member can borrow."""
        return 2

    def validate_borrow(self, isbn, book_title):
        """
        Check if this member is allowed to borrow a book.

        Raises:
            LibraryError: If already borrowed or limit reached.
        """
        if isbn in self.borrowed_books:
            raise LibraryError(f"You already have '{book_title}' borrowed.")
        if len(self.borrowed_books) >= self.borrow_limit():
            raise LibraryError(
                f"'{self.name}' has reached the borrow limit of {self.borrow_limit()} book(s)."
            )

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, d):
        if d["membership_type"] == "premium":
            return PremiumMember(
                d["member_id"], d["name"], d["email"], d["phone"],
                join_date=d["join_date"], borrowed_books=d["borrowed_books"]
            )
        return cls(
            d["member_id"], d["name"], d["email"], d["phone"],
            join_date=d["join_date"], borrowed_books=d["borrowed_books"]
        )

    def __str__(self):
        return (f"[{self.member_id}] {self.name} ({self.membership_type})"
                f" | Borrowed: {len(self.borrowed_books)}/{self.borrow_limit()}"
                f" | Email: {self.email}")


class PremiumMember(Member):
    """
    A premium library member with a higher borrow limit.

    Inherits all attributes from Member and overrides borrow validation
    to allow up to 5 simultaneous borrows instead of 2.

    Attributes:
        member_id (str): Unique member identifier.
        name (str): Full name of the member.
        email (str): Email address.
        phone (str): Phone number.
        membership_type (str): Always 'premium' for this class.
        join_date (str): ISO date string when member joined.
        borrowed_books (list): List of ISBNs currently borrowed (max 5).
    """

    def __init__(self, member_id, name, email, phone,
                join_date=None, borrowed_books=None):
        super().__init__(member_id, name, email, phone,
                        membership_type="premium",
                        join_date=join_date,
                        borrowed_books=borrowed_books)

    def borrow_limit(self):
        """Premium members can borrow up to 5 books."""
        return 5

    def validate_borrow(self, isbn, book_title):
        """
        Check borrow eligibility with premium limit of 5.

        Raises:
            LibraryError: If already borrowed or limit of 5 reached.
        """
        if isbn in self.borrowed_books:
            raise LibraryError(f"You already have '{book_title}' borrowed.")
        if len(self.borrowed_books) >= self.borrow_limit():
            raise LibraryError(
                f"'{self.name}' has reached the premium borrow limit of {self.borrow_limit()} book(s)."
            )


class Transaction:
    """
    Records a single borrow/return event.

    Attributes:
        txn_id (str): Unique transaction ID (e.g. 'TXN-0001').
        member_id (str): ID of the member who borrowed the book.
        isbn (str): ISBN of the borrowed book.
        borrow_date (str): ISO date the book was borrowed.
        due_date (str): ISO date the book is due back (14 days after borrow).
        return_date (str|None): ISO date returned; None if still borrowed.
        fine (float): Fine in Rs. charged on return (Rs. 10/day overdue).
        status (str): 'borrowed' or 'returned'.
    """

    def __init__(self, txn_id, member_id, isbn, borrow_date, due_date):
        self.txn_id = txn_id
        self.member_id = member_id
        self.isbn = isbn
        self.borrow_date = borrow_date
        self.due_date = due_date
        self.return_date = None
        self.fine = 0.0
        self.status = "borrowed"

    def is_overdue(self):
        """Return True if the book is not returned and past its due date."""
        return self.return_date is None and date.today() > date.fromisoformat(self.due_date)

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, d):
        t = cls(d["txn_id"], d["member_id"], d["isbn"], d["borrow_date"], d["due_date"])
        t.return_date = d["return_date"]
        t.fine = d["fine"]
        t.status = d["status"]
        return t

    def __str__(self):
        return (f"[{self.txn_id}] Member: {self.member_id} | ISBN: {self.isbn}"
                f" | Due: {self.due_date} | Status: {self.status.upper()}"
                f" | Fine: Rs. {self.fine:.2f}")


class Librarian:
    """
    Represents a library staff member.

    Attributes:
        employee_id (str): Unique staff identifier.
        name (str): Full name of the librarian.
        email (str): Work email address.
        shift (str): Assigned shift — 'morning', 'evening', or 'night'.
    """

    def __init__(self, employee_id, name, email, shift):
        self.employee_id = employee_id
        self.name = name
        self.email = email
        self.shift = shift

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, d):
        return cls(d["employee_id"], d["name"], d["email"], d["shift"])

    def __str__(self):
        return f"[{self.employee_id}] {self.name} | Shift: {self.shift} | Email: {self.email}"

class Library:
    """
    Central class representing the library and all its operations.

    Attributes:
        name (str): Name of the library.
        address (str): Physical address of the library.
        books (list): List of Book objects in the catalogue.
        members (list): List of registered Member objects.
        librarians (list): List of Librarian staff objects.
        transactions (list): Full history of Transaction records.
    """

    def __init__(self, name="City Library", address="123 Main St"):
        self.name = name
        self.address = address
        self.books = []
        self.members = []
        self.librarians = []
        self.transactions = []
        self._counter = 0

    def add_book(self, book):
        """
        Add a new book to the library catalogue.

        Args:
            book (Book): The book to add.

        Raises:
            LibraryError: If a book with the same ISBN already exists.
        """
        for b in self.books:
            if b.isbn == book.isbn:
                raise LibraryError(f"A book with ISBN '{book.isbn}' already exists.")
        self.books.append(book)
        self._save()
        print(f" '{book.title}' added.")

    def remove_book(self, isbn):
        """
        Remove a book from the catalogue by ISBN.

        Args:
            isbn (str): ISBN of the book to remove.

        Raises:
            LibraryError: If the book is not found or copies are still borrowed.
        """
        book = self._find_book(isbn)
        if book.copies_available < book.copies_total:
            raise LibraryError(f"Cannot remove '{book.title}' — some copies are still borrowed.")
        self.books.remove(book)
        self._save()
        print(f" '{book.title}' removed.")

    def search_books(self, query):
        """
        Search books by title, author, or genre (case-insensitive).

        Args:
            query (str): The search term.

        Returns:
            list: Matching Book objects.
        """
        q = query.lower()
        return [b for b in self.books
                if q in b.title.lower()
                or q in b.author.lower()
                or q in b.genre.lower()]

    def register_member(self, member):
        """
        Register a new library member.

        Args:
            member (Member): The member to register.

        Raises:
            LibraryError: If the member ID already exists.
        """
        for m in self.members:
            if m.member_id == member.member_id:
                raise LibraryError(f"Member ID '{member.member_id}' already exists.")
        self.members.append(member)
        self._save()
        print(f"Member '{member.name}' registered.")

    # ── Borrow / Return ───────────────────────

    def borrow_book(self, member_id, isbn):
        """
        Issue a book to a member.

        Checks availability, validates borrow rules, decrements copies_available,
        updates member's borrowed list, and creates a Transaction record.

        Args:
            member_id (str): ID of the borrowing member.
            isbn (str): ISBN of the book to borrow.

        Returns:
            Transaction: The newly created transaction.

        Raises:
            LibraryError: If member/book not found, limit exceeded, or unavailable.
        """
        member = self._find_member(member_id)
        book = self._find_book(isbn)

        member.validate_borrow(isbn, book.title)  # raises if invalid

        if book.copies_available <= 0:
            raise LibraryError(f"No copies of '{book.title}' are currently available.")

        book.copies_available -= 1
        member.borrowed_books.append(isbn)

        self._counter += 1
        today = date.today()
        due = today + timedelta(days=14)
        txn = Transaction(
            f"TXN-{self._counter:04d}", member_id, isbn,
            today.isoformat(), due.isoformat()
        )
        self.transactions.append(txn)
        self._save()
        print(f"'{book.title}' borrowed by {member.name}. Due: {due}.")
        return txn

    def return_book(self, member_id, isbn):
        """
        Process the return of a borrowed book.

        Calculates overdue fine at Rs. 10/day after 14 days, updates the
        transaction, restores copies_available, and removes from member's list.

        Args:
            member_id (str): ID of the returning member.
            isbn (str): ISBN of the book being returned.

        Returns:
            Transaction: The updated transaction record.

        Raises:
            LibraryError: If member/book not found or book was not borrowed.
        """
        member = self._find_member(member_id)
        book = self._find_book(isbn)

        if isbn not in member.borrowed_books:
            raise LibraryError(f"'{member.name}' has not borrowed '{book.title}'.")

        txn = next(
            (t for t in self.transactions
            if t.member_id == member_id and t.isbn == isbn and t.return_date is None),
            None
        )
        if not txn:
            raise LibraryError("Active transaction not found.")

        overdue_days = (date.today() - date.fromisoformat(txn.due_date)).days
        fine = max(0, overdue_days * 10)

        txn.return_date = date.today().isoformat()
        txn.fine = fine
        txn.status = "returned"

        book.copies_available += 1
        member.borrowed_books.remove(isbn)
        self._save()

        if fine:
            print(f"'{book.title}' returned by {member.name}. ⚠️  Fine: Rs. {fine}")
        else:
            print(f"'{book.title}' returned by {member.name}. No fine.")
        return txn

    def get_overdue_books(self):
        """
        Return all transactions where the book is overdue and not yet returned.

        Returns:
            list: Overdue Transaction objects.
        """
        return [t for t in self.transactions if t.is_overdue()]

    def generate_report(self):
        """
        Print a formatted summary of the library's current state.

        Includes book counts, member counts, active borrows,
        overdue items, and fines collected.
        """
        overdue = self.get_overdue_books()
        active  = [t for t in self.transactions if t.return_date is None]
        fines   = sum(t.fine for t in self.transactions)

        print(f"""
    {'='*48}
    {self.name.upper()} — LIBRARY REPORT
    {self.address}
    {'='*48}
    Books (unique titles)    : {len(self.books)}
    Total copies owned       : {sum(b.copies_total for b in self.books)}
    Copies available         : {sum(b.copies_available for b in self.books)}
    Copies borrowed          : {sum(b.copies_total - b.copies_available for b in self.books)}
    {'='*48}
    Registered members       : {len(self.members)}
        Basic                  : {sum(1 for m in self.members if m.membership_type == 'basic')}
        Premium                : {sum(1 for m in self.members if m.membership_type == 'premium')}
    {'='*48}
    Total transactions       : {len(self.transactions)}
    Active borrows           : {len(active)}
    Overdue borrows          : {len(overdue)}
    Fines collected          : Rs. {fines:.2f}
{'='*48}""")

        if overdue:
            print("\nOVERDUE LIST:")
            for t in overdue:
                days_late = (date.today() - date.fromisoformat(t.due_date)).days
                print(f"    • TXN {t.txn_id} | Member: {t.member_id}"
                    f" | ISBN: {t.isbn} | {days_late} day(s) late"
                    f" | Fine: Rs. {days_late * 10}")
        print()

    # ── Helpers ───────────────────────────────

    def _find_book(self, isbn):
        for b in self.books:
            if b.isbn == isbn:
                return b
        raise LibraryError(f"Book with ISBN '{isbn}' not found.")

    def _find_member(self, member_id):
        for m in self.members:
            if m.member_id == member_id:
                return m
        raise LibraryError(f"Member with ID '{member_id}' not found.")

    def _save(self):
        """Persist all library data to a JSON file."""
        data = {
            "name": self.name,
            "address": self.address,
            "counter": self._counter,
            "books": [b.to_dict() for b in self.books],
            "members": [m.to_dict() for m in self.members],
            "librarians": [l.to_dict() for l in self.librarians],
            "transactions": [t.to_dict() for t in self.transactions],
        }
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls):
        """
        Load library data from JSON and reconstruct all objects.

        Returns:
            Library: Fully restored Library instance.
        """
        if not os.path.exists(DATA_FILE):
            print("No saved data found — starting fresh.")
            return cls()
        with open(DATA_FILE) as f:
            data = json.load(f)
        lib = cls(data["name"], data["address"])
        lib._counter   = data.get("counter", 0)
        lib.books       = [Book.from_dict(b)        for b in data.get("books", [])]
        lib.members     = [Member.from_dict(m)      for m in data.get("members", [])]
        lib.librarians  = [Librarian.from_dict(l)   for l in data.get("librarians", [])]
        lib.transactions= [Transaction.from_dict(t) for t in data.get("transactions", [])]
        return lib


def pause():
    input("\nPress Enter to continue...")

def main():
    lib = Library.load()
    print(f"\nWelcome to {lib.name}!")

    while True:
        print("""
══════════════════════════════
MAIN MENU
══════════════════════════════
1.  Add Book
2.  Remove Book
3.  Search Books
4.  List All Books
5.  Register Member
6.  List Members
7.  Borrow Book
8.  Return Book
9.  View Overdue Books
10. Generate Report
11.  Exit
══════════════════════════════""")

        choice = input("Choose: ").strip()

        try:
            if choice == "1":
                title  = input("Title          : ")
                author = input("Author         : ")
                isbn   = input("ISBN           : ")
                genre  = input("Genre          : ")
                copies = int(input("Copies         : "))
                year   = int(input("Published Year : "))
                lib.add_book(Book(title, author, isbn, genre, copies, copies, year))

            elif choice == "2":
                isbn = input("ISBN to remove: ")
                lib.remove_book(isbn)

            elif choice == "3":
                query = input("Search (title / author / genre): ")
                results = lib.search_books(query)
                print(f"\n  {len(results)} result(s) found:")
                for b in results:
                    print(f"  {b}")

            elif choice == "4":
                if lib.books:
                    for b in lib.books: print(f"  {b}")
                else:
                    print("  No books in library.")

            elif choice == "5":
                mid   = input("Member ID      : ")
                name  = input("Name           : ")
                email = input("Email          : ")
                phone = input("Phone          : ")
                mtype = input("Type (basic / premium): ").strip().lower()
                if mtype == "premium":
                    lib.register_member(PremiumMember(mid, name, email, phone))
                else:
                    lib.register_member(Member(mid, name, email, phone))

            elif choice == "6":
                if lib.members:
                    for m in lib.members: print(f"  {m}")
                else:
                    print("  No members registered.")

            elif choice == "7":
                mid  = input("Member ID : ")
                isbn = input("Book ISBN : ")
                lib.borrow_book(mid, isbn)

            elif choice == "8":
                mid  = input("Member ID : ")
                isbn = input("Book ISBN : ")
                lib.return_book(mid, isbn)

            elif choice == "9":
                overdue = lib.get_overdue_books()
                if overdue:
                    print(f"\n{len(overdue)} overdue borrow(s):")
                    for t in overdue: print(f"  {t}")
                else:
                    print("No overdue books.")

            elif choice == "10":
                lib.generate_report()

            elif choice == "0":
                print("\nGoodbye!\n")
                break

            else:
                print("  Invalid choice.")

        except LibraryError as e:
            print(f"{e}")
        except ValueError:
            print("Please enter a valid number.")

        pause()

if __name__ == "__main__":
    main()