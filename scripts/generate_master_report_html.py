"""Generate a cross-domain master HTML dashboard for PDF accessibility.

Reads every timestamped .xlsx report for every domain found in the OneDrive/local
folder and produces a single self-contained HTML dashboard saved to
<source-folder>/Master/master_report.html (overwritten on every run).

Usage
-----
    python scripts/generate_master_report_html.py
    python scripts/generate_master_report_html.py --source local --local-path /path/to/folder
    python scripts/generate_master_report_html.py --domains www.calstatela.edu_admissions
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

_CHART_COLORS = [
    "#003262", "#C4820E", "#27ae60", "#e67e22",
    "#8e44ad", "#16a085", "#c0392b", "#2980b9",
    "#229954", "#d4ac0d",
]

# =============================================================================
# Helpers
# =============================================================================

def _js(obj: Any) -> str:
    """HTML-safe JSON for <script> blocks — escapes <, >, & to prevent tag breakage."""
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
    if pct >= 80:
        return "good"
    if pct >= 50:
        return "warn"
    return "bad"


def _bar_color(pct: float) -> str:
    if pct >= 80:
        return "#1a6e3a"
    if pct >= 50:
        return "#C4820E"
    return "#8b0000"


def _trend_arrow(scans: list[dict]) -> tuple[str, str]:
    if len(scans) < 2:
        return "—", "neu"
    diff = scans[-1]["compliance_pct"] - scans[0]["compliance_pct"]
    if diff > 2:
        return f"↑ +{diff:.1f}%", "good"
    if diff < -2:
        return f"↓ {diff:.1f}%", "bad"
    return f"→ {diff:+.1f}%", "neu"


# =============================================================================
# Data aggregation
# =============================================================================

def aggregate_stats(domain_data: dict[str, list[dict]]) -> dict:
    items = list(domain_data.items())
    total_pdfs      = sum(_latest(s)["unique_pdfs"]       for _, s in items)
    total_compliant = sum(_latest(s)["compliant_scanned"] for _, s in items)
    total_high      = sum(_latest(s)["high_priority"]     for _, s in items)
    total_viol      = sum(_latest(s)["violations_total"]  for _, s in items)
    compliance_pct  = round(total_compliant / total_pdfs * 100, 1) if total_pdfs else 0.0

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
    """Cumulative aggregate compliance over time. Each date uses the latest
    scan at-or-before that date for every domain, so the series is smooth
    even when domains are scanned on different days."""
    all_dates: set[str] = set()
    for scans in domain_data.values():
        for s in scans:
            all_dates.add(s["timestamp"].strftime("%Y-%m-%d"))
    sorted_dates = sorted(all_dates)

    agg_pct:  list[float] = []
    agg_high: list[int]   = []

    for date_str in sorted_dates:
        tot_pdfs = tot_comp = tot_high = 0
        for scans in domain_data.values():
            match = [s for s in scans if s["timestamp"].strftime("%Y-%m-%d") <= date_str]
            if match:
                s = match[-1]
                tot_pdfs += s["unique_pdfs"]
                tot_comp += s["compliant_scanned"]
                tot_high += s["high_priority"]
        agg_pct.append(round(tot_comp / tot_pdfs * 100, 1) if tot_pdfs else 0.0)
        agg_high.append(tot_high)

    return sorted_dates, agg_pct, agg_high


def _domain_progress_table(domain_data: dict[str, list[dict]]) -> str:
    """HTML table: first scan → latest scan compliance change per domain (≥2 scans only)."""
    rows = []
    for domain, scans in domain_data.items():
        if len(scans) < 2:
            continue
        first  = scans[0]["compliance_pct"]
        latest = scans[-1]["compliance_pct"]
        delta  = latest - first
        rows.append((domain, first, latest, delta, len(scans)))

    if not rows:
        return (
            '<p style="color:#888;font-size:.85rem;padding:14px 0">'
            'Not enough scan history yet — each domain needs at least 2 scans to show progress.</p>'
        )

    # Biggest movers (improving or declining) first
    rows.sort(key=lambda r: abs(r[3]), reverse=True)

    html = (
        '<table class="prog-tbl"><thead><tr>'
        '<th>Domain</th>'
        '<th class="c">Baseline</th>'
        '<th class="c">Latest</th>'
        '<th class="c">Change</th>'
        '<th class="c">Scans</th>'
        '</tr></thead><tbody>'
    )
    for domain, first, latest, delta, n_scans in rows:
        if delta > 2:
            delta_html = f'<span class="prog-up">&#8593;&nbsp;+{delta:.1f}%</span>'
        elif delta < -2:
            delta_html = f'<span class="prog-dn">&#8595;&nbsp;{delta:.1f}%</span>'
        else:
            delta_html = f'<span class="prog-st">&#8594;&nbsp;{delta:+.1f}%</span>'
        html += (
            f'<tr>'
            f'<td><a href="#{_anchor(domain)}" class="domain-link">{domain}</a></td>'
            f'<td class="c"><span class="pval {_pct_cls(first)}">{first:.1f}%</span></td>'
            f'<td class="c"><span class="pval {_pct_cls(latest)}">{latest:.1f}%</span></td>'
            f'<td class="c">{delta_html}</td>'
            f'<td class="c" style="color:#999;font-size:.8rem">{n_scans}</td>'
            f'</tr>'
        )
    html += '</tbody></table>'
    return html


# =============================================================================
# JavaScript builders  (plain string concatenation — no f-string brace escaping)
# =============================================================================
# All JS is assembled here via concatenation so that literal JS braces never
# need to be doubled as {{ / }} inside Python f-strings.

def _chart_guard() -> str:
    return "if(typeof Chart==='undefined'){console.error('Chart.js not loaded');return;}"


def _pct_callback() -> str:
    return "function(v){return v+'%';}"


def _mini_chart_js(cid: str, dates_js: str, comp_js: str,
                   tgt_js: str, bar_color: str) -> str:
    """Inline Chart.js init script for one domain's mini trend chart."""
    return (
        '<canvas id="' + cid + '"></canvas>'
        '<script>(function(){'
        + _chart_guard() +
        'new Chart(document.getElementById("' + cid + '"),{'
        'type:"line",'
        'data:{labels:' + dates_js + ',datasets:['
        '{label:"Compliance %",data:' + comp_js + ','
        'borderColor:"' + bar_color + '",'
        'backgroundColor:"' + bar_color + '18",'
        'tension:0.3,fill:true,pointRadius:3},'
        '{label:"Target",data:' + tgt_js + ','
        'borderColor:"#ccc",borderDash:[5,4],pointRadius:0,fill:false}'
        ']},'
        'options:{responsive:true,'
        'plugins:{legend:{display:false}},'
        'scales:{y:{min:0,max:100,ticks:{callback:' + _pct_callback() + '}}}}'
        '});'
        '})();</script>'
    )


