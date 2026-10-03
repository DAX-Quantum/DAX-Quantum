#!/usr/bin/env python3
"""
Generates terminal.svg: an animated Linux-desktop terminal for your GitHub profile,
and automatically synchronizes the projects table in README.md.

Features:
- Dynamically fetches public repositories from GitHub API.
- Supports curated overrides (custom descriptions & stacks).
- Automatically includes new repositories when added to GitHub.
- Updates terminal.svg and README.md with pixel-perfect formatting.
- Gracefully falls back to cached/default data if offline or rate-limited.
"""

import json
import os
import re
import urllib.error
import urllib.request
from xml.sax.saxutils import escape

# ============================== CONFIG ==============================
USER = "DAX-Quantum"            # shown in the prompt: yourname@tux
HOST = "tux"
ROLE = "CSE Student | Developer | HPC Enthusiast"
LOCATION = "India"
EDITOR = "Neovim / VS Code"
UPTIME = "coding since 2025"
OS_NAME = "Arch Linux (btw), Rocky Linux, Windows"

ABOUT = [
    "Hi, I'm Daksh Vashistha. I build software and tools that solve real problems.",
    "Focused on High Performance Computing (HPC), C++, and Systems Development.",
    "Open to collaborations, open-source contributions, and engineering internships.",
]

# (skill name, percent 0-100)
SKILLS = [
    ("C++", 90),
    ("C", 85),
    ("JavaScript", 85),
    ("React", 80),
    ("Linux/Bash", 80),
    ("Docker", 65),
]

# Repositories to exclude from projects listing
IGNORED_REPOS = {
    USER.lower(),      # Special profile repository (DAX-Quantum/DAX-Quantum)
    ".github",
}

# Maximum projects to animate inside terminal.svg (README table will list all)
MAX_TERMINAL_PROJECTS = 8

# Curated overrides for known projects (order here is preserved)
PROJECT_OVERRIDES = {
    "linux-server-health-audit": {
        "desc": "Automated server health auditor monitoring CPU, memory, storage, and active services with status alerts.",
        "short_desc": "Server health & resource monitor",
        "stack": "Bash",
        "tags": ["Bash", "Linux"],
    },
    "linux-system-info-tool": {
        "desc": "Interactive CLI utility for querying hardware specifications, kernel versions, and OS telemetry.",
        "short_desc": "System telemetry & hardware info",
        "stack": "Bash",
        "tags": ["Bash", "Linux"],
    },
    "Student_Record_System": {
        "desc": "CLI database management tool to store, search, update, and persist student academic records.",
        "short_desc": "Student database & records manager",
        "stack": "C++",
        "tags": ["C++", "File I/O"],
    },
    "Comic_book": {
        "desc": "Responsive comic book showcase and reader web application with catalog browsing.",
        "short_desc": "Comic showcase & reader web app",
        "stack": "React/JS",
        "tags": ["React", "JavaScript", "CSS3"],
    },
    "finanace-manager": {
        "desc": "FinVault personal expense & finance management web application.",
        "short_desc": "Personal finance & expense manager",
        "stack": "JavaScript",
        "tags": ["JavaScript", "HTML5", "CSS3"],
    },
}

CONTACT = [
    ("github", f"github.com/{USER}"),
    ("linkedin", "linkedin.com/in/daksh-vashistha-483a29420"),
    ("email", "Dax.in@outlook.com"),
]
# ====================================================================

# Tokyo-Night-style palette
C = dict(
    fg="#c0caf5",
    green="#9ece6a",
    blue="#7aa2f7",
    yellow="#e0af68",
    red="#f7768e",
    purple="#bb9af7",
    cyan="#7dcfff",
    dim="#565f89",
    black="#15161e",
    white="#ffffff",
)
FONT = "'Fira Code', 'Cascadia Code', 'JetBrains Mono', Menlo, Consolas, 'DejaVu Sans Mono', monospace"
UI_FONT = "Ubuntu, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
CW = 8.4          # character width at font-size 14
LH = 21           # line height
W = 820           # svg width
LEFT = 44         # text x
WIN_X, WIN_Y = 16, 44
TYPE_SPEED = 0.055  # seconds per typed character


