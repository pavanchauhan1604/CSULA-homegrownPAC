"""Generate a cross-domain master HTML dashboard for PDF accessibility.

Reads every timestamped .xlsx report for every domain found in the
OneDrive/local folder (same data source as historical_analysis.py), then
produces a single self-contained HTML dashboard showing:

  • Aggregate totals — unique PDFs, high-priority PDFs, overall compliance %
  • Trend insights  — how many domains are improving / declining / stable
  • Snapshot charts — compliance % and high-priority counts per domain
  • Historical charts — aggregate compliance over time + per-domain trend lines
  • Domain table     — sortable summary with colour-coded status and trend arrows
  • Domain cards     — per-domain metrics + mini compliance trend chart

The report is saved to <source-folder>/Master/master_report.html and overwrites
the previous version on every run, so Teams/OneDrive will sync the latest copy
automatically.

Usage
-----
    # Default — reads from TEAMS_ONEDRIVE_PATH set in config.py:
    python scripts/generate_master_report_html.py

    # Arbitrary local folder:
    python scripts/generate_master_report_html.py --source local --local-path /path/to/folder

    # Filter to specific domains only:
    python scripts/generate_master_report_html.py --domains www.calstatela.edu_admissions

    # Write the HTML somewhere other than the source folder:
    python scripts/generate_master_report_html.py --output /tmp/master.html
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import config
from scripts.historical_analysis import collect_from_local

# Chart.js colour palette — CSULA navy first, then accessible contrasting colours
_CHART_COLORS = [
    "#003262", "#C4820E", "#27ae60", "#e67e22",
    "#8e44ad", "#16a085", "#c0392b", "#2980b9",
    "#229954", "#d4ac0d",
]

# =============================================================================
# Helpers
# =============================================================================

def _js(obj: Any) -> str:
    """HTML-safe JSON serialisation for embedding in <script> blocks.

    Escapes <, >, & so that error-message text like </script> or <!-- cannot
    break the enclosing HTML <script> tag.
    """
    return (
        json.dumps(obj, default=str)
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )


def _anchor(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "-", s)


def _latest(scans: list[dict]) -> dict:
    return scans[-1]


def _pct_cls(pct: float) -> str:
    """CSS modifier for a compliance percentage: good / warn / bad."""
    if pct >= 80:
        return "good"
    if pct >= 50:
        return "warn"
    return "bad"


def _trend_arrow(scans: list[dict]) -> tuple[str, str]:
    """(display_text, css_class) for overall compliance trend."""
    if len(scans) < 2:
        return "—", "trend-flat"
    diff = scans[-1]["compliance_pct"] - scans[0]["compliance_pct"]
    if diff > 2:
        return f"↑ +{diff:.1f}%", "trend-up"
    if diff < -2:
        return f"↓ {diff:.1f}%", "trend-down"
    return f"→ {diff:+.1f}%", "trend-flat"


# =============================================================================
# Aggregate data helpers
# =============================================================================

def aggregate_stats(domain_data: dict[str, list[dict]]) -> dict:
    """Compute summary metrics from the latest scan of every domain."""
    items = list(domain_data.items())
    total_pdfs     = sum(_latest(s)["unique_pdfs"]       for _, s in items)
    total_compliant= sum(_latest(s)["compliant_scanned"] for _, s in items)
    total_high     = sum(_latest(s)["high_priority"]     for _, s in items)
    total_viol     = sum(_latest(s)["violations_total"]  for _, s in items)
    compliance_pct = round(total_compliant / total_pdfs * 100, 1) if total_pdfs else 0.0

    improving   = sum(1 for _, s in items if len(s) >= 2 and s[-1]["compliance_pct"] - s[0]["compliance_pct"] >  2)
    declining   = sum(1 for _, s in items if len(s) >= 2 and s[-1]["compliance_pct"] - s[0]["compliance_pct"] < -2)
    stable      = sum(1 for _, s in items if len(s) >= 2 and abs(s[-1]["compliance_pct"] - s[0]["compliance_pct"]) <= 2)
    single_scan = sum(1 for _, s in items if len(s) < 2)

    return dict(
        total_domains=len(items),
        total_pdfs=total_pdfs,
        total_compliant=total_compliant,
        total_high=total_high,
        total_violations=total_viol,
        compliance_pct=compliance_pct,
        improving=improving,
        declining=declining,
        stable=stable,
        single_scan=single_scan,
    )


def _agg_over_time(domain_data: dict[str, list[dict]]):
    """Aggregate compliance % over time using the cumulative latest scan per domain.

    For each unique scan date D, each domain contributes its most recent scan
    at or before D.  This gives a smoothly evolving aggregate even when domains
    are scanned on different days.

    Returns: (date_strings, compliance_pcts, total_pdfs, high_priority_counts)
    """
    all_dates: set[str] = set()
    for scans in domain_data.values():
        for s in scans:
            all_dates.add(s["timestamp"].strftime("%Y-%m-%d"))
    sorted_dates = sorted(all_dates)

    agg_pct:   list[float] = []
    agg_total: list[int]   = []
    agg_high:  list[int]   = []

    for date_str in sorted_dates:
        tot_pdfs = tot_comp = tot_high = 0
        for scans in domain_data.values():
            match = [s for s in scans if s["timestamp"].strftime("%Y-%m-%d") <= date_str]
            if match:
                s = match[-1]
                tot_pdfs += s["unique_pdfs"]
                tot_comp += s["compliant_scanned"]
                tot_high += s["high_priority"]
        pct = round(tot_comp / tot_pdfs * 100, 1) if tot_pdfs else 0.0
        agg_pct.append(pct)
        agg_total.append(tot_pdfs)
        agg_high.append(tot_high)

    return sorted_dates, agg_pct, agg_total, agg_high


def _domain_trend_datasets(domain_data: dict[str, list[dict]]):
    """Per-domain compliance % over time — one Chart.js dataset per domain."""
    all_dates: set[str] = set()
    for scans in domain_data.values():
        for s in scans:
            all_dates.add(s["timestamp"].strftime("%Y-%m-%d"))
    sorted_dates = sorted(all_dates)

    datasets = []
    for i, (domain, scans) in enumerate(sorted(domain_data.items())):
        points = []
        for date_str in sorted_dates:
            match = [s for s in scans if s["timestamp"].strftime("%Y-%m-%d") <= date_str]
            points.append(match[-1]["compliance_pct"] if match else None)
        color = _CHART_COLORS[i % len(_CHART_COLORS)]
        datasets.append({
            "label": domain,
            "data": points,
            "borderColor": color,
            "backgroundColor": color + "33",
            "tension": 0.3,
            "fill": False,
            "spanGaps": True,
        })
    return sorted_dates, datasets


# =============================================================================
# HTML building
# =============================================================================

def _domain_card(domain: str, scans: list[dict], idx: int) -> str:
    """Build the per-domain detail card HTML (with optional mini trend chart)."""
    latest = _latest(scans)
    trend_text, trend_cls = _trend_arrow(scans)
    pct_cls = _pct_cls(latest["compliance_pct"])

    badge_pct_cls  = pct_cls
    badge_high_cls = "warn" if latest["high_priority"] > 0 else "good"

    mini_chart = ""
    if len(scans) >= 2:
        chart_id  = f"dc-{idx}"
        dates_js  = _js([s["timestamp"].strftime("%Y-%m-%d") for s in scans])
        comp_js   = _js([s["compliance_pct"] for s in scans])
        target_js = _js([100] * len(scans))
        mini_chart = f"""<div class="mini-chart-wrap">
            <canvas id="{chart_id}"></canvas>
            <script>
            (function(){{
              if (typeof Chart === 'undefined') return;
              new Chart(document.getElementById('{chart_id}'), {{
                type: 'line',
                data: {{
                  labels: {dates_js},
                  datasets: [
                    {{ label: 'Compliance %', data: {comp_js},   borderColor: '#003262', backgroundColor: '#00326215', tension: 0.3, fill: true,  pointRadius: 4 }},
                    {{ label: 'Target 100%',  data: {target_js}, borderColor: '#b0b8c4', borderDash: [6,4],            pointRadius: 0, fill: false }}
                  ]
                }},
                options: {{
                  responsive: true,
                  plugins: {{ legend: {{ display: false }} }},
                  scales: {{ y: {{ min: 0, max: 100, ticks: {{ callback: function(v){{ return v + '%'; }} }} }} }}
                }}
              }});
            }})();
            </script>
          </div>"""

    return f"""<section id="{_anchor(domain)}" class="domain-card">
  <div class="domain-card-header">
    <span class="domain-name">{domain}</span>
    <div class="domain-badges">
      <span class="badge badge-{badge_pct_cls}">{latest['compliance_pct']:.1f}% compliant</span>
      <span class="badge badge-{badge_high_cls}">{latest['high_priority']} high priority</span>
      <span class="badge badge-flat {trend_cls}">{trend_text}</span>
    </div>
  </div>
  <div class="domain-card-body">
    <div class="domain-metrics">
      <div class="dm"><span class="dmv">{latest['unique_pdfs']}</span><span class="dml">Unique PDFs</span></div>
      <div class="dm"><span class="dmv">{latest['compliant_scanned']}</span><span class="dml">Compliant</span></div>
      <div class="dm"><span class="dmv dmv-{pct_cls}">{latest['compliance_pct']:.1f}%</span><span class="dml">Compliance</span></div>
      <div class="dm"><span class="dmv dmv-warn">{latest['high_priority']}</span><span class="dml">High Priority</span></div>
      <div class="dm"><span class="dmv">{latest['violations_total']}</span><span class="dml">Total Violations</span></div>
      <div class="dm"><span class="dmv">{latest['errors_per_page_avg']:.2f}</span><span class="dml">Avg Err/Page</span></div>
      <div class="dm"><span class="dmv">{len(scans)}</span><span class="dml">Scans on Record</span></div>
      <div class="dm"><span class="dmv">{latest['timestamp'].strftime('%Y-%m-%d')}</span><span class="dml">Latest Scan</span></div>
    </div>
    {mini_chart}
  </div>
  <a href="#top" class="back-link">↑ Back to top</a>
