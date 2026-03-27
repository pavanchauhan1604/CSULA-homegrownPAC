# Upgrade Planning — CSULA PDF Accessibility Checker

## Current State of the Software (March 2026)

### What it does end-to-end
Scrapy spiders crawl 182 CSULA website sections → collect PDF URLs → `conformance_checker.py` downloads each PDF, runs VeraPDF (PDF/UA-1) and pikepdf analysis → stores results in SQLite (`drupal_pdfs.db`) → `data_export.py` generates per-domain Excel reports → `sharepoint_sync.py` syncs to OneDrive/Teams + generates per-employee HTML email drafts → `send_emails.py` sends via Outlook COM (Windows only) → `generate_master_report.py` + `generate_master_report_html.py` produce cross-domain summary reports.

### What the scanner currently measures per PDF

| Check | Tool | What it actually detects |
|---|---|---|
| `tagged` | pikepdf | `/StructTreeRoot` key exists in PDF root — existence only |
| `pdf_text_type` | pdfminer | Raw content stream has text glyphs — bypasses tag tree entirely |
| `violations` | VeraPDF (PDF/UA-1) | Structural rule violations (tag types, alt attribute presence, lang, etc.) |
| `failed_checks` | VeraPDF | Individual failed rule checks (granular count) |
| `has_form` | pikepdf | Any annotation with `/FT` key — existence only |
| `approved_pdf_exporter` | pikepdf metadata | Producer field matches approved tool list (currently: Equidox 7) |
| `page_count` | pikepdf | Number of pages |
| `title_set` | pikepdf metadata | `dc:title` present in XMP metadata |
| `language_set` | pikepdf | `/Lang` key present — stored but NOT used in priority filter |
| `file_hash` | SHA-256 | Dedup fingerprint |

### Current high-priority logic (`src/core/filters.py` → `is_high_priority()`)

Returns `True` (high priority = needs remediation) if ANY of:
- `tagged == 0` — untagged, screen reader cannot navigate
- `pdf_text_type == "Image Only"` — no text layer, screen reader reads nothing
- `errors/page > 9` — systematic widespread violations
- `has_form == 1 AND errors/page > 3` — form inaccessible to screen reader

Auto-pass: `approved_pdf_exporter == True` → always low priority regardless.

`language_set` is stored in the DB but is NOT currently factored into `is_high_priority()`.

---

## The Critical Gap Discovered — March 2026

### What happened
64 high-priority UAS domain PDFs were sent to Connectivo DocuRem for remediation. Returned files scanned as 94% improved — violations dropped, `tagged = True`, VeraPDF rules passed. Manual review in Adobe Acrobat revealed four distinct failure modes, none of which our software detected.

### Finding 1 — Partial MCID linkage (not all-or-nothing)
Tags were not uniformly empty — some tag elements on some pages had correct MCID references and real content linked. Others on the same document had zero MCIDs. This means `mcid_count > 0` is not sufficient; we need `mcid_count` as a ratio relative to the number of pages or the number of text elements in the content stream. A document with 200 pages and 12 MCIDs is functionally broken even though `mcid_count != 0`. The check needs to be: **mcid_count relative to document complexity**, not just existence.

Implication for implementation: store `tag_content_refs` as a raw integer AND compute `tag_refs_per_page = tag_content_refs / page_count`. Flag high priority if `tagged AND tag_refs_per_page < threshold` (threshold TBD from calibration, suggest starting at 1.0 — fewer than one content reference per page is a strong signal of incomplete tagging).

### Finding 2 — Inconsistent reading order across pages
Reading order was correct on some pages within a document and random on others. This is harder to detect than complete disorder — a document where every page is wrong would still score the same as one where half the pages are right. The inconsistency itself is the problem because users cannot predict which pages will work.

Implication: reading order scoring needs to be per-page, not per-document. An aggregate score hides page-level failures. This makes reading order detection more expensive (per-page bounding box comparison vs. MCID sequence) but more meaningful. Still high false-positive risk on complex legitimate layouts — treat as advisory/medium signal, not high-priority trigger.