def _snapshot_js(sorted_domains: list[str], snap_comp: list[float],
                 snap_high: list[int], bar_bg: str, bar_border: str) -> str:
    """Chart.js init for the two snapshot bar charts (compliance + high-priority)."""
    lbl = _js(sorted_domains)
    return (
        '<script>(function(){'
        + _chart_guard() +
        'var lbl=' + lbl + ';'
        'new Chart(document.getElementById("snap-comp"),{'
        'type:"bar",'
        'data:{labels:lbl,datasets:[{'
        'label:"Compliance %",'
        'data:' + _js(snap_comp) + ','
        'backgroundColor:' + bar_bg + ','
        'borderColor:' + bar_border + ','
        'borderWidth:1'
        '}]},'
        'options:{indexAxis:"y",responsive:true,maintainAspectRatio:false,'
        'plugins:{legend:{display:false}},'
        'scales:{x:{min:0,max:100,ticks:{callback:' + _pct_callback() + '}}}}'
        '});'
        'new Chart(document.getElementById("snap-high"),{'
        'type:"bar",'
        'data:{labels:lbl,datasets:[{'
        'label:"High Priority",'
        'data:' + _js(snap_high) + ','
        'backgroundColor:"#8b000066",'
        'borderColor:"#8b0000",'
        'borderWidth:1'
        '}]},'
        'options:{indexAxis:"y",responsive:true,maintainAspectRatio:false,'
        'plugins:{legend:{display:false}},'
        'scales:{x:{beginAtZero:true}}}'
        '});'
        '})();</script>'
    )