def fetch_github_projects(username):
    """
    Fetches public repositories for `username` from GitHub API.
    Returns a list of project dicts with name, desc, short_desc, stack, tags, and html_url.
    Falls back gracefully to PROJECT_OVERRIDES on error.
    """
    url = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=100"
    headers = {
        "User-Agent": "Profile-Terminal-Updater",
        "Accept": "application/vnd.github.v3+json",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    api_repos = []
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            api_repos = json.loads(resp.read().decode("utf-8"))
        print(f"Fetched {len(api_repos)} repositories from GitHub API.")
    except Exception as e:
        print(f"[WARN] GitHub API request failed ({e}). Using cached/override list.")

    repo_map = {r["name"]: r for r in api_repos if isinstance(r, dict)}

    projects = []
    seen = set()

    # 1. First add curated projects from PROJECT_OVERRIDES (maintaining priority order)
    for name, info in PROJECT_OVERRIDES.items():
        if name.lower() in IGNORED_REPOS:
            continue
        api_data = repo_map.get(name, {})
        html_url = api_data.get("html_url", f"https://github.com/{username}/{name}")
        projects.append({
            "name": name,
            "desc": info.get("desc", api_data.get("description") or f"{name} repository"),
            "short_desc": info.get("short_desc", "Project"),
            "stack": info.get("stack", api_data.get("language") or "Code"),
            "tags": info.get("tags", [info.get("stack", "Code")]),
            "html_url": html_url,
        })
        seen.add(name.lower())

    # 2. Add any newly discovered repositories from GitHub API
    for repo in api_repos:
        name = repo.get("name", "")
        if not name or name.lower() in seen or name.lower() in IGNORED_REPOS:
            continue
        if repo.get("fork"):  # skip forks
            continue

        raw_desc = (repo.get("description") or "").strip()
        desc = raw_desc if raw_desc else f"{name} repository"
        short_desc = (desc[:32] + "…") if len(desc) > 35 else desc
        lang = repo.get("language") or "Code"
        topics = [t.capitalize() for t in repo.get("topics", []) if t.lower() != lang.lower()][:2]
        tags = [lang] + topics

        projects.append({
            "name": name,
            "desc": desc,
            "short_desc": short_desc,
            "stack": lang,
            "tags": tags,
            "html_url": repo.get("html_url", f"https://github.com/{username}/{name}"),
        })
        seen.add(name.lower())

    return projects


def update_readme_projects(projects_data, readme_path="README.md"):
    """Synchronizes the projects table in README.md."""
    if not os.path.exists(readme_path):
        print(f"[WARN] {readme_path} not found. Skipping README update.")
        return

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = [
        "| Project | Description | Stack | Link |",
        "| :--- | :--- | :--- | :--- |",
    ]
    for p in projects_data:
        name = p["name"]
        url = p["html_url"]
        desc = p["desc"]
        tags_str = " ".join(f"`{t}`" for t in p["tags"])
        badge = f"[![View Repo](https://img.shields.io/badge/Repo-View-181717?logo=github&style=flat-square)]({url})"
        lines.append(f"| **[{name}]({url})** | {desc} | {tags_str} | {badge} |")

    table_md = "\n".join(lines)
    start_tag = "<!-- START_SECTION:projects -->"
    end_tag = "<!-- END_SECTION:projects -->"
    section_text = f"{start_tag}\n{table_md}\n{end_tag}"

    pattern = re.compile(rf"{re.escape(start_tag)}[\s\S]*?{re.escape(end_tag)}")
    if pattern.search(content):
        new_content = pattern.sub(section_text, content)
    else:
        # Wrap existing table if markers are not yet present
        table_pattern = re.compile(r"\| Project \| Description \| Stack \| Link \|[\s\S]*?(?=\n<br/>|\n---|\Z)")
        if table_pattern.search(content):
            new_content = table_pattern.sub(section_text, content)
        else:
            new_content = content

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("[OK] README.md projects table updated successfully.")


# Tux penguin with multi-color segments (each line is exactly 12 characters)
TUX_SEGS = [
    [("    .--.    ", "fg")],
    [("   |", "fg"), ("o_o ", "cyan"), ("|   ", "fg")],
    [("   |", "fg"), (":_/", "yellow"), (" |   ", "fg")],
    [("  //   \\ \\  ", "fg")],
    [(" (|     | ) ", "fg")],
    [("/'\\_   _/`\\ ", "yellow")],
    [("\\___)=(___/ ", "yellow")],
]


def make_skill_bar(pct, width=20):
    """Returns dual-color progress bar with bright filled blocks and dim empty track."""
    filled = round(width * pct / 100)
    empty = width - filled
    return [
        ("\u2588" * filled, "green"),
        ("\u2591" * empty, "dim"),
    ]


def tspans(segs):
    return "".join(f'<tspan fill="{C[c]}">{escape(t)}</tspan>' for t, c in segs)


def discrete(values):
    n = len(values) - 1
    vals = ";".join(f"{v:.1f}" for v in values)
    keys = ";".join(f"{i / n:.4f}" for i in range(n + 1))
    return vals, keys


def generate():
    # 1. Fetch live projects
    projects = fetch_github_projects(USER)
    print(f"Total projects active: {len(projects)}")

    # Update README table
    update_readme_projects(projects, "README.md")

    # Limit animated terminal entries to MAX_TERMINAL_PROJECTS
    terminal_projects = projects[:MAX_TERMINAL_PROJECTS]

    # System info lines (padded consistently with colons)
    info = [
        [(f"{USER}@{HOST}", "green")],
        [("-" * (len(USER) + len(HOST) + 1), "dim")],
        [("OS:       ", "blue"), (OS_NAME, "fg")],
        [("Role:     ", "blue"), (ROLE, "fg")],
        [("Location: ", "blue"), (LOCATION, "fg")],
        [("Editor:   ", "blue"), (EDITOR, "fg")],
        [("Uptime:   ", "blue"), (UPTIME, "fg")],
    ]

    neofetch_lines = [TUX_SEGS[i] + info[i] for i in range(7)]

    # Neofetch signature color palette row
    palette_row = [
        (" " * 12, "dim"),
        ("███ ", "black"),
        ("███ ", "red"),
        ("███ ", "green"),
        ("███ ", "yellow"),
        ("███ ", "blue"),
        ("███ ", "purple"),
        ("███ ", "cyan"),
        ("███", "fg"),
    ]
    neofetch_lines.append(palette_row)

    # Format project lines for monospace terminal
    project_lines = []
    for p in terminal_projects:
        name = p["name"]
        short_desc = p["short_desc"]
        stack = p["stack"]

        name_disp = (name[:24] + "…") if len(name) > 25 else name
        desc_disp = (short_desc[:33] + "…") if len(short_desc) > 34 else short_desc

        project_lines.append([
            ("drwxr-xr-x  ", "dim"),
            (name_disp.ljust(26), "purple"),
            (desc_disp.ljust(35), "fg"),
            (f"[{stack[:10]}]", "cyan"),
        ])

    blocks = [
        dict(cmd="neofetch", out=neofetch_lines),
        dict(cmd="cat about.md", out=[[(line, "fg")] for line in ABOUT]),
        dict(
            cmd="skills --list",
            out=[
                [(n.ljust(12), "cyan")] + make_skill_bar(p) + [(f" {p}%", "yellow")]
                for n, p in SKILLS
            ],
        ),
        dict(
            cmd="ls -l ~/projects",
            out=project_lines,
        ),
        dict(
            cmd="./contact.sh",
            out=[[(f"{k}:".ljust(12), "blue"), (v, "fg")] for k, v in CONTACT],
        ),
    ]

    prompt = [(f"{USER}@{HOST}", "green"), (":", "fg"), ("~", "blue"), ("$ ", "fg")]
    plen = len(USER) + len(HOST) + 5  # chars in prompt

    body = []
    defs = []
    y = WIN_Y + 34 + 30  # first baseline
    t = 0.8

    for i, blk in enumerate(blocks):
        cmd = blk["cmd"]
        n = len(cmd)
        pw = plen * CW
        type_start = t + 0.4
        type_dur = n * TYPE_SPEED
        type_end = type_start + type_dur

        widths = [pw + k * CW + 2 for k in range(n + 1)]
        wv, wk = discrete(widths)
        defs.append(
            f'<clipPath id="c{i}"><rect x="{LEFT}" y="{y - 16}" width="{widths[0]:.1f}" height="{LH}">'
            f'<animate attributeName="width" values="{wv}" keyTimes="{wk}" calcMode="discrete" '
            f'begin="{type_start:.2f}s" dur="{type_dur:.2f}s" fill="freeze"/></rect></clipPath>'
        )

        # prompt + typed command
        body.append(
            f'<g opacity="0"><set attributeName="opacity" to="1" begin="{t:.2f}s" fill="freeze"/>'
            f'<text x="{LEFT}" y="{y}" clip-path="url(#c{i})" xml:space="preserve">'
            f'{tspans(prompt)}<tspan fill="{C["fg"]}">{escape(cmd)}</tspan></text></g>'
        )

        # moving block cursor while typing
        xs = [LEFT + pw + k * CW for k in range(n + 1)]
        xv, xk = discrete(xs)
        body.append(
            f'<rect x="{xs[0]:.1f}" y="{y - 13}" width="8" height="17" fill="{C["fg"]}" opacity="0">'
            f'<set attributeName="opacity" to="1" begin="{t:.2f}s" fill="freeze"/>'
            f'<animate attributeName="x" values="{xv}" keyTimes="{xk}" calcMode="discrete" '
            f'begin="{type_start:.2f}s" dur="{type_dur:.2f}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0" begin="{type_end + 0.25:.2f}s" fill="freeze"/></rect>'
        )

        # output lines appear one after another
        ot = type_end + 0.35
        y += LH
        for line in blk["out"]:
            body.append(
                f'<text x="{LEFT}" y="{y}" opacity="0" xml:space="preserve">'
                f'<set attributeName="opacity" to="1" begin="{ot:.2f}s" fill="freeze"/>'
                f'{tspans(line)}</text>'
            )
            ot += 0.10
            y += LH
        y += 10
        t = ot + 0.45

    # final prompt with blinking cursor
    body.append(
        f'<text x="{LEFT}" y="{y}" opacity="0" xml:space="preserve">'
        f'<set attributeName="opacity" to="1" begin="{t:.2f}s" fill="freeze"/>{tspans(prompt)}</text>'
    )
    body.append(
        f'<rect x="{LEFT + plen * CW:.1f}" y="{y - 13}" width="8" height="17" fill="{C["fg"]}" opacity="0">'
        f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1.1s" '
        f'begin="{t:.2f}s" repeatCount="indefinite"/></rect>'
    )

    h = y + 40
    win_w = W - 2 * WIN_X
    win_h = h - WIN_Y - 16

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h:.0f}" viewBox="0 0 {W} {h:.0f}" font-family="{FONT}" font-size="14">
<title>{escape(USER)}@{HOST}: ~</title>
<defs>
<linearGradient id="wall" x1="0" y1="0" x2="1" y2="1">
<stop offset="0%" stop-color="#0e1017"/>
<stop offset="50%" stop-color="#181d28"/>
<stop offset="100%" stop-color="#0f121a"/>
</linearGradient>
<radialGradient id="glow" cx="85%" cy="15%" r="65%">
<stop offset="0%" stop-color="#7aa2f7" stop-opacity="0.16"/>
<stop offset="100%" stop-color="#7aa2f7" stop-opacity="0"/>
</radialGradient>
{"".join(defs)}
</defs>

