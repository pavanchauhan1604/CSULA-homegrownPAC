# Future Upgrade Planning — PDF Auto-Remediation Pipeline
## Phase 2: After PDF Checker Improvements Are Complete

**Context:** This document is a memory file for future Claude sessions. It captures a
planning conversation held in March 2026 about building an automated PDF remediation
pipeline as the next major phase of the CSULA HomegrownPAC project. Do not implement
anything here until the improvements in `upgradeplanning.md` are complete and validated.

---

## Where We Are When This Becomes Relevant

By the time this phase starts, the PDF checker (`conformance_checker.py`) will have been
upgraded with the following (see `upgradeplanning.md` for full detail):
- MCID / empty tag detection (tag_content_refs column)
- Alt text coverage ratio
- Form field label quality check
- Language in priority filter
- OCR garbage detection
- PDF/UA-2 dual check

The checker will then reliably identify documents that are **genuinely inaccessible** —
not just structurally non-compliant on paper. The output is a prioritised list of PDFs
that need remediation. The next problem is volume: there are thousands of them and
manual remediation through Acrobat or Equidox does not scale to the April 2026 deadline.

---

## The Goal of This Phase

Build a local automated remediation pipeline:

```
Input: inaccessible PDF
Output: remediated PDF that passes VeraPDF + has real content in tags
```

The pipeline runs entirely locally on the M1 Ultra Mac Studio (64GB unified memory).
No external API calls, no per-document cost, no data leaving the machine.

Human review is still required for complex cases (reading order in multi-column
layouts, complex tables, form labels). The automation target is:
**get 60-70% of documents to a good baseline state so human review time is minimised.**

---

## Hardware Context

**Machine:** M1 Ultra Mac Studio, 64GB unified memory
**Implication:** Can run models that require 40GB+ VRAM that most machines cannot.
Specifically, Qwen2-VL 72B at 4-bit quantization (~38GB) fits comfortably alongside
other processes. Apple Silicon MPS acceleration makes surya/marker fast.

---

## Proposed Pipeline Architecture

```
PDF Input
  │
  ├─[if scanned / Image Only]──────────────────────────────────────────────────┐
  │   OCRmyPDF (wraps Tesseract)                                                │
  │   → adds clean searchable text layer                                        │
  │   → output: PDF with text layer                                             │
  └─────────────────────────────────────────────────────────────────────────────┘
  │
  ├── pdf2image (wraps poppler) ──────────────────────────────────────────────────
  │   → render each page as a high-res image (300 DPI)
  │   → needed for both layout analysis and vision LLM
  │
  ├── surya ──────────────────────────────────────────────────────────────────────
  │   → layout analysis on page images (runs on Apple Silicon MPS)
  │   → outputs per-page bounding boxes with element type:
  │       Heading1/2/3, Paragraph, Figure, Table, List, ListItem, Caption,
  │       Header, Footer, PageNumber
  │   → outputs detected reading order per page
  │   → outputs table structure (rows, columns, header cells)
  │
  ├── for each detected Figure bounding box:
  │   └── crop image region → local vision LLM → alt text string
  │       Model options (in order of preference for quality vs speed):
  │       - Qwen2-VL 72B (4-bit, ~38GB) — best quality, ~8-12s per image
  │       - Qwen2-VL 7B (~5GB) — good quality, ~2-3s per image
  │       - MiniCPM-V 2.6 (~8GB) — fast, good at document figures
  │       All served via Ollama (already installable on Mac)
  │
  ├── pikepdf ── tag injection ─────────────────────────────────────────────────
  │   (see "The Hard Part" section below)
  │
  └── VeraPDF ── validation ────────────────────────────────────────────────────
      → run PDF/UA-1 check on output
      → generate diff report: issues before vs issues after
      → flag anything that still needs human review
```

---

## Two Implementation Approaches — Decision Needed

### Approach A: Reconstruct (Recommended Starting Point)

**How it works:**
1. surya/marker converts PDF → structured JSON/Markdown (headings, paragraphs, tables, figures with positions)
2. Alt text is generated for figures
3. A new PDF is built from scratch using `fpdf2` or `reportlab` with tagged PDF support
4. The new PDF has correct tag structure, MCIDs, reading order, alt text, language, title