def _history_js(agg_dates: list[str], agg_pct: list[float],
                agg_high: list[int]) -> str:
    """Chart.js init for the two aggregate historical charts."""
    tgt = _js([100] * len(agg_dates))
    return (
        '<script>(function(){'
        + _chart_guard() +
        # Overall compliance line chart
        'new Chart(document.getElementById("agg-comp"),{'
        'type:"line",'
        'data:{labels:' + _js(agg_dates) + ',datasets:['
        '{label:"Overall Compliance %",'
        'data:' + _js(agg_pct) + ','
        'borderColor:"#003262",backgroundColor:"#00326218",'
        'tension:0.3,fill:true,pointRadius:4},'
        '{label:"Target 100%",'
        'data:' + tgt + ','
        'borderColor:"#ccc",borderDash:[6,4],pointRadius:0,fill:false}'
        ']},'
        'options:{responsive:true,'
        'plugins:{legend:{position:"top"}},'
        'scales:{y:{min:0,max:100,ticks:{callback:' + _pct_callback() + '}}}}'
        '});'
        # High-priority bar chart
        'new Chart(document.getElementById("agg-high"),{'
        'type:"bar",'
        'data:{labels:' + _js(agg_dates) + ',datasets:[{'
        'label:"High Priority PDFs",'
        'data:' + _js(agg_high) + ','
        'backgroundColor:"#8b000088",borderColor:"#8b0000",borderWidth:1'
        '}]},'
        'options:{responsive:true,'
        'plugins:{legend:{position:"top"}},'
        'scales:{y:{beginAtZero:true}}}'
        '});'
        '})();</script>'
    )


# =============================================================================
# HTML components  (f-strings used only for HTML structure, not JS)
# =============================================================================

def _domain_card(domain: str, scans: list[dict], idx: int) -> str:
    latest                  = _latest(scans)
    trend_text, trend_cls   = _trend_arrow(scans)
    pct_cls                 = _pct_cls(latest["compliance_pct"])
    bar_color               = _bar_color(latest["compliance_pct"])
    hp                      = latest["high_priority"]
    hp_cls                  = "bad" if hp > 0 else "good"
    pct                     = latest["compliance_pct"]

    mini_chart = ""
    if len(scans) >= 2:
        cid      = f"dc-{idx}"
        dates_js = _js([s["timestamp"].strftime("%Y-%m-%d") for s in scans])
        comp_js  = _js([s["compliance_pct"] for s in scans])
        tgt_js   = _js([100] * len(scans))
        mini_chart = (
            '<div class="dcard-chart">'
            + _mini_chart_js(cid, dates_js, comp_js, tgt_js, bar_color)
            + '</div>'
        )

    return (
        f'<div id="{_anchor(domain)}" class="dcard">'
        f'<div class="dcard-header">'
        f'<span class="dcard-domain">{domain}</span>'
        f'<div class="dcard-badges">'
        f'<span class="badge badge-{pct_cls}">{pct:.1f}% compliant</span>'
        f'<span class="badge badge-{hp_cls}">{hp} high priority</span>'
        f'<span class="badge badge-{trend_cls}">{trend_text}</span>'
        f'</div></div>'
        f'<div class="dcard-metrics">'
        f'<div class="dm"><span class="dmv">{latest["unique_pdfs"]}</span><span class="dml">Unique PDFs</span></div>'
        f'<div class="dm"><span class="dmv {pct_cls}">{pct:.1f}%</span><span class="dml">Compliance</span></div>'
        f'<div class="dm"><span class="dmv {"bad" if hp > 0 else ""}">{hp}</span><span class="dml">High Priority</span></div>'
        f'<div class="dm"><span class="dmv">{latest["violations_total"]}</span><span class="dml">Violations</span></div>'
        f'<div class="dm"><span class="dmv">{latest["errors_per_page_avg"]:.2f}</span><span class="dml">Err / Page</span></div>'
        f'<div class="dm"><span class="dmv">{len(scans)}</span><span class="dml">Scans</span></div>'
        f'</div>'
        + mini_chart +
        f'<a href="#top" class="back-link">↑ Back to top</a>'
        f'</div>'
    )


# =============================================================================
# Full HTML assembly
# =============================================================================