</section>"""


def build_html(domain_data: dict[str, list[dict]], generated_at: datetime) -> str:
    """Assemble the complete master HTML dashboard."""
    stats = aggregate_stats(domain_data)
    agg_dates, agg_pct, _, agg_high = _agg_over_time(domain_data)
    trend_dates, trend_datasets      = _domain_trend_datasets(domain_data)
    show_history = len(agg_dates) >= 2

    gen_str = generated_at.strftime("%B %d, %Y at %I:%M %p")

    # ── Insight banner ────────────────────────────────────────────────────────
    parts = []
    if stats["improving"]:
        parts.append(f"<strong>{stats['improving']}</strong> domain(s) improving")
    if stats["declining"]:
        parts.append(f"<strong>{stats['declining']}</strong> domain(s) declining")
    if stats["stable"]:
        parts.append(f"<strong>{stats['stable']}</strong> stable")
    if stats["single_scan"]:
        parts.append(f"<strong>{stats['single_scan']}</strong> with only 1 scan (no trend yet)")
    insight_text = " &nbsp;·&nbsp; ".join(parts) or "Not enough scan history to compare trends."
    insight_cls  = (
        "all-good" if not stats["declining"] and stats["compliance_pct"] >= 80
        else "has-bad" if stats["declining"]
        else ""
    )

    # ── Summary pills ─────────────────────────────────────────────────────────
    overall_cls = _pct_cls(stats["compliance_pct"])
    pills = f"""<div class="pills">
    <div class="pill"><div class="pv">{stats['total_domains']}</div><div class="pl">Domains Tracked</div></div>
    <div class="pill"><div class="pv">{stats['total_pdfs']}</div><div class="pl">Total Unique PDFs</div></div>
    <div class="pill {overall_cls}"><div class="pv">{stats['compliance_pct']:.1f}%</div><div class="pl">Overall Compliance</div></div>
    <div class="pill"><div class="pv">{stats['total_compliant']}</div><div class="pl">Compliant PDFs</div></div>
    <div class="pill bad"><div class="pv">{stats['total_high']}</div><div class="pl">High Priority PDFs</div></div>
    <div class="pill"><div class="pv">{stats['total_violations']}</div><div class="pl">Total Violations</div></div>
  </div>"""

    # ── Domain summary table ──────────────────────────────────────────────────
    domain_rows = ""
    for domain in sorted(domain_data):
        scans  = domain_data[domain]
        latest = _latest(scans)
        trend_text, trend_cls = _trend_arrow(scans)
        pct_cls = _pct_cls(latest["compliance_pct"])
        domain_rows += (
            f'<tr>'
            f'<td><a href="#{_anchor(domain)}">{domain}</a></td>'
            f'<td class="c">{len(scans)}</td>'
            f'<td class="c">{scans[0]["timestamp"].strftime("%Y-%m-%d")}</td>'
            f'<td class="c">{latest["timestamp"].strftime("%Y-%m-%d")}</td>'
            f'<td class="c">{latest["unique_pdfs"]}</td>'
            f'<td class="c status-{pct_cls}">{latest["compliance_pct"]:.1f}%</td>'
            f'<td class="c">{latest["compliant_scanned"]}/{latest["unique_pdfs"]}</td>'
            f'<td class="c high-col">{latest["high_priority"]}</td>'
            f'<td class="c {trend_cls}">{trend_text}</td>'
            f'</tr>\n'
        )

    # ── Snapshot bar charts ───────────────────────────────────────────────────
    sorted_domains = sorted(domain_data.keys())
    snap_comp = [_latest(domain_data[d])["compliance_pct"] for d in sorted_domains]
    snap_high = [_latest(domain_data[d])["high_priority"]  for d in sorted_domains]

    # Colour each bar by compliance status
    bar_bg_comp     = _js([("#1a6e3a99" if v >= 80 else "#C4820E99" if v >= 50 else "#8b000099") for v in snap_comp])
    bar_border_comp = _js([("#1a6e3a"   if v >= 80 else "#C4820E"   if v >= 50 else "#8b0000")   for v in snap_comp])

    # Chart canvas height scales with number of domains (min 260 px, +22 px/domain)
    bar_height = max(260, 22 * len(sorted_domains))

    snapshot_block = f"""<div class="charts-grid-2">
  <div class="chart-box">
    <h3 class="chart-title">Compliance % by Domain — Latest Scan</h3>
    <div style="height:{bar_height}px"><canvas id="snap-comp-chart"></canvas></div>
  </div>
  <div class="chart-box">
    <h3 class="chart-title">High Priority PDFs by Domain — Latest Scan</h3>
    <div style="height:{bar_height}px"><canvas id="snap-high-chart"></canvas></div>
  </div>
