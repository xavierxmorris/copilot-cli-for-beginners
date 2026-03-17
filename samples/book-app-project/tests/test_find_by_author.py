"""Edge-case tests for BookCollection.find_by_author.

Covers: hyphenated names, multiple first names, empty string,
and accented/Unicode characters.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import books
from books import BookCollection


@pytest.fixture(autouse=True)
def use_temp_data_file(tmp_path, monkeypatch):
    temp_file = tmp_path / "data.json"
    temp_file.write_text("[]")
    monkeypatch.setattr(books, "DATA_FILE", str(temp_file))


@pytest.fixture
def collection():
    return BookCollection()


# --- Hyphenated author names ---


class TestHyphenatedAuthors:

    def test_exact_match(self, collection):
        collection.add_book("Nausea", "Jean-Paul Sartre", 1938)
        results = collection.find_by_author("Jean-Paul Sartre")
        assert len(results) == 1
        assert results[0].title == "Nausea"

    def test_case_insensitive(self, collection):
        collection.add_book("Nausea", "Jean-Paul Sartre", 1938)
        assert len(collection.find_by_author("jean-paul sartre")) == 1

    def test_partial_hyphenated_name_matches(self, collection):
        collection.add_book("Nausea", "Jean-Paul Sartre", 1938)
        # Partial match now supported
        assert len(collection.find_by_author("Jean-Paul")) == 1
        assert len(collection.find_by_author("Sartre")) == 1

    def test_double_hyphen(self, collection):
        collection.add_book("Test", "Anne-Marie Claire-Dubois", 2000)
        assert len(collection.find_by_author("Anne-Marie Claire-Dubois")) == 1


# --- Authors with multiple first names ---


class TestMultipleFirstNames:

    def test_three_part_name(self, collection):
        collection.add_book("The Hobbit", "John Ronald Reuel Tolkien", 1937)
        results = collection.find_by_author("John Ronald Reuel Tolkien")
        assert len(results) == 1

    def test_case_insensitive_multipart(self, collection):
        collection.add_book("The Hobbit", "John Ronald Reuel Tolkien", 1937)
        assert len(collection.find_by_author("john ronald reuel tolkien")) == 1

    def test_partial_multipart_matches(self, collection):
        collection.add_book("The Hobbit", "John Ronald Reuel Tolkien", 1937)
        # Partial match now supported
        assert len(collection.find_by_author("Tolkien")) == 1
        # "John Tolkien" is NOT a contiguous substring, so no match
        assert collection.find_by_author("John Tolkien") == []

    def test_initials_style_name(self, collection):
        collection.add_book("The Hobbit", "J.R.R. Tolkien", 1937)
        assert len(collection.find_by_author("J.R.R. Tolkien")) == 1
        assert len(collection.find_by_author("j.r.r. tolkien")) == 1


# --- Empty string as author ---


class TestEmptyAuthor:

    def test_empty_string_matches_all(self, collection):
        collection.add_book("Dune", "Frank Herbert", 1965)
        # Empty string is a substring of every string
        assert len(collection.find_by_author("")) == 1

    def test_empty_string_matches_empty_author(self, collection):
        collection.add_book("Anonymous Work", "", 1800)
        results = collection.find_by_author("")
        assert len(results) == 1
        assert results[0].title == "Anonymous Work"

    def test_whitespace_does_not_match_empty(self, collection):
        collection.add_book("Anonymous Work", "", 1800)
        # " " != "" after .lower(), so no match
        assert collection.find_by_author(" ") == []


# --- Accented / Unicode characters ---


class TestAccentedAuthors:

    @pytest.mark.parametrize("author,query", [
        ("Gabriel García Márquez", "gabriel garcía márquez"),
        ("José Saramago", "josé saramago"),
        ("Stanisław Lem", "stanisław lem"),
        ("Ngũgĩ wa Thiong'o", "ngũgĩ wa thiong'o"),
    ])
    def test_accented_case_insensitive(self, collection, author, query):
        collection.add_book("Book", author, 2000)
        assert len(collection.find_by_author(query)) == 1

    def test_cjk_author(self, collection):
        collection.add_book("A Personal Matter", "大江健三郎", 1964)
        assert len(collection.find_by_author("大江健三郎")) == 1

    def test_arabic_author(self, collection):
        collection.add_book("Book", "نجيب محفوظ", 1988)
        assert len(collection.find_by_author("نجيب محفوظ")) == 1

    def test_accent_mismatch_no_result(self, collection):
        """Searching without accents should NOT match accented author."""
        collection.add_book("Book", "Gabriel García Márquez", 1967)
        assert collection.find_by_author("Gabriel Garcia Marquez") == []

    def test_multiple_accented_books_same_author(self, collection):
        collection.add_book("Book A", "José Saramago", 1995)
        collection.add_book("Book B", "José Saramago", 1998)
        assert len(collection.find_by_author("José Saramago")) == 2
