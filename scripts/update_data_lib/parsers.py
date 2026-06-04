from __future__ import annotations

import re
from html import unescape
from html.parser import HTMLParser


class DraftTableParser(HTMLParser):
    def __init__(
        self,
        expected_table_class: str | None = None,
        expected_table_id: str | None = None,
    ) -> None:
        super().__init__()
        self.expected_table_class = expected_table_class
        self.expected_table_id = expected_table_id
        self.use_first_table = expected_table_class is None and expected_table_id is None
        self.in_target_table = False
        self.table_depth = 0
        self.capture_cell = False
        self.current_row: list[str] = []
        self.current_cell: list[str] = []
        self.rows: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "table":
            classes = (attrs_dict.get("class") or "").split()
            matches_class = self.expected_table_class and self.expected_table_class in classes
            matches_id = self.expected_table_id and attrs_dict.get("id") == self.expected_table_id
            if (self.use_first_table or matches_class or matches_id) and not self.in_target_table:
                self.in_target_table = True
                self.table_depth = 1
                return
            if self.in_target_table:
                self.table_depth += 1
        elif self.in_target_table and tag == "tr":
            self.current_row = []
        elif self.in_target_table and tag in {"td", "th"}:
            self.capture_cell = True
            self.current_cell = []

    def handle_endtag(self, tag: str) -> None:
        if self.in_target_table and tag in {"td", "th"} and self.capture_cell:
            cell_text = unescape("".join(self.current_cell))
            cell_text = re.sub(r"\s+", " ", cell_text).strip()
            self.current_row.append(cell_text)
            self.capture_cell = False
        elif self.in_target_table and tag == "tr" and self.current_row:
            self.rows.append(self.current_row)
            self.current_row = []
        elif self.in_target_table and tag == "table":
            self.table_depth -= 1
            if self.table_depth <= 0:
                self.in_target_table = False

    def handle_data(self, data: str) -> None:
        if self.capture_cell:
            self.current_cell.append(data)


class LinkedTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_target_table = False
        self.table_depth = 0
        self.capture_cell = False
        self.current_row: list[dict[str, str]] = []
        self.current_cell_text: list[str] = []
        self.current_cell_link = ""
        self.rows: list[list[dict[str, str]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "table" and not self.in_target_table:
            self.in_target_table = True
            self.table_depth = 1
            return
        if self.in_target_table and tag == "table":
            self.table_depth += 1
        elif self.in_target_table and tag == "tr":
            self.current_row = []
        elif self.in_target_table and tag in {"td", "th"}:
            self.capture_cell = True
            self.current_cell_text = []
            self.current_cell_link = ""
        elif self.capture_cell and tag == "a":
            self.current_cell_link = attrs_dict.get("href") or ""

    def handle_endtag(self, tag: str) -> None:
        if self.in_target_table and tag in {"td", "th"} and self.capture_cell:
            text = unescape("".join(self.current_cell_text))
            text = re.sub(r"\s+", " ", text).strip()
            self.current_row.append({"text": text, "href": self.current_cell_link})
            self.capture_cell = False
        elif self.in_target_table and tag == "tr" and self.current_row:
            self.rows.append(self.current_row)
            self.current_row = []
        elif self.in_target_table and tag == "table":
            self.table_depth -= 1
            if self.table_depth <= 0:
                self.in_target_table = False

    def handle_data(self, data: str) -> None:
        if self.capture_cell:
            self.current_cell_text.append(data)


def parse_score_feed(
    html: str,
    table_id: str,
    player_column: str,
    score_column: str,
) -> dict[str, float]:
    parser = DraftTableParser(expected_table_id=table_id)
    parser.feed(html)

    if len(parser.rows) < 2:
        raise ValueError("No rows found in target score table")

    headers = parser.rows[0]
    try:
        player_index = headers.index(player_column)
        score_index = headers.index(score_column)
    except ValueError as exc:
        raise ValueError(f"Missing expected columns in table headers: {headers}") from exc

    scores: dict[str, float] = {}
    for row in parser.rows[1:]:
        if len(row) <= max(player_index, score_index):
            continue

        player_name = row[player_index].strip()
        score_text = row[score_index].strip()
        if not player_name or player_name == player_column:
            continue

        try:
            score_value = float(score_text or 0)
        except ValueError:
            continue

        scores[player_name] = score_value

    return scores


def extract_csrf_token(html: str) -> str:
    match = re.search(r"CSRF_TOKEN\s*=\s*'([^']+)'", html)
    if not match:
        raise ValueError("Could not find CSRF token on sweat page")
    return match.group(1)