_CSS = """\
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:"Segoe UI",Arial,sans-serif;background:#f5f6f8;color:#1a1a1a;font-size:14px;line-height:1.5}

/* Header */
header{background:#003262;color:#fff;padding:22px 48px;border-bottom:4px solid #C4820E}
header h1{font-size:1.4rem;font-weight:700;letter-spacing:.01em}
header p{font-size:.8rem;color:#90aac8;margin-top:4px}

/* Nav — slim white bar; no domain links cluttering it */
nav{background:#fff;border-bottom:2px solid #e1e5ea;padding:0 48px;display:flex;
    align-items:center;justify-content:space-between;position:sticky;top:0;
    z-index:100;height:46px;box-shadow:0 2px 6px rgba(0,0,0,.07)}
.nav-links{display:flex;gap:2px}
.nav-links a{color:#003262;font-size:.8rem;font-weight:600;text-decoration:none;
             padding:5px 12px;border-radius:4px}
.nav-links a:hover{background:#f0f4f8;color:#C4820E}
.nav-jump{display:flex;align-items:center;gap:8px;font-size:.8rem;color:#555}
.nav-jump select{padding:4px 8px;border:1px solid #d0d7de;border-radius:4px;
                 background:#fff;color:#333;font-size:.78rem;cursor:pointer;max-width:220px}

/* Layout */
.wrap{max-width:1320px;margin:0 auto;padding:26px 48px}

/* KPI pills */
.kpi-row{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:18px}
.kpi{background:#fff;border:1px solid #e1e5ea;border-radius:8px;padding:16px 20px;
     min-width:126px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,.06);
     position:relative;overflow:hidden;flex:1}
.kpi::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:#C4820E}
.kpi.green::before{background:#1a6e3a}
.kpi.red::before{background:#8b0000}
.kpi.navy::before{background:#003262}
.kpi-val{font-size:1.9rem;font-weight:700;color:#111;line-height:1;display:block}
.kpi.green .kpi-val{color:#1a6e3a}
.kpi.red   .kpi-val{color:#8b0000}
.kpi-lbl{font-size:.67rem;color:#667;text-transform:uppercase;letter-spacing:.06em;
         margin-top:5px;display:block}

/* Insight banner */
.insight{background:#fff;border-left:4px solid #C4820E;border-radius:6px;
         padding:11px 18px;margin-bottom:26px;font-size:.875rem;color:#333;
         box-shadow:0 1px 3px rgba(0,0,0,.06)}
.insight.good{border-left-color:#1a6e3a}
.insight.bad{border-left-color:#8b0000}

/* Section labels */
.section-label{font-size:.75rem;font-weight:700;text-transform:uppercase;
               letter-spacing:.1em;color:#003262;border-left:3px solid #C4820E;
               padding-left:9px;margin:28px 0 14px}

/* Chart grids */
.charts-2{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px}
.charts-60-40{display:grid;grid-template-columns:3fr 2fr;gap:14px;margin-bottom:14px}
.chart-card{background:#fff;border:1px solid #e1e5ea;border-radius:8px;
            padding:16px 18px;box-shadow:0 1px 3px rgba(0,0,0,.05)}
.chart-label{font-size:.72rem;font-weight:700;text-transform:uppercase;
             letter-spacing:.07em;color:#003262;margin-bottom:11px}

/* Domain table */
.tbl-wrap{background:#fff;border:1px solid #e1e5ea;border-radius:8px;overflow:auto;
          margin-bottom:26px;box-shadow:0 1px 3px rgba(0,0,0,.06)}
table{width:100%;border-collapse:collapse;font-size:.855rem}
th{background:#003262;color:#fff;padding:10px 16px;text-align:left;
   font-size:.75rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;
   white-space:nowrap}
td{padding:10px 16px;border-bottom:1px solid #f0f2f5;color:#222;vertical-align:middle}
tr:last-child td{border-bottom:none}
tr:hover td{background:#f6f9ff}
.c{text-align:center}
.domain-link{color:#003262;font-weight:600;text-decoration:none}
.domain-link:hover{color:#C4820E;text-decoration:underline}
.trend-good{color:#1a6e3a;font-weight:700}
.trend-bad{color:#8b0000;font-weight:700}
.trend-neu{color:#999}

/* Inline compliance bar */
.comp-bar{display:flex;align-items:center;gap:10px}
.comp-bar-bg{flex:1;height:6px;background:#eee;border-radius:3px;
             overflow:hidden;min-width:60px}
.comp-bar-fill{height:100%;border-radius:3px}
.comp-val{font-weight:700;font-size:.82rem;min-width:42px;text-align:right}
.comp-val.good{color:#1a6e3a}
.comp-val.warn{color:#7a4f00}
.comp-val.bad{color:#8b0000}
.hp-badge{display:inline-block;padding:2px 9px;border-radius:10px;font-size:.75rem;font-weight:700}
.hp-badge.has{background:#fdecea;color:#8b0000}
.hp-badge.none{background:#e6f4eb;color:#1a6e3a}

/* Domain cards grid */
.cards-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));
            gap:14px;margin-bottom:32px}
.dcard{background:#fff;border:1px solid #e1e5ea;border-radius:8px;padding:16px 18px;
       box-shadow:0 1px 3px rgba(0,0,0,.06);display:flex;flex-direction:column;gap:11px}
.dcard-header{padding-bottom:10px;border-bottom:1px solid #f0f2f5}
.dcard-domain{display:block;font-size:.87rem;font-weight:700;color:#003262;
              word-break:break-all;margin-bottom:7px}
.dcard-badges{display:flex;gap:5px;flex-wrap:wrap}
.badge{padding:2px 8px;border-radius:12px;font-size:.7rem;font-weight:700;border:1px solid transparent}
.badge-good{background:#e6f4eb;color:#1a6e3a;border-color:#b2dfcc}
.badge-warn{background:#fff8e8;color:#7a4f00;border-color:#f0d888}
.badge-bad{background:#fdecea;color:#8b0000;border-color:#f5b8b5}
.badge-neu{background:#f0f0f0;color:#555;border-color:#d8d8d8}
.dcard-metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:7px}
.dm{background:#f8f9fa;border-radius:6px;padding:8px 4px;text-align:center}
.dmv{display:block;font-size:1.05rem;font-weight:700;color:#111;line-height:1.2}
.dmv.good{color:#1a6e3a}
.dmv.warn{color:#7a4f00}
.dmv.bad{color:#8b0000}
.dml{display:block;font-size:.6rem;color:#777;text-transform:uppercase;
     letter-spacing:.04em;margin-top:2px}
.dcard-chart canvas{max-height:130px}
.back-link{font-size:.76rem;color:#C4820E;text-decoration:none;font-weight:600}
.back-link:hover{color:#003262}

/* Domain progress table */
.prog-tbl{width:100%;border-collapse:collapse;font-size:.855rem}
.prog-tbl th{background:#003262;color:#fff;padding:9px 14px;font-size:.72rem;font-weight:700;
             text-transform:uppercase;letter-spacing:.06em;white-space:nowrap}
.prog-tbl td{padding:9px 14px;border-bottom:1px solid #f0f2f5;vertical-align:middle}
.prog-tbl tr:last-child td{border-bottom:none}
.prog-tbl tr:hover td{background:#f6f9ff}
.pval{font-weight:700}
.pval.good{color:#1a6e3a}
.pval.warn{color:#7a4f00}
.pval.bad{color:#8b0000}
.prog-up{color:#1a6e3a;font-weight:700}
.prog-dn{color:#8b0000;font-weight:700}
.prog-st{color:#999;font-weight:600}

footer{text-align:center;padding:18px;font-size:.73rem;color:#90aac8;
       border-top:1px solid #1a4a7a;background:#003262}

@media(max-width:900px){
  header,nav{padding-left:18px;padding-right:18px}
  .wrap{padding:16px 18px}
  nav{height:auto;flex-direction:column;align-items:flex-start;padding:10px 18px;gap:8px}
  .charts-2,.charts-60-40{grid-template-columns:1fr}
  .cards-grid{grid-template-columns:1fr}
  .dcard-metrics{grid-template-columns:repeat(3,1fr)}
}"""


