"""Simple call analytics dashboard for Sehat Sathi.

Run with:
    uv run python src/dashboard.py

Then open http://localhost:5050 in your browser.

Reads real call data from the same SQLite database the agent writes to
(callers.db, calls table). Does not display any caller-identifying or
sensitive information - only aggregate counts.
"""

from flask import Flask

import db

app = Flask(__name__)

PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta http-equiv="refresh" content="5" />
  <title>Sehat Sathi - Call Analytics</title>
  <style>
    body {{
      font-family: -apple-system, Segoe UI, Roboto, sans-serif;
      background: #f4faf9;
      margin: 0;
      padding: 40px;
      display: flex;
      flex-direction: column;
      align-items: center;
    }}
    h1 {{
      color: #0F9D8C;
      margin-bottom: 4px;
    }}
    p.sub {{
      color: #555;
      margin-top: 0;
    }}
    .cards {{
      display: flex;
      gap: 24px;
      margin-top: 32px;
      flex-wrap: wrap;
      justify-content: center;
    }}
    .card {{
      background: white;
      border-radius: 16px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.08);
      padding: 32px 48px;
      text-align: center;
      min-width: 180px;
    }}
    .card .number {{
      font-size: 48px;
      font-weight: 700;
    }}
    .card .label {{
      margin-top: 8px;
      color: #666;
      font-size: 14px;
      text-transform: uppercase;
      letter-spacing: 1px;
    }}
    .total .number {{ color: #333; }}
    .success .number {{ color: #0F9D8C; }}
    .failed .number {{ color: #d9534f; }}
    .footer {{
      margin-top: 40px;
      color: #999;
      font-size: 12px;
    }}
  </style>
</head>
<body>
  <h1>Sehat Sathi - Call Analytics</h1>
  <p class="sub">Live counts from real agent calls. Auto-refreshes every 5 seconds.</p>
  <div class="cards">
    <div class="card total">
      <div class="number">{total}</div>
      <div class="label">Total Calls</div>
    </div>
    <div class="card success">
      <div class="number">{successful}</div>
      <div class="label">Successful Calls</div>
    </div>
    <div class="card failed">
      <div class="number">{failed}</div>
      <div class="label">Failed Calls</div>
    </div>
  </div>
  <p class="footer">No caller-identifying or sensitive information is shown on this dashboard.</p>
</body>
</html>
"""


@app.route("/")
def dashboard():
    stats = db.get_call_stats()
    return PAGE_TEMPLATE.format(
        total=stats["total"],
        successful=stats["successful"],
        failed=stats["failed"],
    )


if __name__ == "__main__":
    db.init_db()
    app.run(host="0.0.0.0", port=5050, debug=False)
