
import os
import json
import urllib.request
from datetime import date, timedelta
from html import escape

USERNAME = "likhith3035"
TOKEN = os.environ["GH_TOKEN"]

QUERY = """
query($login: String!) {
    user(login: $login) {
        contributionsCollection {
            contributionCalendar {
                totalContributions
                weeks {
                    contributionDays {
                        date
                        contributionCount
                    }
                }
            }
        }
    }
}
"""

payload = json.dumps({
    "query": QUERY,
    "variables": {"login": USERNAME}
}).encode("utf-8")

request = urllib.request.Request(
    "https://api.github.com/graphql",
    data=payload,
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
)

with urllib.request.urlopen(request) as response:
    result = json.loads(response.read())

if result.get("errors"):
    raise RuntimeError(result["errors"])

user = result["data"]["user"]

if user is None:
    raise RuntimeError(f"GitHub user {USERNAME} not found.")

calendar = user["contributionsCollection"]["contributionCalendar"]

all_days = {
    day["date"]: day["contributionCount"]
    for week in calendar["weeks"]
    for day in week["contributionDays"]
}

# Last 365 days
end = date.today()
start = end - timedelta(days=364)

max_count = max(
    (count for day, count in all_days.items()
     if start.isoformat() <= day <= end.isoformat()),
    default=0
)

# Blue intensity palette
COLORS = [
    "#161B22",
    "#102A43",
    "#174A78",
    "#2176BD",
    "#60A5FA"
]


def get_color(count):
    if count == 0:
        return COLORS[0]

    if max_count == 0:
        return COLORS[0]

    level = min(4, (count * 4 + max_count - 1) // max_count)
    return COLORS[max(1, level)]


# Calendar layout: Sunday to Saturday
first_day = start - timedelta(
    days=(start.weekday() + 1) % 7
)

weeks = ((end - first_day).days // 7) + 1

CELL = 11
GAP = 3
STEP = CELL + GAP

LEFT = 35
TOP = 42
RIGHT = 20
BOTTOM = 38

WIDTH = LEFT + weeks * STEP + RIGHT
HEIGHT = TOP + 7 * STEP + BOTTOM

svg = [
    f'<svg xmlns="http://www.w3.org/2000/svg" '
    f'width="{WIDTH}" height="{HEIGHT}" '
    f'viewBox="0 0 {WIDTH} {HEIGHT}">',

    '<rect width="100%" height="100%" '
    'rx="10" fill="#0D1117"/>',

    '<style>'
    'text{font-family:Arial,Helvetica,sans-serif}'
    '</style>',

    f'<text x="{LEFT}" y="20" '
    'fill="#60A5FA" font-size="13" '
    'font-weight="bold">'
    '365 DAYS OF CONTRIBUTIONS'
    '</text>'
]

# Month labels
previous_month = None

for week in range(weeks):
    week_date = first_day + timedelta(days=week * 7)

    if week_date > end:
        continue

    if week_date.month != previous_month:
        x = LEFT + week * STEP

        svg.append(
            f'<text x="{x}" y="36" '
            'fill="#94A3B8" font-size="10">'
            f'{escape(week_date.strftime("%b"))}'
            '</text>'
        )

        previous_month = week_date.month


# Weekday labels
weekday_labels = {
    1: "Mon",
    3: "Wed",
    5: "Fri"
}

for row, label in weekday_labels.items():
    y = TOP + row * STEP + 9

    svg.append(
        f'<text x="4" y="{y}" '
        'fill="#64748B" font-size="9">'
        f'{label}'
        '</text>'
    )


# Contribution squares
current = first_day

while current <= end:
    day_string = current.isoformat()
    count = all_days.get(day_string, 0)

    column = (current - first_day).days // 7
    row = (current.weekday() + 1) % 7

    x = LEFT + column * STEP
    y = TOP + row * STEP

    color = get_color(count)

    svg.append(
        f'<rect x="{x}" y="{y}" '
        f'width="{CELL}" height="{CELL}" '
        f'rx="2" fill="{color}">'
        f'<title>{day_string}: '
        f'{count} contributions</title>'
        '</rect>'
    )

    current += timedelta(days=1)


# Legend
legend_y = HEIGHT - 21
legend_x = WIDTH - 145

svg.append(
    f'<text x="{legend_x - 30}" y="{legend_y + 9}" '
    'fill="#94A3B8" font-size="9">Less</text>'
)

for index, color in enumerate(COLORS):
    x = legend_x + index * 15

    svg.append(
        f'<rect x="{x}" y="{legend_y}" '
        'width="10" height="10" rx="2" '
        f'fill="{color}"/>'
    )

svg.append(
    f'<text x="{legend_x + 82}" y="{legend_y + 9}" '
    'fill="#94A3B8" font-size="9">More</text>'
)

# Attribution
svg.append(
    f'<text x="{WIDTH - 12}" y="{HEIGHT - 5}" '
    'text-anchor="end" fill="#64748B" '
    'font-size="9">© Likhith</text>'
)

svg.append('</svg>')

with open("heatmap.svg", "w", encoding="utf-8") as file:
    file.write("\n".join(svg))

print("Blue contribution heatmap generated successfully.")
print(f"Total contributions in GitHub calendar: "
      f"{calendar['totalContributions']}")
