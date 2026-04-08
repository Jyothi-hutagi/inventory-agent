"""
Report Sub-Agent
Formats raw BigQuery data into clear, structured inventory reports.
Called by the root agent when it needs a polished multi-section response.
"""
from google.adk.agents import Agent


def make_report_agent() -> Agent:
    """Returns a fresh Agent instance each call to avoid parent-conflict errors."""
    return Agent(
        name="inventory_report_agent",
        model="gemini-2.5-flash",
        description=(
            "Formats raw inventory data into clean, human-readable reports with "
            "highlights, alerts, and actionable recommendations."
        ),
        instruction="""
You are an inventory report formatter for a manufacturing company.

When you receive raw data (JSON or structured text), convert it into a
well-structured report with these sections as applicable:

📊 SUMMARY
- 2-3 bullet highlights from the data

⚠️ ALERTS
- Flag critical items (stock below 50% of reorder level)
- Flag delayed purchase orders

✅ RECOMMENDED ACTIONS
- Suggest immediate reorder for critical items
- Suggest expediting delayed POs

Always use INR (₹) for currency values.
Keep the tone professional but concise — factory managers are busy.
Never invent data — only use what you are given.
""",
    )