<!-- desktop wallpaper -->
<rect width="{W}" height="{h:.0f}" rx="12" fill="url(#wall)"/>
<rect width="{W}" height="{h:.0f}" rx="12" fill="url(#glow)"/>

<!-- GNOME-style top panel -->
<rect width="{W}" height="28" rx="0" fill="#000000" opacity="0.75"/>
<text x="18" y="19" font-family="{UI_FONT}" font-size="12" font-weight="600" fill="#ffffff">Activities</text>
<text x="86" y="19" font-family="{UI_FONT}" font-size="12" fill="#7aa2f7" font-weight="500">Terminal</text>
<text x="{W / 2}" y="19" text-anchor="middle" font-family="{UI_FONT}" font-size="12" fill="#c0caf5" opacity="0.9">Thu Oct 1  02:10</text>
<g fill="#ffffff" opacity="0.9">
<!-- network wifi -->
<path d="M{W - 74} 18 a5 5 0 0 1 10 0" fill="none" stroke="#ffffff" stroke-width="1.6" stroke-linecap="round"/>
<circle cx="{W - 69}" cy="19" r="1.3"/>
<!-- audio volume -->
<path d="M{W - 55} 12 v6 l4 3 h2 v-12 h-2 z" fill="#ffffff"/>
<path d="M{W - 47} 13 a4 4 0 0 1 0 6" fill="none" stroke="#ffffff" stroke-width="1.4" stroke-linecap="round"/>
<!-- battery pill -->
<rect x="{W - 38}" y="9.5" width="18" height="10" rx="2" fill="none" stroke="#ffffff" stroke-width="1.3"/>
<rect x="{W - 35}" y="11.5" width="11" height="6" rx="1" fill="#9ece6a"/>
<rect x="{W - 19}" y="12.5" width="2" height="4" rx="0.5" fill="#ffffff"/>
</g>

