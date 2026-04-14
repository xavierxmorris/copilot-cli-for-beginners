"""Tests for the export module."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import books
from books import Book, StorageError
import export


@pytest.fixture(autouse=True)
def use_temp_data_file(tmp_path, monkeypatch):
    temp_file = tmp_path / "data.json"
    temp_file.write_text("[]")
    monkeypatch.setattr(books, "DATA_FILE", str(temp_file))


@pytest.fixture
def sample_books():
    return [
        Book("Dune", "Frank Herbert", 1965, read=True),
        Book("1984", "George Orwell", 1949, read=False),
    ]


class TestBooksToCsvString:
    def test_empty_list_returns_header_only(self):
        result = export.books_to_csv_string([])
        lines = result.strip().split("\n")
        assert len(lines) == 1
        assert lines[0] == "title,author,year,read"

    def test_single_book_correct_csv_line(self):
        book = Book("Dune", "Frank Herbert", 1965, read=True)
        result = export.books_to_csv_string([book])
        lines = result.strip().split("\n")
        assert len(lines) == 2
        assert lines[1] == "Dune,Frank Herbert,1965,True"

    def test_multiple_books(self, sample_books):
        result = export.books_to_csv_string(sample_books)
        lines = result.strip().split("\n")
        assert len(lines) == 3

    def test_book_with_comma_in_title(self):
        book = Book("The Lion, the Witch and the Wardrobe", "C.S. Lewis", 1950)
        result = export.books_to_csv_string([book])
        lines = result.strip().split("\n")
        # CSV module should quote the field containing a comma
        assert '"The Lion, the Witch and the Wardrobe"' in lines[1]

    def test_read_true_and_false(self, sample_books):
        result = export.books_to_csv_string(sample_books)
        lines = result.strip().splitlines()
        assert lines[1].strip().endswith("True")
        assert lines[2].strip().endswith("False")


class TestExportBooksToCsv:
    def test_writes_file_and_returns_count(self, tmp_path, sample_books):
        filepath = str(tmp_path / "out.csv")
        count = export.export_books_to_csv(sample_books, filepath)
        assert count == 2
        assert os.path.exists(filepath)

    def test_file_content_matches_expected(self, tmp_path, sample_books):
        filepath = str(tmp_path / "out.csv")
        export.export_books_to_csv(sample_books, filepath)
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
        lines = content.strip().split("\n")
        assert lines[0] == "title,author,year,read"
        assert lines[1] == "Dune,Frank Herbert,1965,True"
        assert lines[2] == "1984,George Orwell,1949,False"

    def test_empty_list_writes_header_only(self, tmp_path):
        filepath = str(tmp_path / "out.csv")
        count = export.export_books_to_csv([], filepath)
        assert count == 0
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
        lines = content.strip().split("\n")
        assert len(lines) == 1
        assert lines[0] == "title,author,year,read"

    def test_raises_storage_error_for_invalid_path(self, sample_books):
        bad_path = os.path.join("no", "such", "deep", "dir", "out.csv")
        with pytest.raises(StorageError, match="Could not write CSV"):
            export.export_books_to_csv(sample_books, bad_path)


class TestBooksToDicts:
    def test_empty_list_returns_empty(self):
        assert export.books_to_dicts([]) == []

    def test_single_book_returns_correct_dict(self):
        book = Book("Dune", "Frank Herbert", 1965, read=True)
        result = export.books_to_dicts([book])
        assert len(result) == 1
        assert result[0] == {
            "title": "Dune",
            "author": "Frank Herbert",
            "year": 1965,
            "read": True,
        }

    def test_multiple_books(self, sample_books):
        result = export.books_to_dicts(sample_books)
        assert len(result) == 2
        assert result[0]["title"] == "Dune"
        assert result[1]["title"] == "1984"

    def test_read_field_is_boolean(self, sample_books):
        result = export.books_to_dicts(sample_books)
        assert result[0]["read"] is True
        assert result[1]["read"] is False

    def test_dict_has_all_four_keys(self):
        book = Book("Dune", "Frank Herbert", 1965)
        result = export.books_to_dicts([book])[0]
        assert set(result.keys()) == {"title", "author", "year", "read"}


class TestExportBooksToJson:
    def test_writes_file_and_returns_count(self, tmp_path, sample_books):
        filepath = str(tmp_path / "out.json")
        count = export.export_books_to_json(sample_books, filepath)
        assert count == 2
        assert os.path.exists(filepath)

    def test_file_content_is_parseable_and_matches(self, tmp_path, sample_books):
        filepath = str(tmp_path / "out.json")
        export.export_books_to_json(sample_books, filepath)
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) == 2
        assert data[0]["title"] == "Dune"
        assert data[1]["title"] == "1984"
        assert data[0]["read"] is True
        assert data[1]["read"] is False

    def test_empty_list_writes_empty_array(self, tmp_path):
        filepath = str(tmp_path / "out.json")
        count = export.export_books_to_json([], filepath)
        assert count == 0
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        assert data == []

    def test_custom_indent(self, tmp_path):
        book = Book("Dune", "Frank Herbert", 1965)
        filepath = str(tmp_path / "out.json")
        export.export_books_to_json([book], filepath, indent=4)
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
        # With indent=4, nested keys should be indented by 8 spaces
        assert "        \"title\"" in content

    def test_raises_storage_error_for_invalid_path(self, sample_books):
        bad_path = os.path.join("no", "such", "deep", "dir", "out.json")
        with pytest.raises(StorageError, match="Could not write JSON"):
            export.export_books_to_json(sample_books, bad_path)
