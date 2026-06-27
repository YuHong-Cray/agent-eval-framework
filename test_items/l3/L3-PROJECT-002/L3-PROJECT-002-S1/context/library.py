"""Monolithic Library Management System ¡ª needs refactoring."""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timedelta


@dataclass
class Book:
    id: int
    title: str
    author: str
    isbn: str
    available: bool = True


@dataclass
class Member:
    id: int
    name: str
    email: str
    joined: str
    active: bool = True
    fines_due: float = 0.0


@dataclass
class Loan:
    id: int
    book_id: int
    member_id: int
    borrowed: str
    due: str
    returned: Optional[str] = None


class Library:
    """Monolithic class handling everything."""

    def __init__(self):
        self.books: list[Book] = []
        self.members: list[Member] = []
        self.loans: list[Loan] = []
        self._next_book_id = 1
        self._next_member_id = 1
        self._next_loan_id = 1

    # ©¤©¤ Book operations ©¤©¤
    def add_book(self, title: str, author: str, isbn: str) -> Book:
        b = Book(id=self._next_book_id, title=title, author=author, isbn=isbn)
        self._next_book_id += 1
        self.books.append(b)
        return b

    def find_book(self, book_id: int) -> Optional[Book]:
        for b in self.books:
            if b.id == book_id:
                return b
        return None

    def search_books(self, query: str) -> list[Book]:
        q = query.lower()
        return [b for b in self.books if q in b.title.lower() or q in b.author.lower()]

    def list_available_books(self) -> list[Book]:
        return [b for b in self.books if b.available]

    # ©¤©¤ Member operations ©¤©¤
    def register_member(self, name: str, email: str) -> Member:
        m = Member(id=self._next_member_id, name=name, email=email, joined=str(datetime.now().date()))
        self._next_member_id += 1
        self.members.append(m)
        return m

    def find_member(self, member_id: int) -> Optional[Member]:
        for m in self.members:
            if m.id == member_id:
                return m
        return None

    def deactivate_member(self, member_id: int) -> bool:
        m = self.find_member(member_id)
        if m:
            m.active = False
            return True
        return False

    # ©¤©¤ Loan operations ©¤©¤
    def borrow_book(self, book_id: int, member_id: int) -> Optional[Loan]:
        book = self.find_book(book_id)
        member = self.find_member(member_id)
        if not book or not member:
            return None
        if not book.available:
            return None
        if not member.active:
            return None
        if member.fines_due > 0:
            return None
        today = str(datetime.now().date())
        due = str(datetime.now().date() + timedelta(days=14))
        loan = Loan(id=self._next_loan_id, book_id=book_id, member_id=member_id, borrowed=today, due=due)
        self._next_loan_id += 1
        book.available = False
        self.loans.append(loan)
        return loan

    def return_book(self, loan_id: int) -> Optional[float]:
        """Returns the book. Returns fine amount if overdue, or 0."""
        loan = None
        for l in self.loans:
            if l.id == loan_id and l.returned is None:
                loan = l
                break
        if not loan:
            return None
        book = self.find_book(loan.book_id)
        if book:
            book.available = True
        loan.returned = str(datetime.now().date())
        due_date = datetime.strptime(loan.due, "%Y-%m-%d")
        today = datetime.now().date()
        if today > due_date.date():
            days_late = (today - due_date.date()).days
            fine = days_late * 0.50
            member = self.find_member(loan.member_id)
            if member:
                member.fines_due += fine
            return fine
        return 0.0

    def get_member_loans(self, member_id: int) -> list[Loan]:
        return [l for l in self.loans if l.member_id == member_id]

    def get_overdue_loans(self) -> list[Loan]:
        today = datetime.now().date()
        overdue = []
        for l in self.loans:
            if l.returned is None:
                due = datetime.strptime(l.due, "%Y-%m-%d").date()
                if today > due:
                    overdue.append(l)
        return overdue

    # ©¤©¤ Reporting ©¤©¤
    def generate_report(self) -> dict:
        total_books = len(self.books)
        available = len(self.list_available_books())
        total_members = len(self.members)
        active_loans = len([l for l in self.loans if l.returned is None])
        total_fines = sum(m.fines_due for m in self.members)
        overdue = self.get_overdue_loans()
        return {
            "total_books": total_books,
            "available_books": available,
            "total_members": total_members,
            "active_loans": active_loans,
            "overdue_loans": len(overdue),
            "total_fines_due": round(total_fines, 2),
        }
