from jinja2 import Template

TEMPLATE = Template("""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Payroll Migration Validation Report</title>
<style>
  body { font-family: -apple-system, Segoe UI, Arial, sans-serif; margin: 40px; color: #1a1a1a; }
  h1 { font-size: 22px; } h2 { font-size: 17px; margin-top: 32px; }
  .summary { display: flex; gap: 16px; margin: 16px 0 24px; }
  .stat { background: #f4f5f7; border-radius: 8px; padding: 12px 18px; min-width: 140px; }
  .stat .n { font-size: 24px; font-weight: 600; }
  .stat .l { font-size: 12px; color: #555; }
  table { border-collapse: collapse; width: 100%; margin-bottom: 24px; font-size: 13px; }
  th, td { border: 1px solid #e0e0e0; padding: 6px 10px; text-align: left; }
  th { background: #fafafa; }
  .ok { color: #1a7f37; }
</style>
</head>
<body>
<h1>Payroll Migration Validation Report</h1>
<p>Generated {{ generated_at }} &mdash; legacy vs target reconciliation</p>
<div class="summary">
  <div class="stat"><div class="n">{{ duplicate_count }}</div><div class="l">Duplicate rows</div></div>
  <div class="stat"><div class="n">{{ missing_count }}</div><div class="l">Missing-field rows</div></div>
  <div class="stat"><div class="n">{{ mismatch_count }}</div><div class="l">Total mismatches</div></div>
</div>

<h2>Duplicates ({{ duplicate_count }})</h2>
{% if duplicates %}
<table><tr>{% for c in duplicate_cols %}<th>{{ c }}</th>{% endfor %}</tr>
{% for row in duplicates %}<tr>{% for c in duplicate_cols %}<td>{{ row[c] }}</td>{% endfor %}</tr>{% endfor %}
</table>
{% else %}<p class="ok">None found.</p>{% endif %}

<h2>Missing Required Fields ({{ missing_count }})</h2>
{% if missing %}
<table><tr>{% for c in missing_cols %}<th>{{ c }}</th>{% endfor %}</tr>
{% for row in missing %}<tr>{% for c in missing_cols %}<td>{{ row[c] }}</td>{% endfor %}</tr>{% endfor %}
</table>
{% else %}<p class="ok">None found.</p>{% endif %}

<h2>Total Mismatches ({{ mismatch_count }})</h2>
{% if mismatches %}
<table><tr><th>employee_id</th><th>issues</th></tr>
{% for row in mismatches %}<tr><td>{{ row.employee_id }}</td><td>{{ row.issues }}</td></tr>{% endfor %}
</table>
{% else %}<p class="ok">None found.</p>{% endif %}

</body>
</html>
""")


def render_html(duplicates, missing, mismatches) -> str:
    duplicate_cols = list(duplicates[0].keys()) if duplicates else []
    missing_cols = list(missing[0].keys()) if missing else []
    import datetime
    return TEMPLATE.render(
        generated_at=datetime.datetime.utcnow().isoformat() + "Z",
        duplicates=duplicates, duplicate_cols=duplicate_cols, duplicate_count=len(duplicates),
        missing=missing, missing_cols=missing_cols, missing_count=len(missing),
        mismatches=mismatches, mismatch_count=len(mismatches),
    )
