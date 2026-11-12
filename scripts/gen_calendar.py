"""Builds iOS-style contribution calendars (light + dark SVG) for the profile.
Run by .github/workflows/calendar.yml with GITHUB_TOKEN; without a token it writes an empty placeholder."""
import os, json, random, urllib.request, datetime as dt
USER = "i-Sush"
OUT_DIRS = ["assets", "docs"]
FONT = '-apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Inter, Roboto, Arial, sans-serif'
TH = {
 "light": dict(bg="#F5F5F7", st="#E5E5EA", tx="#1D1D1F", sub="#6E6E73", lv=["#E4E4E9", "#BBDCFF", "#6DB4FF", "#2F8DFF", "#0057C2"]),
 "dark":  dict(bg="#1C1C1E", st="#2C2C2E", tx="#F5F5F7", sub="#A1A1A6", lv=["#2C2C2E", "#0F3D6E", "#155FA8", "#2A85E8", "#64B5FF"]),
}
Q = "query($u:String!){user(login:$u){contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount weekday}}}}}}"

def fetch():
    req = urllib.request.Request("https://api.github.com/graphql",
        data=json.dumps({"query": Q, "variables": {"u": USER}}).encode(),
        headers={"Authorization": "bearer " + os.environ["GITHUB_TOKEN"], "Content-Type": "application/json", "User-Agent": "calendar-gen"})
    cal = json.load(urllib.request.urlopen(req, timeout=30))["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    return [[(d["date"], d["contributionCount"], d["weekday"]) for d in w["contributionDays"]] for w in cal["weeks"]], cal["totalContributions"]

def blank(mock=False):
    end = dt.date.today(); start = end - dt.timedelta(days=364)
    start -= dt.timedelta(days=(start.weekday() + 1) % 7)
    weeks, d = [], start
    while d <= end:
        wk = []
        for _ in range(7):
            if d <= end: wk.append((d.isoformat(), random.choice([0, 0, 0, 1, 2, 4, 7]) if mock else 0, (d.weekday() + 1) % 7))
            d += dt.timedelta(days=1)
        weeks.append(wk)
    return weeks, sum(c for w in weeks for _, c, _ in w)

def render(weeks, total, t, note=None):
    C, G, L, TOP = 10, 3, 40, 58; S = C + G
    W = L + len(weeks) * S + 20; H = TOP + 7 * S + 46
    mx = max((c for w in weeks for _, c, _ in w), default=0)
    lv = lambda c: 0 if c == 0 else 1 + min(3, int((c - 1) * 4 / max(mx, 1)))
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Contribution calendar for {USER}" font-family=\'{FONT}\'>',
         f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="24" fill="{t["bg"]}" stroke="{t["st"]}"/>',
         f'<text x="{L-18}" y="32" font-size="15" font-weight="600" fill="{t["tx"]}">{note or f"{total} contributions in the last year"}</text>']
    prev = None
    for i, wk in enumerate(weeks):
        m = dt.date.fromisoformat(wk[0][0]).month
        if m != prev and i < len(weeks) - 2:
            o.append(f'<text x="{L+i*S}" y="{TOP-8}" font-size="10.5" fill="{t["sub"]}">{dt.date(2000, m, 1):%b}</text>')
        prev = m
        for date, c, wd in wk:
            o.append(f'<rect x="{L+i*S}" y="{TOP+wd*S}" width="{C}" height="{C}" rx="2.6" fill="{t["lv"][lv(c)]}"><title>{c} contributions on {date}</title></rect>')
    for wd, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        o.append(f'<text x="{L-8}" y="{TOP+wd*S+9}" font-size="10" fill="{t["sub"]}" text-anchor="end">{name}</text>')
    lx = W - 20 - (5 * S + 70)
    o.append(f'<text x="{lx}" y="{H-16}" font-size="10.5" fill="{t["sub"]}">Less</text>')
    for k in range(5): o.append(f'<rect x="{lx+30+k*S}" y="{H-25}" width="{C}" height="{C}" rx="2.6" fill="{t["lv"][k]}"/>')
    o.append(f'<text x="{lx+34+5*S}" y="{H-16}" font-size="10.5" fill="{t["sub"]}">More</text></svg>')
    return "\n".join(o)

if __name__ == "__main__":
    note = None
    if os.environ.get("GITHUB_TOKEN"): weeks, total = fetch()
    elif os.environ.get("MOCK"): weeks, total = blank(True)
    else: weeks, total = blank(); note = "Calendar updates daily. Run the workflow once to start."
    for d in OUT_DIRS:
        os.makedirs(d, exist_ok=True)
        for name, t in TH.items():
            open(f"{d}/calendar-{name}.svg", "w", encoding="utf-8").write(render(weeks, total, t, note))
    print("calendar written:", total, "contributions")
