import os
import tempfile
import sqlite3
from unittest.mock import patch, MagicMock
import pytest
from src.c108_genre_importer import import_c108_genre_mapping
from src.db import get_db_connection

MOCK_HTML = """
<html>
<body>
<table class="table_0">
  <tr>
    <th>日</th>
    <th>ジャンルコード</th>
    <th>ジャンル名</th>
    <th>ジャンル補足</th>
    <th>サブジャンル補足</th>
  </tr>
  <tr>
    <td rowspan="2">2</td>
    <td rowspan="2">111</td>
    <td rowspan="2">創作(少年)</td>
    <td rowspan="2"></td>
    <td>---</td>
  </tr>
  <tr>
    <td>イラスト</td>
  </tr>
  <tr>
    <td>1</td>
    <td>113</td>
    <td>創作(JUNE/BL)</td>
    <td>備考メモ</td>
    <td>---</td>
  </tr>
</table>
</body>
</html>
"""

@patch("src.c108_genre_importer.requests.get")
def test_c108_genre_importer(mock_get):
    # 1. Mock the requests.get response
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = MOCK_HTML
    mock_get.return_value = mock_resp

    # 2. Setup mock sqlite database
    db_fd, db_path = tempfile.mkstemp()
    try:
        # Import genre mapping
        success = import_c108_genre_mapping(db_path=db_path)
        assert success is True
        
        # Verify db entries
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM comiket_genre_mapping")
        assert cursor.fetchone()[0] == 3
        
        cursor.execute("SELECT event, day, genre_code, genre_name, note, supplement FROM comiket_genre_mapping ORDER BY genre_code, supplement")
        rows = cursor.fetchall()
        
        # Row 1 (111 ---)
        assert rows[0][0] == "C108"
        assert rows[0][1] == "2"
        assert rows[0][2] == 111
        assert rows[0][3] == "創作(少年)"
        assert rows[0][4] is None
        assert rows[0][5] == "---"
        
        # Row 2 (111 イラスト)
        assert rows[1][0] == "C108"
        assert rows[1][1] == "2"
        assert rows[1][2] == 111
        assert rows[1][3] == "創作(少年)"
        assert rows[1][4] is None
        assert rows[1][5] == "イラスト"
        
        # Row 3 (113 ---)
        assert rows[2][0] == "C108"
        assert rows[2][1] == "1"
        assert rows[2][2] == 113
        assert rows[2][3] == "創作(JUNE/BL)"
        assert rows[2][4] == "備考メモ"
        assert rows[2][5] == "---"
        
        conn.close()
        
        # Test idempotency (should run without failure because of UNIQUE constraint and ON CONFLICT REPLACE)
        success_retry = import_c108_genre_mapping(db_path=db_path)
        assert success_retry is True
        
    finally:
        os.close(db_fd)
        os.remove(db_path)