</div>
<script>
(function(){{
  if (typeof Chart === 'undefined') {{
    console.error('Chart.js failed to load — charts will not render.');
    return;
  }}
  var labels = {_js(sorted_domains)};
  new Chart(document.getElementById('snap-comp-chart'), {{
    type: 'bar',
    data: {{
      labels: labels,
      datasets: [{{
        label: 'Compliance %',
        data: {_js(snap_comp)},
        backgroundColor: {bar_bg_comp},
        borderColor: {bar_border_comp},
        borderWidth: 1
      }}]
    }},
    options: {{
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{ legend: {{ display: false }} }},
      scales: {{ x: {{ min: 0, max: 100, ticks: {{ callback: function(v){{ return v + '%'; }} }} }} }}
    }}
  }});
  new Chart(document.getElementById('snap-high-chart'), {{
    type: 'bar',
    data: {{
      labels: labels,
      datasets: [{{
        label: 'High Priority PDFs',
        data: {_js(snap_high)},
        backgroundColor: '#8b000066',
        borderColor: '#8b0000',
        borderWidth: 1
      }}]
    }},
    options: {{
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{ legend: {{ display: false }} }},
      scales: {{ x: {{ beginAtZero: true }} }}
    }}
  }});
}})();
</script>"""

    # ── Historical trend charts (only when ≥ 2 unique scan dates exist) ───────
    history_block = ""
    if show_history:
        history_block = f"""<h2 class="section-head">Historical Trends</h2>