def build_html(domain_data: dict[str, list[dict]], generated_at: datetime) -> str:
    stats                        = aggregate_stats(domain_data)
    agg_dates, agg_pct, agg_high = _agg_over_time(domain_data)
    show_history                 = len(agg_dates) >= 2

    gen_str     = generated_at.strftime("%B %d, %Y at %I:%M %p")
    overall_cls = _pct_cls(stats["compliance_pct"])

    # ── Insight banner text ────────────────────────────────────────────────
    parts = []
    if stats["improving"]:
        parts.append(f"<b>{stats['improving']}</b> improving")
    if stats["declining"]:
        parts.append(f"<b>{stats['declining']}</b> declining")
    if stats["stable"]:
        parts.append(f"<b>{stats['stable']}</b> stable")
    if stats["single_scan"]:
        parts.append(f"<b>{stats['single_scan']}</b> with only 1 scan")
    insight_text = " &nbsp;·&nbsp; ".join(parts) if parts else "Not enough scan history to compare trends yet."
    insight_cls  = "good" if not stats["declining"] and stats["compliance_pct"] >= 80 else (
                   "bad"  if stats["declining"] else "")

    # ── Jump-to dropdown ───────────────────────────────────────────────────
    jump_opts = "\n".join(
        f'<option value="{_anchor(d)}">{d}</option>'
        for d in sorted(domain_data)
    )

    # ── KPI pills ──────────────────────────────────────────────────────────
    kpi_color = "green" if overall_cls == "good" else ("red" if overall_cls == "bad" else "")
    kpi_row = (
        f'<div class="kpi-row">'
        f'<div class="kpi navy"><span class="kpi-val">{stats["total_domains"]}</span><span class="kpi-lbl">Domains</span></div>'
        f'<div class="kpi"><span class="kpi-val">{stats["total_pdfs"]}</span><span class="kpi-lbl">Unique PDFs</span></div>'
        f'<div class="kpi {kpi_color}"><span class="kpi-val">{stats["compliance_pct"]:.1f}%</span><span class="kpi-lbl">Overall Compliance</span></div>'
        f'<div class="kpi green"><span class="kpi-val">{stats["total_compliant"]}</span><span class="kpi-lbl">Compliant PDFs</span></div>'
        f'<div class="kpi red"><span class="kpi-val">{stats["total_high"]}</span><span class="kpi-lbl">High Priority</span></div>'
        f'<div class="kpi"><span class="kpi-val">{stats["total_violations"]}</span><span class="kpi-lbl">Total Violations</span></div>'
        f'</div>'
    )

    # ── Domain summary table (sorted worst compliance first) ───────────────
    domain_rows = ""
    for domain in sorted(domain_data, key=lambda d: _latest(domain_data[d])["compliance_pct"]):
        scans            = domain_data[domain]
        latest           = _latest(scans)
        trend_text, tcls = _trend_arrow(scans)
        pct              = latest["compliance_pct"]
        pct_cls          = _pct_cls(pct)
        bc               = _bar_color(pct)
        hp               = latest["high_priority"]
        hp_cls           = "has" if hp > 0 else "none"
        domain_rows += (
            f'<tr>'
            f'<td><a href="#{_anchor(domain)}" class="domain-link">{domain}</a></td>'
            f'<td class="c">{latest["timestamp"].strftime("%Y-%m-%d")}</td>'
            f'<td class="c">{latest["unique_pdfs"]}</td>'
            f'<td>'
            f'<div class="comp-bar">'
            f'<div class="comp-bar-bg"><div class="comp-bar-fill" style="width:{pct:.1f}%;background:{bc}"></div></div>'
            f'<span class="comp-val {pct_cls}">{pct:.1f}%</span>'
            f'</div>'
            f'</td>'
            f'<td class="c"><span class="hp-badge {hp_cls}">{hp}</span></td>'
            f'<td class="c trend-{tcls}">{trend_text}</td>'
            f'</tr>\n'
        )

    # ── Snapshot bar charts ────────────────────────────────────────────────
    # Sort ascending by compliance so the worst domains appear at the top of
    # horizontal bars — easiest to read at a glance.
    sorted_domains = sorted(domain_data.keys(),
                            key=lambda d: _latest(domain_data[d])["compliance_pct"])
    snap_comp  = [_latest(domain_data[d])["compliance_pct"] for d in sorted_domains]
    snap_high  = [_latest(domain_data[d])["high_priority"]  for d in sorted_domains]
    bar_bg     = _js([_bar_color(v) + "99" for v in snap_comp])
    bar_border = _js([_bar_color(v) for v in snap_comp])
    bar_h      = min(max(220, 28 * len(sorted_domains)), 480)

    snapshot_block = (
        f'<div class="charts-2">'
        f'<div class="chart-card">'
        f'<div class="chart-label">Compliance % by Domain — Latest Scan</div>'
        f'<div style="height:{bar_h}px;overflow-y:auto"><canvas id="snap-comp"></canvas></div>'
        f'</div>'
        f'<div class="chart-card">'
        f'<div class="chart-label">High Priority PDFs by Domain — Latest Scan</div>'
        f'<div style="height:{bar_h}px;overflow-y:auto"><canvas id="snap-high"></canvas></div>'
        f'</div>'
        f'</div>'
        + _snapshot_js(sorted_domains, snap_comp, snap_high, bar_bg, bar_border)
    )

    # ── Historical trend charts ────────────────────────────────────────────
    history_block = ""
    if show_history:
        history_block = (
            '<p class="section-label" id="charts-history">Historical Trends</p>'
            '<div class="charts-60-40">'
            '<div class="chart-card">'
            '<div class="chart-label">Overall Compliance % Over Time</div>'
            '<canvas id="agg-comp"></canvas>'
            '</div>'
            '<div class="chart-card">'
            '<div class="chart-label">High Priority PDFs Over Time</div>'
            '<canvas id="agg-high"></canvas>'
            '</div>'
            '</div>'
            '<div class="chart-card" style="margin-bottom:16px">'
            '<div class="chart-label">Domain Progress — Baseline to Latest Scan</div>'
            '<p style="font-size:.75rem;color:#888;margin-bottom:10px">Sorted by biggest change. '
            'Each domain card below has its own trend chart.</p>'
            + _domain_progress_table(domain_data) +
            '</div>'
            + _history_js(agg_dates, agg_pct, agg_high)
        )

    # ── Per-domain cards ───────────────────────────────────────────────────
    cards_html = "\n".join(
        _domain_card(domain, domain_data[domain], idx)
        for idx, domain in enumerate(sorted(domain_data))
    )

    # ── Full page ──────────────────────────────────────────────────────────
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CSULA PDF Accessibility — Master Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>{_CSS}</style>
</head>
<body id="top">