<!-- terminal window shadow -->
<rect x="{WIN_X}" y="{WIN_Y + 3}" width="{win_w}" height="{win_h:.0f}" rx="10" fill="#000000" opacity="0.4"/>

<!-- terminal window body & titlebar -->
<rect x="{WIN_X}" y="{WIN_Y}" width="{win_w}" height="{win_h:.0f}" rx="10" fill="#16161e" stroke="#24283b" stroke-width="1.2"/>
<path d="M{WIN_X} {WIN_Y + 34} V{WIN_Y + 10} a10 10 0 0 1 10 -10 H{WIN_X + win_w - 10} a10 10 0 0 1 10 10 V{WIN_Y + 34} Z" fill="#1f2335"/>

<!-- traffic light controls -->
<circle cx="{WIN_X + 18}" cy="{WIN_Y + 17}" r="6" fill="#f7768e"/>
<circle cx="{WIN_X + 38}" cy="{WIN_Y + 17}" r="6" fill="#e0af68"/>
<circle cx="{WIN_X + 58}" cy="{WIN_Y + 17}" r="6" fill="#9ece6a"/>

<!-- window title -->
<text x="{W / 2}" y="{WIN_Y + 22}" text-anchor="middle" font-size="12" fill="#7aa2f7" font-weight="500">{escape(USER)}@{HOST}: ~</text>

<!-- animated content -->
{chr(10).join(body)}
</svg>
'''

    with open("terminal.svg", "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"[OK] terminal.svg written ({len(svg) / 1024:.1f} KB, animation ~{t:.1f}s)")


if __name__ == "__main__":
    generate()