### Finding 3 — Form field tooltips present but contextually useless
`/TU` (tooltip = accessible name) was set on form fields, but the value was just the adjacent text on the page — the word or phrase immediately before or after the blank. Examples: "below", "the following", "date" used as the label for fields requiring full context. This passes our planned form field label check (which only verifies `/TU` exists) but delivers nothing useful to a screen reader user.

Implication: checking `/TU` existence is necessary but not sufficient. Need to also check `/TU` value length and quality — very short values (< 3 words) or values matching a list of known junk patterns ("below", "above", "following", "see", "the") should be flagged. Consider minimum meaningful label length of ~10 characters.

### Finding 4 — Interactive form fields removed, replaced with static text
The original documents had fillable form fields (PDF annotations with `/FT`). In the remediated versions those annotations were removed and only surrounding static text remained. The documents show no `has_form` in our system — technically correct since no `/FT` annotations exist. But the original intent was a form and the user cannot complete it.

Implication: this is largely undetectable from the PDF structure alone without knowing the original. However, documents that look structurally like forms (repeated short text blocks followed by whitespace, table structures with blank cells, underline patterns) but have no form fields may warrant a heuristic "possible de-formed document" flag. This is research-level work, not near-term. Short term: include original `has_form` value in remediation comparison reports so reviewers can spot this manually.

### Why our stack missed all four
- pikepdf checks `/StructTreeRoot` existence ✓ — does not check MCID count or per-page coverage
- pdfminer reads raw content stream directly, bypassing the tag tree entirely ✓
- VeraPDF validates tag type validity and attribute presence, not content linkage or reading order ✓
- Our form field check (`has_form`) looks for `/FT` existence — passes Finding 3 (labels present but bad), misses Finding 4 (fields removed)

---

## Planned Improvements — Prioritised

### Priority 1 — MCID / Empty Tag Detection
**What:** Walk the StructTreeRoot recursively and count leaf nodes containing `/MCID` integers or `/Obj` content references. If `tagged == True AND mcid_count == 0` → treat as equivalent to untagged.

**Where:** `pdf_check()` in `src/core/pdf_priority.py` — add `tag_content_refs: int` to return dict. New column `tag_content_refs` in `pdf_report` DB table and Excel output. New condition in `is_high_priority()` in `src/core/filters.py`.

**Tool:** pikepdf — no new dependency.

**Confidence:** Near 100% for zero-MCID case. For partial linkage, confidence depends on threshold calibration — `tag_refs_per_page < 1.0` is a strong signal but needs validation against real documents. Start conservative (flag only if < 0.5 per page) and lower the threshold after reviewing results.

```python
def count_tag_mcids(document) -> int:
    root = document.Root.get("/StructTreeRoot")
    if root is None:
        return 0
    count = 0
    def walk(node):
        nonlocal count
        if isinstance(node, pikepdf.Dictionary):
            if "/MCID" in node:
                count += 1
            elif "/K" in node:
                walk(node["/K"])
        elif isinstance(node, pikepdf.Array):
            for item in node:
                walk(item)
        elif isinstance(node, int):
            count += 1
    k = root.get("/K")
    if k:
        walk(k)
    return count
```

---

### Priority 2 — Alt Text Coverage Ratio
**What:** We already walk the tag tree for alt text via `check_for_alt_tags()`. Problem: we don't weight by document image density. A 20-page form missing alt on one decorative logo is low risk. A 15-page research paper where every figure is a chart with no alt text means all data is inaccessible.

**Improvement:** Compute `images_without_alt / total_pages`. Add `alt_coverage_ratio` to DB. Add to `is_high_priority()` threshold: if ratio > 0.5 (more than one missing alt text per 2 pages on average) → high priority.

Also add heuristic junk detection: alt text that is `""`, `" "`, `"image"`, `"figure"`, matches the filename, or is a single character → treat as missing.

**Tool:** pikepdf — no new dependency.

