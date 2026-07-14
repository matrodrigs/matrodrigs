from __future__ import annotations

import html
import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
USER = os.environ.get("GITHUB_USER", "matrodrigs")
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
GRAPHQL_URL = "https://api.github.com/graphql"

WIDTH = 1050
HEIGHT = 540
RIGHT_X = 380
CHAR_WIDTH = 9.6
VALUE_COLUMN = 22
FONT_FAMILY = "'SFMono-Regular', Consolas, 'Liberation Mono', monospace"


THEMES = {
    "dark": {
        "background": "#0d1117",
        "panel": "#161b22",
        "border": "#30363d",
        "text": "#c9d1d9",
        "muted": "#6e7681",
        "label": "#f2a65a",
        "value": "#79c0ff",
        "positive": "#56d364",
        "negative": "#ff7b72",
    },
    "light": {
        "background": "#ffffff",
        "panel": "#f6f8fa",
        "border": "#d0d7de",
        "text": "#24292f",
        "muted": "#8c959f",
        "label": "#bc4c00",
        "value": "#0969da",
        "positive": "#1a7f37",
        "negative": "#cf222e",
    },
}


def graphql(query: str, variables: dict) -> dict:
    if not TOKEN:
        raise RuntimeError("GITHUB_TOKEN or GH_TOKEN is required")

    payload = json.dumps({"query": query, "variables": variables}).encode()
    request = Request(
        GRAPHQL_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": f"{USER}-profile-readme",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=45) as response:
            result = json.load(response)
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub GraphQL request failed: {error.code}: {detail}") from error

    if result.get("errors"):
        raise RuntimeError(f"GitHub GraphQL returned errors: {result['errors']}")
    return result["data"]


def fetch_profile() -> tuple[list[dict], int]:
    query = """
    query($login: String!, $cursor: String) {
      user(login: $login) {
        followers { totalCount }
        repositories(
          first: 100,
          after: $cursor,
          ownerAffiliations: [OWNER],
          privacy: PUBLIC,
          orderBy: {field: UPDATED_AT, direction: DESC}
        ) {
          nodes { name owner { login } defaultBranchRef { name } }
          pageInfo { hasNextPage endCursor }
        }
      }
    }
    """

    repositories: list[dict] = []
    cursor = None
    followers = 0
    while True:
        data = graphql(query, {"login": USER, "cursor": cursor})["user"]
        followers = data["followers"]["totalCount"]
        page = data["repositories"]
        repositories.extend(page["nodes"])
        if not page["pageInfo"]["hasNextPage"]:
            return repositories, followers
        cursor = page["pageInfo"]["endCursor"]


def fetch_repository_metrics(owner: str, name: str) -> tuple[int, int, int]:
    query = """
    query($owner: String!, $name: String!, $cursor: String) {
      repository(owner: $owner, name: $name) {
        defaultBranchRef {
          target {
            ... on Commit {
              history(first: 100, after: $cursor) {
                nodes {
                  additions
                  deletions
                  author { user { login } }
                }
                pageInfo { hasNextPage endCursor }
              }
            }
          }
        }
      }
    }
    """

    commits = additions = deletions = 0
    cursor = None
    while True:
        data = graphql(query, {"owner": owner, "name": name, "cursor": cursor})
        branch = data["repository"]["defaultBranchRef"]
        if branch is None:
            return commits, additions, deletions

        history = branch["target"]["history"]
        for commit in history["nodes"]:
            author = commit.get("author") or {}
            account = author.get("user") or {}
            if account.get("login", "").lower() != USER.lower():
                continue
            commits += 1
            additions += commit["additions"]
            deletions += commit["deletions"]

        if not history["pageInfo"]["hasNextPage"]:
            return commits, additions, deletions
        cursor = history["pageInfo"]["endCursor"]


def collect_metrics() -> dict[str, int]:
    repositories, followers = fetch_profile()
    commits = additions = deletions = 0
    for repository in repositories:
        repo_commits, repo_additions, repo_deletions = fetch_repository_metrics(
            repository["owner"]["login"], repository["name"]
        )
        commits += repo_commits
        additions += repo_additions
        deletions += repo_deletions

    return {
        "repositories": len(repositories),
        "followers": followers,
        "commits": commits,
        "additions": additions,
        "deletions": deletions,
        "lines": additions - deletions,
    }


def svg_text(x: int, y: float, value: str, color: str, size: int = 16, weight: int = 400) -> str:
    return (
        f'<text x="{x}" y="{y:g}" fill="{color}" font-family="{FONT_FAMILY}" '
        f'font-size="{size}" font-weight="{weight}" style="white-space:pre">{html.escape(value)}</text>'
    )


def render(theme_name: str, metrics: dict[str, int]) -> str:
    colors = THEMES[theme_name]
    portrait = (ASSETS / "portrait.txt").read_text(encoding="utf-8").splitlines()
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc" xml:space="preserve">',
        '<title id="title">Mateus Rodrigues GitHub profile</title>',
        '<desc id="desc">Terminal-style profile card with an ASCII portrait, skills, projects, contact information, and live GitHub statistics.</desc>',
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{colors["background"]}"/>',
        f'<rect x="14" y="14" width="{WIDTH - 28}" height="{HEIGHT - 28}" rx="20" fill="{colors["panel"]}" stroke="{colors["border"]}" stroke-width="2"/>',
    ]

    for index, line in enumerate(portrait):
        elements.append(svg_text(20, 32 + index * 10.55, line, colors["text"], size=12))

    y = 39.0
    right_edge_chars = int((WIDTH - RIGHT_X - 36) / CHAR_WIDTH)

    def header(title: str, username: bool = False) -> None:
        nonlocal y
        separator = "-" if username else "─"
        length = max(4, right_edge_chars - len(title) - 1)
        elements.append(svg_text(RIGHT_X, y, title, colors["text"], weight=700 if username else 400))
        elements.append(svg_text(RIGHT_X + (len(title) + 1) * CHAR_WIDTH, y, separator * length, colors["muted"]))
        y += 25

    def field(label: str, value: str, value_color: str | None = None) -> None:
        nonlocal y
        dots = "." * max(3, VALUE_COLUMN - 1 - len(label))
        elements.append(svg_text(RIGHT_X + 16, y, label, colors["label"]))
        elements.append(svg_text(RIGHT_X + 16 + (len(label) + 1) * CHAR_WIDTH, y, dots, colors["muted"]))
        elements.append(svg_text(RIGHT_X + 16 + VALUE_COLUMN * CHAR_WIDTH, y, value, value_color or colors["value"]))
        y += 24

    def lines_field() -> None:
        nonlocal y
        label = "Lines.of.Code:"
        dots = "." * max(3, VALUE_COLUMN - 1 - len(label))
        value_x = RIGHT_X + 16 + VALUE_COLUMN * CHAR_WIDTH
        net = f'{metrics["lines"]:,}'
        added = f' ({metrics["additions"]:,}++'
        removed = f', {metrics["deletions"]:,}--)'
        elements.append(svg_text(RIGHT_X + 16, y, label, colors["label"]))
        elements.append(svg_text(RIGHT_X + 16 + (len(label) + 1) * CHAR_WIDTH, y, dots, colors["muted"]))
        elements.append(svg_text(value_x, y, net, colors["value"]))
        elements.append(svg_text(value_x + len(net) * CHAR_WIDTH, y, added, colors["positive"]))
        elements.append(svg_text(value_x + (len(net) + len(added)) * CHAR_WIDTH, y, removed, colors["negative"]))
        y += 24

    header("matrodrigs@github", username=True)
    field("Name:", "Mateus Rodrigues")
    field("Role:", "Software Developer · Java & TypeScript")
    field("Education:", "Computer Science @ UNESP")
    field("Location:", "Bauru, SP · Brazil")
    y += 8

    header("- What I Do ")
    field("Main.Stack:", "Java · TypeScript")
    field("Best.At:", "Turning real problems into software solutions")
    y += 8

    header("- Featured Work ")
    field("Furia.Botanica:", "2D boss fight · Java 21 · libGDX")
    field("Shotcut.MCP:", "Transactional AI video editing server")
    y += 8

    header("- Contact ")
    field("Email:", "teus_rodrigues@outlook.com.br")
    field("LinkedIn:", "linkedin.com/in/mat-rodrigues")
    y += 8

    header("- GitHub Stats ")
    field("Public.Repos:", f'{metrics["repositories"]}')
    field("Commits:", f'{metrics["commits"]:,}')
    field("Followers:", f'{metrics["followers"]:,}')
    lines_field()

    elements.append("</svg>")
    return "\n".join(elements) + "\n"


def main() -> None:
    metrics = collect_metrics()
    for theme in THEMES:
        target = ASSETS / f"{theme}_mode.svg"
        target.write_text(render(theme, metrics), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
