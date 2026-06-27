from main import *


def test_read(tmp_path):
    import os
    f = tmp_path / 'test.txt'
    f.write_text('line1\nline2\nline3')
    assert read_file_lines(str(f)) == ['line1', 'line2', 'line3']


def test_empty(tmp_path):
    import os
    f = tmp_path / 'empty.txt'
    f.write_text('')
    assert read_file_lines(str(f)) == ['']


def test_not_found():
    try:
        read_file_lines('/nonexistent/file.txt')
        assert False, 'should have raised'
    except FileNotFoundError:
        pass
