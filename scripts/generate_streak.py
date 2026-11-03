
import os
import json
import urllib.request
from datetime import date, datetime, timedelta
from html import escape

USERNAME = "likhith3035"
TOKEN = os.environ["GH_TOKEN"]
OUTPUT = "streak.svg"

def fetch_contributions():
    query = """
    query($login: String!) {
      user(login: $login) {
        createdAt
        contributionsCollection {
          contributionCalendar {
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
        "query": query,
        "variables": {"login": USERNAME}
    }).encode()

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
    days = {}

    for week in user["contributionsCollection"]["contributionCalendar"]["weeks"]:
        for item in week["contributionDays"]:
            days[date.fromisoformat(item["date"])] = item["contributionCount"]

    return days


def calculate_streaks(days):
    active = sorted(d for d, count in days.items() if count > 0)

    if not active:
        return (0, None, None), (0, None)

    # Longest streak
    longest = 0
    best_start = best_end = None
    start = previous = active[0]
    length = 1

    for current in active[1:]:
        if current == previous + timedelta(days=1):
            length += 1
        else:
            if length > longest:
                longest = length
                best_start, best_end = start, previous

            start = current
            length = 1

        previous = current

    if length > longest:
        longest = length
        best_start, best_end = start, previous

    # Current streak: today or yesterday must be active
    today = date.today()

    if days.get(today, 0) > 0:
        current_end = today
    elif days.get(today - timedelta(days=1), 0) > 0:
        current_end = today - timedelta(days=1)
    else:
        return (longest, best_start, best_end), (0, None)

    current_start = current_end

    while days.get(current_start - timedelta(days=1), 0) > 0:
        current_start -= timedelta(days=1)

    current_length = (current_end - current_start).days + 1

    return (
        (longest, best_start, best_end),
        (current_length, current_start)
    )


def generate_svg(longest, current):
    longest_days, longest_start, longest_end = longest
    current_days, current_start = current

    def fmt(value):
        return value.strftime("%b %d, %Y") if value else "N/A"

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg"
    width="850" height="245" viewBox="0 0 850 245">
      <rect width="850" height="245" rx="18" fill="#0d1117"
        stroke="#30363d"/>

      <text x="35" y="43" fill="#8b949e"
        font-family="Arial" font-size="14"
        font-weight="bold" letter-spacing="2">
        LONGEST CONTRIBUTION STREAK
      </text>

      <text x="35" y="105" fill="#58a6ff"
        font-family="Arial" font-size="43"
        font-weight="bold">{longest_days} DAYS 🔥</text>

      <text x="35" y="151" fill="#8b949e"
        font-family="Arial" font-size="12">FROM</text>
      <text x="35" y="177" fill="#e6edf3"
        font-family="Arial" font-size="17"
        font-weight="bold">{escape(fmt(longest_start))}</text>

      <text x="345" y="151" fill="#8b949e"
        font-family="Arial" font-size="12">TO</text>
      <text x="345" y="177" fill="#e6edf3"
        font-family="Arial" font-size="17"
        font-weight="bold">{escape(fmt(longest_end))}</text>

      <line x1="35" y1="195" x2="815" y2="195"
        stroke="#30363d"/>

      <text x="35" y="225" fill="#3fb950"
        font-family="Arial" font-size="15"
        font-weight="bold">
        CURRENT STREAK: {current_days} DAYS
      </text>

      <text x="440" y="225" fill="#8b949e"
        font-family="Arial" font-size="13">
        Started: {escape(fmt(current_start))}
      </text>
    </svg>"""

    with open(OUTPUT, "w", encoding="utf-8") as file:
        file.write(svg)


def main():
    days = fetch_contributions()
    longest, current = calculate_streaks(days)
    generate_svg(longest, current)
    print("Streak card generated successfully!")


if __name__ == "__main__":
    main()