<div class="charts-grid-hist">
  <div class="chart-box chart-col-2">
    <h3 class="chart-title">Overall Compliance % Over Time (All Domains Combined)</h3>
    <canvas id="agg-comp-chart"></canvas>
  </div>
  <div class="chart-box">
    <h3 class="chart-title">High Priority PDFs Over Time</h3>
    <canvas id="agg-high-chart"></canvas>
  </div>
</div>
<div class="chart-box chart-full-row">
  <h3 class="chart-title">Per-Domain Compliance % Over Time</h3>
  <canvas id="domain-trend-chart"></canvas>
</div>
<script>
(function(){{
  if (typeof Chart === 'undefined') return;
  new Chart(document.getElementById('agg-comp-chart'), {{
    type: 'line',
    data: {{
      labels: {_js(agg_dates)},
      datasets: [
        {{ label: 'Overall Compliance %', data: {_js(agg_pct)},  borderColor: '#27ae60', backgroundColor: '#27ae6018', tension: 0.3, fill: true }},
        {{ label: 'Target 100%',          data: {_js([100]*len(agg_dates))}, borderColor: '#b0b8c4', borderDash: [6,4], pointRadius: 0, fill: false }}
      ]
    }},
    options: {{
      responsive: true,
      plugins: {{ legend: {{ position: 'top' }} }},
      scales: {{ y: {{ min: 0, max: 100, ticks: {{ callback: function(v){{ return v + '%'; }} }} }} }}
    }}
  }});
  new Chart(document.getElementById('agg-high-chart'), {{
    type: 'bar',
    data: {{
      labels: {_js(agg_dates)},
      datasets: [{{ label: 'High Priority PDFs', data: {_js(agg_high)}, backgroundColor: '#8b000099', borderColor: '#8b0000', borderWidth: 1 }}]
    }},
    options: {{
      responsive: true,
      plugins: {{ legend: {{ position: 'top' }} }},
      scales: {{ y: {{ beginAtZero: true }} }}
    }}
  }});
  new Chart(document.getElementById('domain-trend-chart'), {{
    type: 'line',
    data: {{
      labels: {_js(trend_dates)},
      datasets: {_js(trend_datasets)}
    }},
    options: {{
      responsive: true,
      plugins: {{ legend: {{ position: 'bottom', labels: {{ boxWidth: 12, font: {{ size: 10 }} }} }} }},
      scales: {{ y: {{ min: 0, max: 100, ticks: {{ callback: function(v){{ return v + '%'; }} }} }} }}
    }}
  }});
}})();
</script>"""

    # ── Per-domain cards ──────────────────────────────────────────────────────
    cards_html = "\n".join(
        _domain_card(domain, domain_data[domain], idx)
        for idx, domain in enumerate(sorted(domain_data))
    )

    # ── Nav links ─────────────────────────────────────────────────────────────
    nav_links = "\n".join(
        f'<a href="#{_anchor(d)}">{d}</a>' for d in sorted(domain_data)
    )

    # ── Assemble ──────────────────────────────────────────────────────────────
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CSULA PDF Accessibility — Master Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:Arial,"Segoe UI",sans-serif;background:#f2f2f2;color:#1a1a1a;font-size:14px;line-height:1.5}}
/* ── Header & Nav ── */
header{{background:#111111;color:#fff;padding:26px 44px;border-bottom:4px solid #C4820E}}
header h1{{font-size:1.5rem;font-weight:700;letter-spacing:.01em}}
header p{{font-size:.82rem;color:#aaa;margin-top:6px}}
nav{{background:#1a1a1a;border-bottom:2px solid #C4820E;padding:10px 44px;display:flex;flex-wrap:wrap;gap:16px;position:sticky;top:0;z-index:10;overflow-x:auto}}
nav a{{color:#C4820E;text-decoration:none;font-size:.78rem;font-weight:600;white-space:nowrap;letter-spacing:.02em}}
nav a:hover{{color:#fff}}
.nav-sep{{color:#444;padding:0 4px}}
/* ── Layout ── */
.wrap{{max-width:1400px;margin:0 auto;padding:30px 44px}}
/* ── Pills ── */
.pills{{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:24px}}
.pill{{background:#fff;border:1px solid #d0d0d0;border-top:3px solid #C4820E;border-radius:4px;padding:18px 26px;text-align:center;min-width:140px;box-shadow:0 1px 4px rgba(0,0,0,.08)}}
.pill.good{{border-top-color:#1a6e3a}}.pill.warn{{border-top-color:#C4820E}}.pill.bad{{border-top-color:#8b0000}}
.pv{{font-size:2.1rem;font-weight:700;color:#111;line-height:1}}
.pill.good .pv{{color:#1a6e3a}}.pill.warn .pv{{color:#7a4f00}}.pill.bad .pv{{color:#8b0000}}
.pl{{font-size:.7rem;color:#666;margin-top:5px;text-transform:uppercase;letter-spacing:.05em}}
/* ── Insight banner ── */
.insight{{background:#fff;border-left:4px solid #C4820E;border-radius:4px;padding:14px 20px;margin-bottom:28px;font-size:.9rem;color:#333;box-shadow:0 1px 4px rgba(0,0,0,.06)}}
.insight.all-good{{border-left-color:#1a6e3a}}.insight.has-bad{{border-left-color:#8b0000}}
/* ── Section headings ── */
.section-head{{font-size:.82rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#111;border-left:3px solid #C4820E;padding-left:10px;margin:32px 0 16px}}
/* ── Tables ── */
.tbl-wrap{{background:#fff;border-radius:4px;border:1px solid #d0d0d0;overflow:auto;margin-bottom:32px;box-shadow:0 1px 4px rgba(0,0,0,.06)}}
table{{width:100%;border-collapse:collapse;font-size:.855rem}}
th{{background:#111111;color:#C4820E;padding:10px 14px;text-align:left;white-space:nowrap;font-weight:700;font-size:.78rem;text-transform:uppercase;letter-spacing:.06em}}
td{{padding:9px 14px;border-bottom:1px solid #ebebeb;color:#222}}
tr:last-child td{{border-bottom:none}}
tr:nth-child(even) td{{background:#fafafa}}
tr:hover td{{background:#fff8ee}}
.c{{text-align:center}}
.trend-up{{color:#1a6e3a;font-weight:700}}.trend-down{{color:#8b0000;font-weight:700}}.trend-flat{{color:#888}}
.status-good{{color:#1a6e3a;font-weight:700}}.status-warn{{color:#7a4f00;font-weight:700}}.status-bad{{color:#8b0000;font-weight:700}}
.high-col{{color:#8b0000;font-weight:600}}
/* ── Chart grids ── */
.charts-grid-2{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:24px}}
.charts-grid-hist{{display:grid;grid-template-columns:2fr 1fr;gap:20px;margin-bottom:20px}}
.chart-box{{background:#fff;border:1px solid #d0d0d0;border-radius:4px;padding:18px;box-shadow:0 1px 3px rgba(0,0,0,.05)}}
.chart-col-2{{grid-column:1/2}}.chart-full-row{{background:#fff;border:1px solid #d0d0d0;border-radius:4px;padding:18px;margin-bottom:28px;box-shadow:0 1px 3px rgba(0,0,0,.05)}}
.chart-title{{font-size:.75rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#111;border-left:2px solid #C4820E;padding-left:8px;margin-bottom:14px}}
/* ── Domain cards ── */
.domain-card{{background:#fff;border-radius:4px;border:1px solid #d0d0d0;border-top:4px solid #C4820E;padding:22px 28px;margin-bottom:22px;box-shadow:0 2px 6px rgba(0,0,0,.06)}}
.domain-card-header{{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;margin-bottom:14px;padding-bottom:12px;border-bottom:1px solid #ebebeb}}
.domain-name{{font-size:1rem;font-weight:700;color:#111}}
.domain-badges{{display:flex;gap:8px;flex-wrap:wrap}}
.badge{{padding:3px 10px;border-radius:20px;font-size:.72rem;font-weight:700;border:1px solid transparent}}
.badge-good{{background:#e6f4eb;color:#1a6e3a;border-color:#b2dfcc}}
.badge-warn{{background:#fff3e0;color:#7a4f00;border-color:#ffd699}}
.badge-bad{{background:#fdecea;color:#8b0000;border-color:#f5b8b5}}
.badge-flat{{background:#f0f0f0;color:#555;border-color:#d0d0d0}}
.domain-card-body{{display:flex;gap:24px;align-items:flex-start;flex-wrap:wrap}}
.domain-metrics{{display:flex;flex-wrap:wrap;gap:10px}}
.dm{{background:#fafafa;border:1px solid #e8e8e8;border-radius:4px;padding:10px 14px;text-align:center;min-width:96px}}
.dmv{{display:block;font-size:1.25rem;font-weight:700;color:#111;line-height:1.2}}
.dmv-good{{color:#1a6e3a}}.dmv-warn{{color:#7a4f00}}.dmv-bad{{color:#8b0000}}
.dml{{display:block;font-size:.67rem;color:#666;margin-top:3px;text-transform:uppercase;letter-spacing:.04em}}
.mini-chart-wrap{{flex:1;min-width:240px;margin-top:4px}}
.mini-chart-wrap canvas{{max-height:160px}}
.back-link{{display:inline-block;margin-top:14px;font-size:.78rem;color:#C4820E;text-decoration:none;font-weight:600}}
.back-link:hover{{color:#111}}
/* ── Footer ── */
footer{{text-align:center;padding:24px;font-size:.75rem;color:#aaa;border-top:2px solid #C4820E;margin-top:10px;background:#111111}}
/* ── Responsive ── */
@media(max-width:900px){{
  .wrap{{padding:16px 18px}}
  header,nav{{padding-left:18px;padding-right:18px}}
  .charts-grid-2,.charts-grid-hist{{grid-template-columns:1fr}}
  .chart-col-2{{grid-column:auto}}
}}
</style>
</head>
<body id="top">
<header>
  <h1>CSULA PDF Accessibility — Master Dashboard</h1>
  <p>Generated: {gen_str} &nbsp;·&nbsp; {stats['total_domains']} domain(s) &nbsp;·&nbsp; {stats['total_pdfs']} total unique PDFs</p>
</header>
<nav>
  <a href="#summary">↑ Summary</a>
  <a href="#domains-table">All Domains</a>
  <span class="nav-sep">|</span>
  {nav_links}
</nav>
<div class="wrap">

  <!-- ── Summary ── -->
  <div id="summary">
    {pills}
    <div class="insight {insight_cls}">
      <strong>Trend Insights:</strong> &nbsp; {insight_text}
    </div>
  </div>

  <!-- ── Snapshot Charts ── -->
  <h2 class="section-head">Latest Snapshot — All Domains</h2>
  {snapshot_block}

  <!-- ── Historical Trend Charts ── -->
  {history_block}

  <!-- ── Domain Summary Table ── -->
  <h2 class="section-head" id="domains-table">All Domains</h2>
  <div class="tbl-wrap">
    <table>
      <thead><tr>
        <th>Domain</th><th>Scans</th><th>First Scan</th><th>Latest Scan</th>
        <th>Unique PDFs</th><th>Compliance %</th><th>Compliant (LP/Total)</th>
        <th>High Priority</th><th>Trend</th>
      </tr></thead>
      <tbody>{domain_rows}</tbody>
    </table>
  </div>

  <!-- ── Domain Detail Cards ── -->
  <h2 class="section-head">Domain Details</h2>
  {cards_html}

</div>
<footer>CSULA PDF Accessibility Checker &nbsp;·&nbsp; {generated_at.year}</footer>
</body>
</html>"""