**Confidence:** High for the junk patterns. The ratio threshold will need calibration against real data.

---

### Priority 3 — Form Field Label Check
**What:** `has_form = 1` currently means "at least one `/FT` annotation exists." It does not mean any field is labelled. A form where every field says "edit, blank" is operationally useless.

**Improvement:** For each form field annotation, check for `/TU` (tooltip — used as accessible name by most screen readers), or a linked structure tree element with text content. Count labelled vs total fields. Add `form_fields_total` and `form_fields_labelled` to DB. Flag high priority if `has_form AND form_fields_labelled == 0`.

**Tool:** pikepdf — no new dependency.

**Confidence:** High for missing `/TU`. Medium for quality check — the junk pattern list needs tuning. Start with: flag if `/TU` is missing OR `/TU` value length < 10 characters OR value matches a known-bad list (`["below", "above", "following", "the", "see", "date", "name", "here"]`).

---

### Priority 4 — Language in Priority Filter
**What:** `language_set` is already stored in `pdf_report` and available in Excel. It is not currently used in `is_high_priority()`.

**Improvement:** Add `language_set == 0` as a contributing factor — not standalone high priority, but combined with other issues. Or add a separate "Medium Priority" output column indicating language is missing.

**Why it matters:** Screen readers select TTS voice and phoneme rules from `/Lang`. Wrong or missing language → wrong pronunciation engine → garbled audio output, especially for proper nouns, abbreviations, and non-English content.

**Tool:** No change — data already in DB. Just update `filters.py`.

**Confidence:** High for detection. Impact varies by document type.

---

### Priority 5 — OCR Garbage Detection
**What:** `pdf_text_type == "Image Over Text"` means OCR was run. We do not check if the OCR output is coherent. Garbled OCR text (`"Tl1e qu1ck br0wn f0x"`) is functionally equivalent to no text.

**Improvement:** For Image Over Text documents, extract text with pdfminer, tokenise, and compute the ratio of tokens that appear in an English word list. Below ~40% real-word ratio → flag as `ocr_quality = "Poor"` → include in high priority logic.

**Tool:** `pyspellchecker` (pip install pyspellchecker) — small, offline, no API calls.

**Confidence:** ~70-75%. Will false-positive on heavily technical documents (code, formulas, abbreviations). Calibrate threshold carefully. Consider limiting to documents where the OCR word ratio is below a stricter threshold (e.g., 25%) for high-priority flagging.

---

### Priority 6 — PDF/UA-2 Dual Check
**What:** VeraPDF already supports `-f ua2` profile. No new software needed.

**Improvement:** Run both `-f ua1` and `-f ua2` checks per PDF. Store both violation counts. Surface UA-2 violations in Excel as an additional column. Does not change current high-priority thresholds — additive information only.

**Why:** PDF/UA-2 has stricter requirements around artifact marking, namespace declarations, and MathML. As the standard evolves and DOJ guidance tightens, having this data already collected will be valuable.

**Tool:** VeraPDF — already installed. Config change + additional DB column only.

---

### Future / Higher Effort (not in immediate roadmap)

**Table header structure detection**
Use `pdfplumber` to detect table regions visually, cross-reference with structure tree to check `TH` header elements and `/Scope` attributes. High real-world impact but moderate false-positive risk on layout tables vs data tables.

**Reading order scoring**
Extract text block bounding boxes with `pdfplumber`, compare spatial order against MCID sequence in structure tree. Useful signal but high false-positive rate on complex legitimate layouts. Consider as an advisory flag only, not a high-priority trigger.

**Color contrast**
Render pages with `pdf2image` (requires poppler), sample foreground/background near text regions, calculate WCAG contrast ratio. Relevant for low-vision users (not screen reader users). High implementation complexity. Out of scope until Tier 1-2 items above are complete.

**Semantic alt text quality via Claude API**
Send image alt text to Claude API with a simple prompt. Would catch `"a bar chart"` vs a descriptive summary. Cost fractions of a cent per PDF. Dependency on external API + latency. Consider for batch post-processing after remediation, not during initial scan.

