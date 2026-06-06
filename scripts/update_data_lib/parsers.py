from __future__ import annotations

import re
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urlparse


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


class PokerOrgTeamPageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.current_heading_tag = ""
        self.current_heading: list[str] = []
        self.in_table = False
        self.table_depth = 0
        self.capture_cell = False
        self.current_row: list[str] = []
        self.current_cell: list[str] = []
        self.current_table: list[list[str]] = []
        self.title_parts: list[str] = []
        self.headings: list[str] = []
        self.tables: list[list[list[str]]] = []
        self.body_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "title":
            self.in_title = True
        elif tag in {"h1", "h2", "h3"}:
            self.current_heading_tag = tag
            self.current_heading = []
        elif tag == "table" and not self.in_table:
            self.in_table = True
            self.table_depth = 1
            self.current_table = []
        elif self.in_table and tag == "table":
            self.table_depth += 1
        elif self.in_table and tag == "tr":
            self.current_row = []
        elif self.in_table and tag in {"td", "th"}:
            self.capture_cell = True
            self.current_cell = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False
        elif tag == self.current_heading_tag:
            heading = normalize_text("".join(self.current_heading))
            if heading:
                self.headings.append(heading)
            self.current_heading_tag = ""
            self.current_heading = []
        elif self.in_table and tag in {"td", "th"} and self.capture_cell:
            cell_text = normalize_text("".join(self.current_cell))
            self.current_row.append(cell_text)
            self.capture_cell = False
        elif self.in_table and tag == "tr" and self.current_row:
            self.current_table.append(self.current_row)
            self.current_row = []
        elif self.in_table and tag == "table":
            self.table_depth -= 1
            if self.table_depth <= 0:
                self.tables.append(self.current_table)
                self.current_table = []
                self.in_table = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
        if self.current_heading_tag:
            self.current_heading.append(data)
        if self.capture_cell:
            self.current_cell.append(data)
        if data.strip():
            self.body_parts.append(data)


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(value)).strip()


def clean_player_name(value: str) -> str:
    name = normalize_text(value)
    name = re.sub(r"^Image:\s*", "", name)
    tokens = name.split()
    midpoint = len(tokens) // 2
    if len(tokens) % 2 == 0 and tokens[:midpoint] == tokens[midpoint:]:
        name = " ".join(tokens[:midpoint])
    return name


def _team_name_from_title(title: str) -> str:
    title = normalize_text(title)
    for separator in (" - Fantasy Poker", " | PokerOrg", " | Poker.org"):
        if separator in title:
            return title.split(separator, 1)[0].strip()
    return title


def _team_name_from_url(url: str) -> str:
    slug = urlparse(url).path.rstrip("/").split("/")[-1]
    return re.sub(r"[-_]+", " ", slug).strip().title()


def _find_roster_table(tables: list[list[list[str]]]) -> list[list[str]]:
    for table in tables:
        if not table:
            continue
        headers = [cell.upper() for cell in table[0]]
        if headers and headers[0] == "PLAYER" and "SCORE" in headers:
            return table
    raise ValueError("Could not find Poker.org roster table")


def parse_poker_org_team_page(html: str, url: str) -> dict:
    parser = PokerOrgTeamPageParser()
    parser.feed(html)

    title = normalize_text("".join(parser.title_parts))
    team_name = _team_name_from_title(title) if title else ""
    generic_headings = {
        "Fantasy Poker",
        "Roster",
        "Team Roster",
        "Player Leaderboard",
        "Leaderboard Rules",
        "Key dates",
    }
    if not team_name or team_name in generic_headings:
        team_name = next(
            (heading for heading in parser.headings if heading not in generic_headings),
            "",
        )
    if not team_name:
        team_name = _team_name_from_url(url)

    body_text = normalize_text(" ".join(parser.body_parts))
    owner_match = re.search(
        r"Owner:\s*(.+?)(?:\s+Tiebreaker|\s+TOTAL SCORE|\s+Current Score|$)",
        body_text,
        re.I,
    )
    manager_name = normalize_text(owner_match.group(1)) if owner_match else team_name

    roster_table = _find_roster_table(parser.tables)
    roster = []
    for row in roster_table[1:]:
        if not row:
            continue
        player_name = clean_player_name(row[0])
        if player_name and player_name.upper() != "PLAYER":
            roster.append(player_name)

    if not roster:
        raise ValueError(f"Could not find roster players for {team_name}")

    return {
        "managerName": manager_name,
        "teamName": team_name,
        "url": url,
        "roster": roster,
    }


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