**Pros:**
- Tag injection is clean — building from scratch is much easier than modifying existing
- Reading order is guaranteed correct (from surya's detected order)
- Output reliably passes VeraPDF

**Cons:**
- Output looks different from original — fonts, layout, exact positioning will shift
- Images are extracted and re-embedded (quality preserved but layout may shift slightly)
- Tables may reflow

**When acceptable:** For most university PDFs (forms, policy documents, reports) where
the content matters more than pixel-perfect appearance. Not acceptable for branded
publications, PDFs with complex visual design, or documents where layout is informational.

---

### Approach B: In-Place Tagging (Higher Fidelity, More Complex)

**How it works:**
1. surya detects element bounding boxes on rendered page images
2. Use pikepdf to read existing content streams (decompressed)
3. Map surya's bounding boxes to text-drawing operators in content streams
4   Insert `BDC` / `EMC` (Begin/End Marked Content) operators wrapping matched operators
5. Build StructTreeRoot tree from detected hierarchy
6. Wire MCIDs between structure tree and content stream markers
7. Inject alt text on Figure elements

**Pros:**
- Output is visually identical to original — fonts, layout, positioning preserved
- Keeps original PDF metadata, links, annotations
- The "right" solution for high-fidelity remediation

**Cons:**
- Content streams are complex: compressed, use various operators, may be split across
  multiple streams per page. Mapping bounding boxes to operators is non-trivial.
- Getting BDC/EMC placement wrong produces worse output than the original
- Significant custom engineering — this is what Acrobat does internally and it took
  Adobe years to build

**Recommended:** Start with Approach A. Validate quality. If output fidelity is
insufficient for a significant portion of documents, revisit Approach B for those cases.

---

## The Hard Part — Tag Injection Detail

This section is for whoever implements the pikepdf injection step.

A valid tagged PDF requires:

**In the page content stream:**
```
/artifact_or_tag_name <</MCID integer>> BDC
  ... text drawing operators (BT, Tf, Td, Tj, ET, etc.) ...
EMC
```

Each `BDC` references an MCID integer. That integer must match a leaf node in the
StructTreeRoot tree that has `/MCID integer` and `/Pg` pointing to the correct page.

**In the StructTreeRoot:**
```
/StructTreeRoot <<
  /Type /StructTreeRoot
  /K [array of top-level structure elements]
  /ParentTree [number tree mapping MCIDs back to structure elements]
>>
```

Each structure element:
```
<<
  /Type /StructElem
  /S /P          (or /H1, /H2, /Figure, /Table, /L, /LI, etc.)
  /P [reference to parent element]
  /K [array of children or MCID integer for leaf nodes]
  /Pg [reference to page object]
>>
```

The `/ParentTree` is a number tree that must map every MCID back to its parent
structure element. VeraPDF validates this rigorously.

pikepdf gives full access to all of this. The implementation complexity is in:
1. Correctly decompressing and parsing content streams to find text operator positions
2. Mapping surya's pixel-space bounding boxes to content stream operator coordinates
3. Maintaining correct MCID integer uniqueness across all pages
4. Building a valid `/ParentTree` number tree

---

## Python Stack to Install

```zsh
# Core pipeline
pip install surya-ocr        # layout analysis + reading order (Apple Silicon MPS)
pip install marker-pdf        # PDF → structured output built on surya
pip install pdf2image         # page rendering (requires poppler)
pip install ocrmypdf          # OCR for scanned documents (requires Tesseract)
pip install pikepdf           # PDF manipulation (already installed)
pip install fpdf2             # tagged PDF generation from scratch (Approach A)

# Validation (already installed)
# VeraPDF at ~/veraPDF/verapdf

# Homebrew dependencies
brew install poppler          # for pdf2image
brew install tesseract        # for ocrmypdf

# Vision LLM (local, via Ollama — already installed if setup_mac.sh was run)
ollama pull qwen2-vl          # 7B default, or qwen2-vl:72b for best quality
# Alternative:
ollama pull minicpm-v         # faster, smaller, good at document images
```

---

## Expected Performance on M1 Ultra

| Step | Time per page | Notes |
|---|---|---|
| OCRmyPDF | ~2-3s | Only for scanned docs |
| pdf2image render | ~0.5s | 300 DPI |
| surya layout | ~1-2s | MPS accelerated |
| Alt text (Qwen2-VL 7B) | ~2-3s per figure | Only pages with images |
| Alt text (Qwen2-VL 72B 4-bit) | ~8-12s per figure | Higher quality |
| pikepdf tag injection | ~0.5s | |
| VeraPDF validation | ~3-5s | |
| **Total (10-page doc, 3 figures)** | **~30-60s** | End to end |

Batch processing 500 documents: ~4-8 hours unattended overnight.

---

## What the Tool Would Fix Automatically

| Issue | Auto-fixable | Confidence |
|---|---|---|
| Untagged document | Yes — full tag structure generated from surya | High |
| Image Only / no text layer | Yes — OCRmyPDF adds text layer first | High |
| Tagged but empty (MCID = 0) | Yes — tags rebuilt with content | High |
| Missing alt text on figures | Yes — vision LLM generates it | Medium-High |
| Missing language (/Lang) | Yes — detect from text + set | High |
| Missing title metadata | Yes — extract from first H1 or filename | Medium |
| Basic reading order | Yes — from surya's detected order | Medium |
| List structure | Yes — surya detects lists | Medium |

## What Still Needs Human Review After Auto-Remediation

| Issue | Why human needed |
|---|---|
| Multi-column reading order | surya gets it mostly right but complex layouts need verification |
| Complex table headers | Table Transformer helps but merged cells/nested tables need review |
| Alt text accuracy on charts/graphs | LLM describes what it sees, human confirms data accuracy |
| Form field semantic labels | Requires understanding form intent |
| Decorative element artifact marking | Requires visual judgment |
| Documents where layout IS the information | E.g. org charts, infographics |

---

## Suggested CLI Interface

```
python scripts/remediate_pdf.py --input path/to/file.pdf --output path/to/fixed.pdf
python scripts/remediate_pdf.py --folder path/to/high_priority_pdfs/ --output-dir path/to/output/
python scripts/remediate_pdf.py --folder ... --model qwen2-vl:72b   # use larger model
python scripts/remediate_pdf.py --folder ... --skip-alt-text        # faster, no vision LLM
python scripts/remediate_pdf.py --validate-only path/to/output/     # just run VeraPDF on outputs
```

Output per document:
- `{filename}_remediated.pdf` — the fixed PDF
- `{filename}_remediation_report.txt` — what was changed, what VeraPDF still flags

---

## Integration With Existing Pipeline

This remediation tool is intentionally standalone — not integrated into the main
scan/report pipeline. The workflow would be:

1. Run existing scan pipeline → get Excel reports with high-priority PDFs
2. Download high-priority PDFs from their URLs (or use the already-downloaded temp copies)
3. Run `remediate_pdf.py` on them in batch
4. Human review the output for complex cases
5. Upload remediated PDFs to replace originals on the university website
6. Re-run the scan pipeline to confirm the originals are now compliant

The remediation tool does NOT write back to the database or generate Excel reports.
It is a file-in / file-out tool. The existing pipeline handles tracking and reporting.

---

## Open Questions to Resolve Before Starting

1. **Approach A vs B decision** — test Approach A on 10-20 real CSULA PDFs first. If
   the visual quality is acceptable to content managers, proceed with A. If not, scope
   Approach B for the specific document types where fidelity matters.

2. **Alt text model selection** — benchmark Qwen2-VL 7B vs 72B on a sample of CSULA
   figures (charts, logos, photos, scanned forms). The quality difference may not
   justify the 4x speed difference for most document types.

3. **surya accuracy on CSULA documents** — run surya on 20 representative CSULA PDFs
   and manually check whether the detected element types and reading order match the
   visual layout. This determines whether the foundation is solid before building on it.

4. **Legal/policy question** — confirm with the accessibility office whether a
   machine-generated remediated PDF satisfies the DOJ requirement, or whether a
   human-reviewed PDF is required. The answer affects how much automation is acceptable
   vs how much human sign-off is needed per document.

---

## Key Dependencies to Be Aware Of

- `surya` and `marker` are maintained by one person (Vik Paruchuri / Datalab). Actively
  maintained as of March 2026 but dependency risk is higher than Apache/IBM projects.
- `fpdf2` tagged PDF support is relatively new — test VeraPDF compliance of its output
  before committing to it as the generation backend.
- Ollama on Apple Silicon is stable and actively developed. Qwen2-VL models are
  available and well-tested on Apple Silicon as of March 2026.
- `OCRmyPDF` is mature, well-maintained, production-grade. Low risk.

---

## Files That Will Be Created in This Phase

```
scripts/remediate_pdf.py          — main CLI entry point
src/remediation/
  ├── __init__.py
  ├── ocr_layer.py                 — OCRmyPDF wrapper for scanned docs
  ├── layout_analyzer.py           — surya wrapper, returns structured page data
  ├── alt_text_generator.py        — Ollama/vision LLM wrapper
  ├── tag_injector.py              — pikepdf tag writing (Approach B) or
  ├── pdf_reconstructor.py         — fpdf2 PDF rebuilding (Approach A)
  └── remediation_validator.py     — VeraPDF wrapper + before/after diff
```

None of these files exist yet. Do not create them until upgradeplanning.md items
are fully implemented and validated.