---

## Limitations That Cannot Be Automated

These are architecturally out of scope — not because of implementation complexity but because they require human judgment and understanding of document meaning:

| Issue | Why automation fails |
|---|---|
| Reading order in multi-column/complex layouts | Correct order depends on document intent, not detectable from structure alone |
| Semantic tag type correctness (wrong heading levels, mis-tagged elements) | Requires understanding document meaning |
| Alt text quality beyond heuristics | Requires seeing the image and judging description sufficiency |
| Complex table header relationships (merged cells, nested tables) | Layout-table vs data-table distinction requires human judgment |
| Vendor compliance — passing checks ≠ accessible | Automated tools check rules, not outcomes. Human spot-check of remediated batches is mandatory |
| Mathematical/formula accessibility | No automated standard; requires specialised tagging (MathML) and human review |
| OCR accuracy for non-English or highly technical content | Word-ratio heuristic breaks down on domain-specific vocabulary |

**Key operational recommendation:** Any batch of files returned by a third-party remediator should have 5-10 files opened in an actual screen reader (NVDA, JAWS, or VoiceOver) and listened to before the batch is accepted. Automated checks are a necessary but not sufficient quality gate.

---

## DB Schema Changes Required for Planned Improvements

```sql
ALTER TABLE pdf_report ADD COLUMN tag_content_refs    INTEGER DEFAULT NULL;
ALTER TABLE pdf_report ADD COLUMN images_without_alt  INTEGER DEFAULT NULL;
ALTER TABLE pdf_report ADD COLUMN form_fields_total   INTEGER DEFAULT NULL;
ALTER TABLE pdf_report ADD COLUMN form_fields_labelled INTEGER DEFAULT NULL;
ALTER TABLE pdf_report ADD COLUMN ocr_quality         TEXT    DEFAULT NULL;
ALTER TABLE pdf_report ADD COLUMN ua2_violations      INTEGER DEFAULT NULL;
ALTER TABLE pdf_report ADD COLUMN ua2_failed_checks   INTEGER DEFAULT NULL;
```

New Excel columns to add in `data_export.py`:
- `Tag Content Refs` — integer, 0 = empty tag structure
- `Images Without Alt` — integer count
- `Form Fields Labelled` — ratio display (e.g. "3/7")
- `OCR Quality` — "Good" / "Poor" / "N/A"
- `PDF/UA-2 Violations` — integer

Updated `is_high_priority()` conditions to add:
```python
# Empty tag structure — tags exist but no content linked
if tagged and tag_content_refs == 0:
    return True
# Form fields all unlabelled
if has_form and form_fields_total > 0 and form_fields_labelled == 0:
    return True
# Poor OCR on image-over-text document
if pdf_text_type == "Image Over Text" and ocr_quality == "Poor":
    return True
```

---

## Files to Modify for Each Improvement

| Improvement | Files |
|---|---|
| MCID check | `src/core/pdf_priority.py`, `src/core/database.py`, `src/data_management/data_export.py`, `src/core/filters.py` |
| Alt text coverage | `src/core/pdf_priority.py`, `src/data_management/data_export.py`, `src/core/filters.py` |
| Form field labels | `src/core/pdf_priority.py`, `src/data_management/data_export.py`, `src/core/filters.py` |
| Language in filter | `src/core/filters.py` only |
| OCR garbage detection | `src/core/pdf_priority.py`, `src/data_management/data_export.py`, `src/core/filters.py` |
| PDF/UA-2 dual check | `src/core/conformance_checker.py`, `src/core/database.py`, `src/data_management/data_export.py` |

All changes must follow the architecture rules in CLAUDE.md:
- Shared logic lives in `report_reader.py`, `filters.py`, or `config.py` — never duplicated
- Priority stamped at export time in `data_export.py`, never re-evaluated downstream
- All new DB columns added via schema migration in `database.py`
- No hardcoded paths — all paths via `config.py`