<header>
  <h1>CSULA PDF Accessibility — Master Dashboard</h1>
  <p>Generated {gen_str} &nbsp;·&nbsp; {stats['total_domains']} domains &nbsp;·&nbsp; {stats['total_pdfs']} unique PDFs</p>
</header>

<nav>
  <div class="nav-links">
    <a href="#summary">Overview</a>
    <a href="#snapshot">Snapshot</a>
    <a href="#domain-table">Domains</a>
    <a href="#domain-details">Details</a>
  </div>
  <div class="nav-jump">
    <label for="jump-sel">Jump to:</label>
    <select id="jump-sel" onchange="var v=this.value;if(v){{var el=document.getElementById(v);if(el)el.scrollIntoView({{behavior:'smooth'}});this.value=''}}">
      <option value="">— select domain —</option>
      {jump_opts}
    </select>
  </div>
</nav>

<div class="wrap">

  <p class="section-label" id="summary">Overview</p>
  {kpi_row}
  <div class="insight {insight_cls}">
    <strong>Trend:</strong> &nbsp; {insight_text}
  </div>

  <p class="section-label" id="snapshot">Latest Snapshot</p>
  {snapshot_block}

  {history_block}

  <p class="section-label" id="domain-table">Domain Summary</p>
  <div class="tbl-wrap">
    <table>
      <thead><tr>
        <th>Domain</th>
        <th class="c">Latest Scan</th>
        <th class="c">Unique PDFs</th>
        <th>Compliance %</th>
        <th class="c">High Priority</th>
        <th class="c">Trend</th>
      </tr></thead>
      <tbody>{domain_rows}</tbody>
    </table>
  </div>

  <p class="section-label" id="domain-details">Domain Details</p>
  <div class="cards-grid">
    {cards_html}
  </div>

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
    parser.add_argument("--source", choices=["onedrive", "local"], default="onedrive",
                        help="'onedrive' uses TEAMS_ONEDRIVE_PATH from config; 'local' requires --local-path")
    parser.add_argument("--local-path", metavar="PATH",
                        help="Root folder containing domain subfolders (--source=local only)")
    parser.add_argument("--domains", nargs="+", metavar="DOMAIN",
                        help="Limit to specific domain(s); default is all subfolders")
    parser.add_argument("--output", metavar="PATH",
                        help="Output HTML path (default: <source-folder>/Master/master_report.html)")
    args = parser.parse_args()

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
    domain_data = collect_from_local(source_path, args.domains or None)

    if not domain_data:
        print(
            "\nNo scan data found. Make sure the folder contains domain subfolders "
            "with timestamped .xlsx files: {domain}-YYYY-MM-DD_HH-MM-SS.xlsx"
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
          f"{stats['compliance_pct']:.1f}% compliance  |  "
          f"{stats['total_high']} high priority")
    if args.source == "onedrive":
        print("       OneDrive will sync it to Teams in the background.")


if __name__ == "__main__":
    main()
