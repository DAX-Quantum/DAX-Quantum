#!/usr/bin/env python3
"""
Generates terminal.svg: an animated Linux-desktop terminal for your GitHub profile.

Usage:
    1. Edit the CONFIG section below.
    2. Run:  python generate_terminal.py
    3. Commit the resulting terminal.svg to your <username>/<username> repo.
"""
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

# (repo_name, short_description, stack)
PROJECTS = [
    ("linux-server-health-audit", "Server health & resource monitor", "Bash"),
    ("linux-system-info-tool", "System telemetry & hardware info", "Bash"),
    ("Student_Record_System", "Student database & records manager", "C++"),
    ("Comic_book", "Comic showcase & reader web app", "React/JS"),
]

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


# Neofetch system info lines (padded consistently with colons)
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

BLOCKS = [
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
        out=[
            [
                ("drwxr-xr-x  ", "dim"),
                (name.ljust(27), "purple"),
                (desc.ljust(36), "fg"),
                (f"[{stack}]", "cyan"),
            ]
            for name, desc, stack in PROJECTS
        ],
    ),
    dict(
        cmd="./contact.sh",
        out=[[(f"{k}:".ljust(12), "blue"), (v, "fg")] for k, v in CONTACT],
    ),
]

PROMPT = [(f"{USER}@{HOST}", "green"), (":", "fg"), ("~", "blue"), ("$ ", "fg")]
PLEN = len(USER) + len(HOST) + 5  # chars in prompt


def tspans(segs):
    return "".join(f'<tspan fill="{C[c]}">{escape(t)}</tspan>' for t, c in segs)


def discrete(values):
    n = len(values) - 1
    vals = ";".join(f"{v:.1f}" for v in values)
    keys = ";".join(f"{i / n:.4f}" for i in range(n + 1))
    return vals, keys


body = []
defs = []
y = WIN_Y + 34 + 30  # first baseline
t = 0.8

for i, blk in enumerate(BLOCKS):
    cmd = blk["cmd"]
    n = len(cmd)
    pw = PLEN * CW
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

    # prompt + typed command (one text element, so alignment always matches)
    body.append(
        f'<g opacity="0"><set attributeName="opacity" to="1" begin="{t:.2f}s" fill="freeze"/>'
        f'<text x="{LEFT}" y="{y}" clip-path="url(#c{i})" xml:space="preserve">'
        f'{tspans(PROMPT)}<tspan fill="{C["fg"]}">{escape(cmd)}</tspan></text></g>'
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
    f'<set attributeName="opacity" to="1" begin="{t:.2f}s" fill="freeze"/>{tspans(PROMPT)}</text>'
)
body.append(
    f'<rect x="{LEFT + PLEN * CW:.1f}" y="{y - 13}" width="8" height="17" fill="{C["fg"]}" opacity="0">'
    f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1.1s" '
    f'begin="{t:.2f}s" repeatCount="indefinite"/></rect>'
)

H = y + 40
WIN_W = W - 2 * WIN_X
WIN_H = H - WIN_Y - 16

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H:.0f}" viewBox="0 0 {W} {H:.0f}" font-family="{FONT}" font-size="14">
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
<rect width="{W}" height="{H:.0f}" rx="12" fill="url(#wall)"/>
<rect width="{W}" height="{H:.0f}" rx="12" fill="url(#glow)"/>

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
<rect x="{WIN_X}" y="{WIN_Y + 3}" width="{WIN_W}" height="{WIN_H:.0f}" rx="10" fill="#000000" opacity="0.4"/>

<!-- terminal window body & titlebar -->
<rect x="{WIN_X}" y="{WIN_Y}" width="{WIN_W}" height="{WIN_H:.0f}" rx="10" fill="#16161e" stroke="#24283b" stroke-width="1.2"/>
<path d="M{WIN_X} {WIN_Y + 34} V{WIN_Y + 10} a10 10 0 0 1 10 -10 H{WIN_X + WIN_W - 10} a10 10 0 0 1 10 10 V{WIN_Y + 34} Z" fill="#1f2335"/>

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
print(f"terminal.svg written ({len(svg) / 1024:.1f} KB, animation ~{t:.1f}s)")