# =============================================================================
# Entry point
# =============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a cross-domain master HTML accessibility dashboard.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--source", choices=["onedrive", "local"], default="onedrive",
        help="'onedrive' (uses TEAMS_ONEDRIVE_PATH from config) or 'local' (requires --local-path)",
    )
    parser.add_argument("--local-path", metavar="PATH",
                        help="Root folder containing domain subfolders (--source=local)")
    parser.add_argument("--domains", nargs="+", metavar="DOMAIN",
                        help="Limit to specific domain(s); default is all subfolders")
    parser.add_argument("--output", metavar="PATH",
                        help="Output HTML path (default: <source-folder>/master_report.html)")
    args = parser.parse_args()

    domains = args.domains or None

    if args.source == "onedrive":
        raw = getattr(config, "TEAMS_ONEDRIVE_PATH", "")
        if not raw:
            print("ERROR: TEAMS_ONEDRIVE_PATH is not set in config.py")
            sys.exit(1)
        source_path = Path(raw)
        if not source_path.exists():
            print(f"ERROR: OneDrive path does not exist: {source_path}")
            print("Make sure your Teams channel Files folder is synced via OneDrive.")
            sys.exit(1)
    else:
        if not args.local_path:
            print("ERROR: --local-path is required when --source=local")
            sys.exit(1)
        source_path = Path(args.local_path)
        if not source_path.exists():
            print(f"ERROR: Path does not exist: {source_path}")
            sys.exit(1)

    print(f"Reading reports from: {source_path}\n")
    domain_data = collect_from_local(source_path, domains)

    if not domain_data:
        print(
            "\nNo scan data found. Make sure the folder contains domain subfolders "
            "with timestamped .xlsx files matching: {domain}-YYYY-MM-DD_HH-MM-SS.xlsx"
        )
        sys.exit(0)

    generated_at = datetime.now()
    html = build_html(domain_data, generated_at)

    if args.output:
        out_path = Path(args.output)
    else:
        master_dir = source_path / "Master"
        master_dir.mkdir(exist_ok=True)
        out_path = master_dir / "master_report.html"
    out_path.write_text(html, encoding="utf-8")

    stats = aggregate_stats(domain_data)
    print(f"\n[DONE] Master report saved → {out_path}")
    print(f"       {stats['total_domains']} domain(s)  |  "
          f"{stats['total_pdfs']} unique PDFs  |  "
          f"{stats['compliance_pct']:.1f}% overall compliance  |  "
          f"{stats['total_high']} high priority")
    if args.source == "onedrive":
        print("       OneDrive will sync it to Teams in the background.")


if __name__ == "__main__":
    main()
