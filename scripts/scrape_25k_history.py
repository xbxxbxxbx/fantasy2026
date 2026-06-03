#!/usr/bin/env python3

from __future__ import annotations

import json
import re
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "docs" / "25k-player-history.json"
YEARS = range(2011, 2026)


class TableParser(HTMLParser):
    def __init__(self, table_id: str) -> None:
        super().__init__()
        self.table_id = table_id
        self.in_target_table = False
        self.table_depth = 0
        self.capture_cell = False
        self.current_row: list[str] = []
        self.current_cell: list[str] = []
        self.rows: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "table":
            if attrs_dict.get("id") == self.table_id and not self.in_target_table:
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


def fetch_html(year: int) -> str:
    url = f"https://www.25kfantasy.com/players/{year}"
    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.25kfantasy.com/",
        },
    )
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_year(html: str, year: int) -> dict[str, float]:
    parser = TableParser("dataTable-main")
    parser.feed(html)

    if len(parser.rows) < 2:
        raise RuntimeError(f"No historical player rows found for {year}")

    headers = parser.rows[0]
    try:
      player_index = headers.index("Player")
      score_index = headers.index("Score")
    except ValueError as exc:
      raise RuntimeError(f"Unexpected headers for {year}: {headers}") from exc

    year_points: dict[str, float] = {}
    for row in parser.rows[1:]:
        if len(row) <= max(player_index, score_index):
            continue

        player_name = row[player_index].strip()
        score_text = row[score_index].strip()
        if not player_name:
            continue

        try:
            score = float(score_text)
        except ValueError:
            continue

        year_points[player_name] = score

    return year_points


def build_history() -> dict[str, dict[str, float]]:
    history: dict[str, dict[str, float]] = {}

    for year in YEARS:
        html = fetch_html(year)
        year_points = parse_year(html, year)
        year_key = str(year)
        for name, score in year_points.items():
            history.setdefault(name, {})[year_key] = score

    return dict(sorted(history.items(), key=lambda item: item[0].lower()))


def main() -> int:
    history = build_history()
    OUTPUT_PATH.write_text(json.dumps(history, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
