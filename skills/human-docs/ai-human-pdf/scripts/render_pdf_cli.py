#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14,<3.15"
# dependencies = ["reportlab>=4.0", "mistune>=3.0", "pyyaml>=6.0"]
# ///
"""Standalone PDF renderer for the ai-human-pdf skill.

Converts markdown with YAML frontmatter to a styled PDF with a cover page,
running headers and footers, a TOC, tables, code blocks, and admonitions.

Run it as `uv run --locked --script render_pdf_cli.py`. The `.lock` beside this
file fixes the dependencies' versions and hashes, and `--locked` refuses a lock
that no longer matches the block above instead of rewriting it. After editing
that block, regenerate the lock with `uv lock --script render_pdf_cli.py`.
"""

import argparse
import re
import shutil
import subprocess  # nosec B404 # runs npx for Mermaid only, never a shell
import sys
import tempfile
from datetime import date
from pathlib import Path

import mistune
import yaml
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    Image as RLImage,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

# ═══════════════════════════════════════════════════════════════════════════════
# TOKENS
# ═══════════════════════════════════════════════════════════════════════════════

#: The accent when neither `--accent` nor frontmatter `accent:` sets one.
DEFAULT_ACCENT = '#2F5D8A'

_HEX_COLOR_RE = re.compile(r'#[0-9A-Fa-f]{6}')

COLORS = {
    'ink_900':       HexColor('#1F2328'),
    'ink_700':       HexColor('#24292F'),
    'accent':        HexColor(DEFAULT_ACCENT),
    'red_600':       HexColor('#C0392B'),
    'gray_900':      HexColor('#333333'),
    'gray_500':      HexColor('#666666'),
    'gray_200':      HexColor('#D4DBDB'),
    'white':         HexColor('#FFFFFF'),
    'warning_fill':  HexColor('#FFF6E5'),
    'critical_fill': HexColor('#FBEAE7'),
}

FONTS = {
    'regular': 'Helvetica',
    'bold':    'Helvetica-Bold',
    'oblique': 'Helvetica-Oblique',
    'mono':    'Courier',
}

SIZES = {
    'display':      30,
    'h1':           18,
    'subtitle':     16,
    'h2':           14,
    'h3':           11,
    'eyebrow':      11,
    'cover_stat':   10,
    'body':          9,
    'header_wm':     9,
    'table':         8,
    'cover_footer':  8,
    'footer':        7,
    'code':          9,
    'toc_h1':       11,
    'toc_h2':       10,
    'toc_h3':        9,
    'mermaid_width': 180,
}

LEADING = {
    'display':      36,
    'h1':           22,
    'subtitle':     20,
    'h2':           18,
    'h3':           14,
    'eyebrow':      14,
    'cover_stat':   14,
    'body':         12,
    'header_wm':    12,
    'table':        11,
    'cover_footer': 11,
    'footer':       10,
    'code':         12,
    'toc_h1':       14,
    'toc_h2':       13,
    'toc_h3':       12,
}

SPACING = {
    's1':  4,
    's2':  6,
    's3':  8,
    's4': 12,
    's5': 16,
    's6': 24,
    's8': 36,
    'toc_indent': 18,
}

PAGE_CHROME = {
    'margin':           42,
    'cover_margin':     54,
    'edge_margin':      36,
    'header_band':      40,
    'header_rule':       2,
    'cover_top_bar':     8,
    'footer_band':      28,
    'footer_rule':       1,
    'cover_bottom_bar':  4,
}

RULES = {
    'h1':       {'thickness': 1.5, 'color': COLORS['accent']},
    'hairline': {'thickness': 0.5, 'color': COLORS['gray_200']},
    'topbar':   {'thickness': PAGE_CHROME['header_rule'],
                 'color': COLORS['accent']},
    'footer_rule': {'thickness': PAGE_CHROME['footer_rule'],
                    'color': COLORS['accent']},
    'cover_topbar':    {'thickness': PAGE_CHROME['cover_top_bar'],
                        'color': COLORS['accent']},
    'cover_bottombar': {'thickness': PAGE_CHROME['cover_bottom_bar'],
                        'color': COLORS['accent']},
    'eyebrow': {'thickness': 1.5, 'color': COLORS['accent'], 'width': '100%'},
}

RADII = {'card': 12}

PAGE_W, PAGE_H = LETTER
content_width = PAGE_W - 2 * PAGE_CHROME['margin']

# ═══════════════════════════════════════════════════════════════════════════════
# STYLES
# ═══════════════════════════════════════════════════════════════════════════════

TOC_TITLE_TEXT = 'Table of Contents'

STYLES = {
    'H1': ParagraphStyle(
        'H1',
        fontName=FONTS['bold'], fontSize=SIZES['h1'],
        leading=LEADING['h1'], textColor=COLORS['ink_700'],
        spaceBefore=SPACING['s6'], spaceAfter=SPACING['s1'],
    ),
    'H2': ParagraphStyle(
        'H2',
        fontName=FONTS['bold'], fontSize=SIZES['h2'],
        leading=LEADING['h2'], textColor=COLORS['ink_700'],
        spaceBefore=SPACING['s5'] + 2, spaceAfter=SPACING['s2'],
    ),
    'H3': ParagraphStyle(
        'H3',
        fontName=FONTS['bold'], fontSize=SIZES['h3'],
        leading=LEADING['h3'], textColor=COLORS['ink_700'],
        spaceBefore=SPACING['s4'], spaceAfter=SPACING['s1'],
    ),
    'H3Accent': ParagraphStyle(
        'H3Accent',
        fontName=FONTS['bold'], fontSize=SIZES['h3'],
        leading=LEADING['h3'], textColor=COLORS['accent'],
        spaceBefore=SPACING['s4'], spaceAfter=SPACING['s1'],
    ),
    'Body': ParagraphStyle(
        'Body',
        fontName=FONTS['regular'], fontSize=SIZES['body'],
        leading=LEADING['body'], textColor=COLORS['gray_900'],
        alignment=TA_JUSTIFY, spaceAfter=SPACING['s2'],
    ),
    'BlockQuote': ParagraphStyle(
        'BlockQuote',
        fontName=FONTS['regular'], fontSize=SIZES['body'],
        leading=LEADING['body'], textColor=COLORS['gray_900'],
        alignment=TA_JUSTIFY, spaceAfter=SPACING['s2'],
        leftIndent=SPACING['s4'],
    ),
    'RunInLabel': ParagraphStyle(
        'RunInLabel',
        fontName=FONTS['regular'], fontSize=SIZES['body'],
        leading=LEADING['body'], textColor=COLORS['gray_900'],
        alignment=TA_LEFT, spaceAfter=SPACING['s2'],
    ),
    'Bullet': ParagraphStyle(
        'Bullet',
        fontName=FONTS['regular'], fontSize=SIZES['body'],
        leading=LEADING['body'], textColor=COLORS['gray_900'],
        bulletText='•', leftIndent=12, bulletIndent=0,
        spaceAfter=SPACING['s1'],
    ),
    'SubBullet': ParagraphStyle(
        'SubBullet',
        fontName=FONTS['regular'], fontSize=SIZES['body'],
        leading=LEADING['body'], textColor=COLORS['gray_900'],
        bulletText='–', leftIndent=24, bulletIndent=12,
        spaceAfter=SPACING['s1'],
    ),
    'CoverEyebrow': ParagraphStyle(
        'CoverEyebrow',
        fontName=FONTS['regular'], fontSize=SIZES['eyebrow'],
        leading=LEADING['eyebrow'], textColor=COLORS['accent'],
        alignment=TA_LEFT,
    ),
    'CoverTitle': ParagraphStyle(
        'CoverTitle',
        fontName=FONTS['bold'], fontSize=SIZES['display'],
        leading=LEADING['display'], textColor=COLORS['white'],
        alignment=TA_LEFT, spaceBefore=SPACING['s5'],
        spaceAfter=SPACING['s4'],
    ),
    'CoverSubtitle': ParagraphStyle(
        'CoverSubtitle',
        fontName=FONTS['regular'], fontSize=SIZES['subtitle'],
        leading=LEADING['subtitle'], textColor=COLORS['accent'],
        alignment=TA_LEFT, spaceAfter=SPACING['s6'],
    ),
    'CoverStatCard': ParagraphStyle(
        'CoverStatCard',
        fontName=FONTS['regular'], fontSize=SIZES['cover_stat'],
        leading=LEADING['cover_stat'], textColor=COLORS['white'],
        alignment=TA_LEFT,
    ),
    'HeaderWordmark': ParagraphStyle(
        'HeaderWordmark',
        fontName=FONTS['regular'], fontSize=SIZES['header_wm'],
        leading=LEADING['header_wm'], textColor=COLORS['white'],
    ),
    'Footer': ParagraphStyle(
        'Footer',
        fontName=FONTS['regular'], fontSize=SIZES['footer'],
        leading=LEADING['footer'], textColor=COLORS['gray_500'],
    ),
    'TableHeader': ParagraphStyle(
        'TableHeader',
        fontName=FONTS['bold'], fontSize=SIZES['table'],
        leading=LEADING['table'], textColor=COLORS['white'],
    ),
    'TableBody': ParagraphStyle(
        'TableBody',
        fontName=FONTS['regular'], fontSize=SIZES['table'],
        leading=LEADING['table'], textColor=COLORS['gray_900'],
    ),
    'Code': ParagraphStyle(
        'Code',
        fontName=FONTS['mono'], fontSize=SIZES['code'],
        leading=LEADING['code'], textColor=COLORS['gray_900'],
        alignment=TA_LEFT,
    ),
    'Admonition': ParagraphStyle(
        'Admonition',
        fontName=FONTS['regular'], fontSize=SIZES['body'],
        leading=LEADING['body'], textColor=COLORS['gray_900'],
    ),
    'TOC_H1': ParagraphStyle(
        'TOC_H1',
        fontName=FONTS['bold'], fontSize=SIZES['toc_h1'],
        leading=LEADING['toc_h1'], textColor=COLORS['ink_700'],
    ),
    'TOC_H2': ParagraphStyle(
        'TOC_H2',
        fontName=FONTS['regular'], fontSize=SIZES['toc_h2'],
        leading=LEADING['toc_h2'], textColor=COLORS['gray_900'],
        leftIndent=SPACING['toc_indent'],
    ),
    'TOC_H3': ParagraphStyle(
        'TOC_H3',
        fontName=FONTS['regular'], fontSize=SIZES['toc_h3'],
        leading=LEADING['toc_h3'], textColor=COLORS['gray_500'],
        leftIndent=2 * SPACING['toc_indent'],
    ),
}

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE TEMPLATES
# ═══════════════════════════════════════════════════════════════════════════════


def _wordmark(doc_vars):
    """Organization × Client, dropping either side when it is unset."""
    parts = [doc_vars.get('Organization', ''), doc_vars.get('Client', '')]
    return ' × '.join(p for p in parts if p)


def _footer_left(doc_vars):
    """Title — Classification, dropping the classification slot when it is unset."""
    parts = [doc_vars.get('DocumentTitle', ''), doc_vars.get('Classification', '')]
    return ' — '.join(p for p in parts if p)


def make_cover_page_callback(doc_vars):
    def draw_cover_page(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(COLORS['ink_900'])
        canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        top_t = PAGE_CHROME['cover_top_bar']
        canvas.setFillColor(COLORS['accent'])
        canvas.rect(0, PAGE_H - top_t, PAGE_W, top_t, fill=1, stroke=0)
        bot_t = PAGE_CHROME['cover_bottom_bar']
        canvas.setFillColor(COLORS['accent'])
        canvas.rect(0, 0, PAGE_W, bot_t, fill=1, stroke=0)
        canvas.setFont(FONTS['regular'], SIZES['cover_footer'])
        canvas.setFillColor(COLORS['gray_500'])
        footer_y = bot_t + SPACING['s4']
        canvas.drawString(
            PAGE_CHROME['edge_margin'], footer_y,
            f"Exported: {doc_vars.get('date', '')}",
        )
        canvas.drawRightString(
            PAGE_W - PAGE_CHROME['edge_margin'], footer_y,
            doc_vars.get('Classification', ''),
        )
        canvas.restoreState()
    return draw_cover_page


def make_body_page_callback(doc_vars):
    def draw_body_page(canvas, doc):
        canvas.saveState()
        band_h = PAGE_CHROME['header_band']
        canvas.setFillColor(COLORS['ink_900'])
        canvas.rect(0, PAGE_H - band_h, PAGE_W, band_h, fill=1, stroke=0)
        canvas.setFont(FONTS['regular'], SIZES['header_wm'])
        canvas.setFillColor(COLORS['white'])
        wordmark = _wordmark(doc_vars)
        canvas.drawString(
            PAGE_CHROME['edge_margin'], PAGE_H - band_h / 2 - 4, wordmark,
        )
        rule_t = PAGE_CHROME['header_rule']
        canvas.setFillColor(COLORS['accent'])
        canvas.rect(0, PAGE_H - band_h - rule_t, PAGE_W, rule_t, fill=1, stroke=0)

        fb_h = PAGE_CHROME['footer_band']
        canvas.setFillColor(COLORS['gray_200'])
        canvas.rect(0, 0, PAGE_W, fb_h, fill=1, stroke=0)
        fr_t = PAGE_CHROME['footer_rule']
        canvas.setFillColor(COLORS['accent'])
        canvas.rect(0, fb_h, PAGE_W, fr_t, fill=1, stroke=0)

        canvas.setFont(FONTS['regular'], SIZES['footer'])
        canvas.setFillColor(COLORS['gray_500'])
        footer_y = (fb_h - SIZES['footer']) / 2 + 1
        footer_left = _footer_left(doc_vars)
        canvas.drawString(PAGE_CHROME['edge_margin'], footer_y, footer_left)
        canvas.drawRightString(
            PAGE_W - PAGE_CHROME['edge_margin'], footer_y,
            f"Page {doc.page}",
        )
        canvas.restoreState()
    return draw_body_page


def make_toc_page_callback(doc_vars):
    def draw_toc_page(canvas, doc):
        canvas.saveState()
        band_h = PAGE_CHROME['header_band']
        canvas.setFillColor(COLORS['ink_900'])
        canvas.rect(0, PAGE_H - band_h, PAGE_W, band_h, fill=1, stroke=0)
        canvas.setFont(FONTS['regular'], SIZES['header_wm'])
        canvas.setFillColor(COLORS['white'])
        wordmark = _wordmark(doc_vars)
        canvas.drawString(PAGE_CHROME['edge_margin'], PAGE_H - band_h / 2 - 4, wordmark)
        rule_t = PAGE_CHROME['header_rule']
        canvas.setFillColor(COLORS['accent'])
        canvas.rect(0, PAGE_H - band_h - rule_t, PAGE_W, rule_t, fill=1, stroke=0)

        fb_h = PAGE_CHROME['footer_band']
        canvas.setFillColor(COLORS['gray_200'])
        canvas.rect(0, 0, PAGE_W, fb_h, fill=1, stroke=0)
        fr_t = PAGE_CHROME['footer_rule']
        canvas.setFillColor(COLORS['accent'])
        canvas.rect(0, fb_h, PAGE_W, fr_t, fill=1, stroke=0)

        canvas.setFont(FONTS['regular'], SIZES['footer'])
        canvas.setFillColor(COLORS['gray_500'])
        footer_y = (fb_h - SIZES['footer']) / 2 + 1
        footer_left = _footer_left(doc_vars)
        canvas.drawString(PAGE_CHROME['edge_margin'], footer_y, footer_left)
        canvas.restoreState()
    return draw_toc_page

# ═══════════════════════════════════════════════════════════════════════════════
# BUILDERS
# ═══════════════════════════════════════════════════════════════════════════════


def _proportional_image(path: str, max_width: float, max_height: float | None = None,
                        h_align: str = 'LEFT') -> RLImage:
    iw, ih = ImageReader(path).getSize()
    scale = max_width / iw
    if max_height is not None:
        scale = min(scale, max_height / ih)
    return RLImage(path, width=iw * scale, height=ih * scale, hAlign=h_align)


def builder_h1(text):
    return KeepTogether([
        Paragraph(text, STYLES['H1']),
        HRFlowable(
            width='100%',
            thickness=RULES['h1']['thickness'],
            color=RULES['h1']['color'],
            spaceAfter=SPACING['s4'],
        ),
    ])


def builder_h2(text, with_rule=False):
    flowables = [Paragraph(text, STYLES['H2'])]
    if with_rule:
        flowables.append(HRFlowable(
            width='100%',
            thickness=RULES['hairline']['thickness'],
            color=RULES['hairline']['color'],
            spaceAfter=SPACING['s2'],
        ))
    return flowables


def builder_h3(text):
    return Paragraph(text, STYLES['H3'])


def builder_h3_accent(text):
    return Paragraph(text, STYLES['H3Accent'])


def builder_body(text):
    return Paragraph(text, STYLES['Body'])


def builder_bullets(items, level=1):
    style = STYLES['Bullet'] if level == 1 else STYLES['SubBullet']
    out = []
    for item in items:
        if isinstance(item, dict):
            out.append(Paragraph(item['text'], style))
            children = item.get('children') or []
            if children:
                out.extend(builder_bullets(children, level=2))
        else:
            out.append(Paragraph(str(item), style))
    return out


def builder_table_basic(headers, rows, col_widths):
    header_paras = [Paragraph(str(h), STYLES['TableHeader']) for h in headers]
    body_rows = []
    for row in rows:
        body_rows.append([Paragraph(str(c), STYLES['TableBody']) for c in row])
    data = [header_paras] + body_rows
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), COLORS['ink_900']),
        ('TEXTCOLOR',     (0, 0), (-1, 0), COLORS['white']),
        ('FONTNAME',      (0, 0), (-1, 0), FONTS['bold']),
        ('FONTSIZE',      (0, 0), (-1, -1), SIZES['table']),
        ('LEADING',       (0, 0), (-1, -1), LEADING['table']),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('GRID',          (0, 0), (-1, -1), 0.5, COLORS['gray_200']),
        ('TEXTCOLOR',     (0, 1), (-1, -1), COLORS['gray_900']),
        ('LEFTPADDING',   (0, 0), (-1, -1), SPACING['s3']),
        ('RIGHTPADDING',  (0, 0), (-1, -1), SPACING['s3']),
        ('TOPPADDING',    (0, 0), (-1, -1), SPACING['s2']),
        ('BOTTOMPADDING', (0, 0), (-1, -1), SPACING['s2']),
    ]))
    return t


def builder_code_block(text, width=None):
    if width is None:
        width = content_width
    safe = (
        text.replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace(' ', '&nbsp;')
        .replace('\n', '<br/>')
    )
    para = Paragraph(safe, STYLES['Code'])
    t = Table([[para]], colWidths=[width])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), COLORS['gray_200']),
        ('LEFTPADDING',   (0, 0), (-1, -1), SPACING['s3']),
        ('RIGHTPADDING',  (0, 0), (-1, -1), SPACING['s3']),
        ('TOPPADDING',    (0, 0), (-1, -1), SPACING['s2']),
        ('BOTTOMPADDING', (0, 0), (-1, -1), SPACING['s2']),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
    ]))
    return t


def builder_admonition(kind, text, width=None):
    if width is None:
        width = content_width
    palette = {
        'info':     {'bar': COLORS['ink_700'],   'fill': COLORS['gray_200']},
        'warning':  {'bar': COLORS['accent'], 'fill': COLORS['warning_fill']},
        'critical': {'bar': COLORS['red_600'],    'fill': COLORS['critical_fill']},
    }[kind.lower()]
    label = f"<b>{kind.upper()}:</b> {text}"
    para = Paragraph(label, STYLES['Admonition'])
    t = Table([[para]], colWidths=[width])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), palette['fill']),
        ('LINEBEFORE',    (0, 0), (0, -1), 3, palette['bar']),
        ('LEFTPADDING',   (0, 0), (-1, -1), SPACING['s4']),
        ('RIGHTPADDING',  (0, 0), (-1, -1), SPACING['s4']),
        ('TOPPADDING',    (0, 0), (-1, -1), SPACING['s3']),
        ('BOTTOMPADDING', (0, 0), (-1, -1), SPACING['s3']),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
    ]))
    return t


def builder_cover_story(doc_vars, next_template='body'):
    elements = [
        Paragraph(_wordmark(doc_vars), STYLES['CoverEyebrow']),
        HRFlowable(
            width=RULES['eyebrow']['width'],
            thickness=RULES['eyebrow']['thickness'],
            color=RULES['eyebrow']['color'],
            spaceAfter=SPACING['s4'],
            hAlign='LEFT',
        ),
        Paragraph(doc_vars.get('DocumentTitle', ''), STYLES['CoverTitle']),
        Paragraph(doc_vars.get('Subtitle', ''), STYLES['CoverSubtitle']),
    ]

    # Already resolved and checked by resolve_logo, so a logo that cannot be
    # drawn has stopped the run before this point rather than vanishing here.
    logo_path = doc_vars.get('logo')
    if logo_path:
        img = _proportional_image(logo_path, max_width=200, h_align='LEFT')
        elements.append(Spacer(1, SPACING['s4']))
        elements.append(img)

    elements.extend([
        Spacer(1, SPACING['s5']),
        NextPageTemplate(next_template),
        PageBreak(),
    ])
    return elements


def builder_toc_page(depth=1, enabled=True):
    if not enabled:
        return []
    from reportlab.platypus.tableofcontents import TableOfContents
    toc = TableOfContents()
    toc.levelStyles = [STYLES[f'TOC_H{i + 1}'] for i in range(depth)]
    return [builder_h1('Table of Contents'), toc, NextPageTemplate('body'), PageBreak()]

# ═══════════════════════════════════════════════════════════════════════════════
# PARSER
# ═══════════════════════════════════════════════════════════════════════════════

_ACCENT_SENTINEL = '\x00ACCENT\x00'

_FRONTMATTER_RE = re.compile(r'\A---\s*\n(.*?)\n---\s*\n', re.DOTALL)

_KEY_MAP = {
    'organization': 'Organization',
    'client': 'Client',
    'title': 'DocumentTitle',
    'subtitle': 'Subtitle',
    'classification': 'Classification',
    'industry': 'Industry',
    'date': 'date',
    'logo': 'logo',
    'accent': 'accent',
}


def extract_frontmatter(text: str) -> tuple[dict, str]:
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    raw = yaml.safe_load(m.group(1)) or {}
    doc_vars = {}
    for fm_key, dv_key in _KEY_MAP.items():
        if fm_key in raw:
            doc_vars[dv_key] = str(raw[fm_key])
    return doc_vars, text[m.end():]


def preprocess(text: str) -> str:
    text = re.sub(r'^###!\s+', f'### {_ACCENT_SENTINEL}', text, flags=re.MULTILINE)
    text = re.sub(r'^\\pagebreak\s*$', '<!-- pagebreak -->', text, flags=re.MULTILINE)
    return text


def _extract_block_quote_text(children: list[dict]) -> str:
    parts = []
    for child in children:
        if child['type'] == 'paragraph':
            parts.append(_inline_raw(child.get('children', [])))
        elif child['type'] == 'block_text':
            parts.append(_inline_raw(child.get('children', [])))
    return '\n\n'.join(parts)


def _inline_raw(nodes: list[dict]) -> str:
    parts = []
    for n in nodes:
        if n['type'] == 'text':
            parts.append(n.get('raw', ''))
        elif n['type'] in ('strong', 'emphasis', 'link'):
            parts.append(_inline_raw(n.get('children', [])))
        elif n['type'] == 'codespan':
            parts.append(n.get('raw', ''))
        elif n['type'] == 'softbreak':
            parts.append('\n')
        elif n['type'] == 'linebreak':
            parts.append('\n')
    return ''.join(parts)


_ADMONITION_RE = re.compile(r'^\[!(INFO|WARNING|CRITICAL)\]\s*\n?', re.IGNORECASE)

_WIDTHS_RE = re.compile(r'<!--\s*widths:\s*(.+?)\s*-->')

_MERMAID_WIDTH_RE = re.compile(r'<!--\s*mermaid-width:\s*(\d+(?:\.\d+)?)\s*-->')


def postprocess(tokens: list[dict]) -> list[dict]:
    out = []
    pending_widths = None
    pending_mermaid_width = None

    for tok in tokens:
        if tok['type'] == 'blank_line':
            continue

        if tok['type'] == 'block_html':
            raw = tok.get('raw', '').strip()
            if raw == '<!-- pagebreak -->':
                out.append({'type': 'pagebreak'})
                continue
            wm = _WIDTHS_RE.match(raw)
            if wm:
                pending_widths = wm.group(1).strip()
                continue
            mw = _MERMAID_WIDTH_RE.match(raw)
            if mw:
                pending_mermaid_width = float(mw.group(1))
                continue
            out.append(tok)
            continue

        if tok['type'] == 'block_quote':
            full_text = _extract_block_quote_text(tok.get('children', []))
            am = _ADMONITION_RE.match(full_text)
            if am:
                kind = am.group(1).lower()
                body_text = full_text[am.end():].strip()
                out.append({
                    'type': 'admonition',
                    'attrs': {'kind': kind},
                    'text': body_text,
                })
                continue

        if tok['type'] == 'heading':
            children = tok.get('children', [])
            if children and children[0].get('type') == 'text':
                raw_text = children[0].get('raw', '')
                if raw_text.startswith(_ACCENT_SENTINEL):
                    children[0]['raw'] = raw_text[len(_ACCENT_SENTINEL):]
                    tok = {**tok, 'attrs': {**tok.get('attrs', {}), 'accent': True}}

        if tok['type'] == 'table' and pending_widths:
            tok = {**tok, 'attrs': {**tok.get('attrs', {}), 'widths': pending_widths}}
            pending_widths = None

        if tok['type'] == 'block_code' and pending_mermaid_width is not None:
            tok = {**tok, 'attrs': {**tok.get('attrs', {}),
                                    'mermaid_width': pending_mermaid_width}}
            pending_mermaid_width = None

        out.append(tok)

    return out


def detect_heading_demotion(doc_vars: dict, tokens: list[dict]) -> tuple[dict, list[dict], int]:
    h1_tokens = [t for t in tokens if t.get('type') == 'heading'
                 and t.get('attrs', {}).get('level') == 1]

    if len(h1_tokens) != 1:
        return doc_vars, tokens, 0

    h1 = h1_tokens[0]
    title_text = _inline_raw(h1.get('children', []))

    if 'DocumentTitle' not in doc_vars:
        doc_vars = {**doc_vars, 'DocumentTitle': title_text}

    tokens = [t for t in tokens if t is not h1]

    out = []
    for t in tokens:
        if t.get('type') == 'heading':
            level = t.get('attrs', {}).get('level', 1)
            t = {**t, 'attrs': {**t.get('attrs', {}), 'level': max(1, level - 1)}}
        out.append(t)

    return doc_vars, out, 1


def parse(text: str) -> tuple[dict, list[dict], int]:
    doc_vars, body = extract_frontmatter(text)
    body = preprocess(body)
    md = mistune.create_markdown(renderer='ast', plugins=['table'])
    ast_tokens = md(body)
    ast_tokens = postprocess(ast_tokens)
    doc_vars, ast_tokens, heading_offset = detect_heading_demotion(doc_vars, ast_tokens)
    return doc_vars, ast_tokens, heading_offset

# ═══════════════════════════════════════════════════════════════════════════════
# MARKDOWN TO FLOWABLES
# ═══════════════════════════════════════════════════════════════════════════════

_BODY_TOP_INSET = PAGE_CHROME['header_band'] + PAGE_CHROME['header_rule'] + 12
_BODY_BOTTOM_INSET = PAGE_CHROME['footer_band'] + PAGE_CHROME['footer_rule'] + 8
_BODY_FRAME_HEIGHT = PAGE_H - _BODY_TOP_INSET - _BODY_BOTTOM_INSET

_mermaid_temp_files: list[str] = []

#: The Mermaid command-line renderer `npx` fetches on first use. Pinned, so the
#: package and the headless browser it downloads are the ones this was tested with.
MERMAID_CLI_VERSION = '11.17.0'

#: Generous because the first run downloads the package and a headless Chromium.
MERMAID_TIMEOUT_S = 180

_MERMAID_FALLBACK = 'Note: a mermaid block was rendered as code'
_noted_no_node = False


def _render_mermaid(source: str) -> str | None:
    global _noted_no_node
    npx = shutil.which('npx')
    if not (shutil.which('node') and npx):
        if not _noted_no_node:
            print(f'{_MERMAID_FALLBACK}: node and npx are not both on PATH', file=sys.stderr)
            _noted_no_node = True
        return None
    try:
        with tempfile.NamedTemporaryFile(suffix='.mmd', mode='w', delete=False) as f:
            f.write(source)
            mmd_path = f.name
        png_path = mmd_path.replace('.mmd', '.png')
        _mermaid_temp_files.extend([mmd_path, png_path])
        result = subprocess.run(  # nosec B603 # argument list; npx resolved by shutil.which
            [npx, '--yes', '-p', f'@mermaid-js/mermaid-cli@{MERMAID_CLI_VERSION}', 'mmdc',
             '-i', mmd_path, '-o', png_path, '-b', 'transparent', '-w', '800'],
            capture_output=True, timeout=MERMAID_TIMEOUT_S,
        )
        if result.returncode == 0 and Path(png_path).is_file():
            return png_path
        print(f'{_MERMAID_FALLBACK}: mermaid-cli failed: {result.stderr.decode()[:200]}',
              file=sys.stderr)
        return None
    except Exception as e:
        print(f'{_MERMAID_FALLBACK}: {e}', file=sys.stderr)
        return None


def cleanup_mermaid_temps():
    for p in _mermaid_temp_files:
        try:
            Path(p).unlink(missing_ok=True)
        except OSError:
            pass
    _mermaid_temp_files.clear()


def _escape_html(text: str) -> str:
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


# Status markers: color emoji have no glyphs in ReportLab's built-in fonts, so
# they fall back to monochrome boxes/tofu. Map each to a colored pill (label
# wrapped in a foreground/background <font> run) keyed by the source emoji.
# (fg, bg) tuples — amber/light-gray use dark text for contrast.
STATUS_MARKERS = {
    '✅':  ('#FFFFFF', '#1E874B'),  # ✅ Built — green
    '\U0001F7E6': ('#FFFFFF', '#2563EB'),  # 🟦 Built · single — blue
    '\U0001F7E8': ('#5B3A02', '#F4C430'),  # 🟨 Partial — amber
    '⬜':  ('#FFFFFF', '#8A929B'),  # ⬜ Gap — gray
    '⚪':  ('#3A4452', '#D4DBDB'),  # ⚪ Ops-owned / by-design — light gray
}

# Match an emoji marker (optional trailing variation selector) followed by an
# immediate bold label produced by inline_to_reportlab (`<b>...</b>`).
_STATUS_CLASS = '[' + ''.join(STATUS_MARKERS) + ']'
_STATUS_PILL_RE = re.compile(_STATUS_CLASS + r'️?\s*<b>(.*?)</b>')
_STATUS_BARE_RE = re.compile(_STATUS_CLASS + r'️?')


def _status_chip(marker: str) -> str:
    _, bg = STATUS_MARKERS[marker]
    return f'<font color="{bg}" backColor="{bg}">&nbsp;&nbsp;</font>'


def colorize_status_markers(s: str) -> str:
    """Turn `<emoji> <b>label</b>` into a colored pill; bare emoji into a chip."""
    def pill(m: re.Match) -> str:
        marker = m.group(0)[0]
        fg, bg = STATUS_MARKERS[marker]
        label = _STATUS_BARE_RE.sub(lambda b: _status_chip(b.group(0)[0]), m.group(1))
        return f'<font color="{fg}" backColor="{bg}">&nbsp;{label}&nbsp;</font>'

    s = _STATUS_PILL_RE.sub(pill, s)
    s = _STATUS_BARE_RE.sub(lambda m: _status_chip(m.group(0)[0]), s)
    return s


def inline_to_reportlab(children: list[dict]) -> str:
    parts = []
    for node in children:
        ntype = node.get('type', '')
        if ntype == 'text':
            parts.append(_escape_html(node.get('raw', '')))
        elif ntype == 'strong':
            inner = inline_to_reportlab(node.get('children', []))
            parts.append(f'<b>{inner}</b>')
        elif ntype == 'emphasis':
            inner = inline_to_reportlab(node.get('children', []))
            parts.append(f'<i>{inner}</i>')
        elif ntype == 'codespan':
            escaped = _escape_html(node.get('raw', ''))
            parts.append(f'<font name="Courier">{escaped}</font>')
        elif ntype == 'link':
            text = inline_to_reportlab(node.get('children', []))
            url = _escape_html(node.get('attrs', {}).get('url', ''))
            parts.append(f'{text} ({url})')
        elif ntype == 'image':
            alt = inline_to_reportlab(node.get('children', []))
            url = node.get('attrs', {}).get('url', '')
            print(f'Warning: image dropped: ![{alt}]({url})', file=sys.stderr)
        elif ntype == 'linebreak':
            parts.append('<br/>')
        elif ntype == 'softbreak':
            parts.append(' ')
    return colorize_status_markers(''.join(parts))


def _extract_list_items(list_token: dict) -> list:
    items = []
    for li in list_token.get('children', []):
        if li.get('type') != 'list_item':
            continue
        text_parts = []
        nested_list = None
        for child in li.get('children', []):
            if child['type'] in ('paragraph', 'block_text'):
                text_parts.append(inline_to_reportlab(child.get('children', [])))
            elif child['type'] == 'list':
                nested_list = child
        text = ' '.join(text_parts)
        if nested_list:
            items.append({'text': text, 'children': _extract_list_items(nested_list)})
        else:
            items.append(text)
    return items


def _parse_widths(widths_str: str, n_cols: int) -> list[float]:
    parts = widths_str.split()
    widths = []
    for part in parts:
        part = part.strip()
        if part.endswith('%'):
            widths.append(content_width * float(part[:-1]) / 100.0)
        elif part.endswith('pt'):
            widths.append(float(part[:-2]))
        else:
            try:
                widths.append(float(part))
            except ValueError:
                widths.append(content_width / n_cols)
    while len(widths) < n_cols:
        widths.append(content_width / n_cols)
    return widths[:n_cols]


def _extract_table(token: dict) -> tuple[list[str], list[list[str]], list[float]]:
    headers = []
    rows = []
    for child in token.get('children', []):
        if child['type'] == 'table_head':
            for cell in child.get('children', []):
                headers.append(inline_to_reportlab(cell.get('children', [])))
        elif child['type'] == 'table_body':
            for row in child.get('children', []):
                cells = []
                for cell in row.get('children', []):
                    cells.append(inline_to_reportlab(cell.get('children', [])))
                rows.append(cells)

    n_cols = max(len(headers), max((len(r) for r in rows), default=0)) if (headers or rows) else 1

    widths_str = token.get('attrs', {}).get('widths')
    if widths_str:
        col_widths = _parse_widths(widths_str, n_cols)
    else:
        col_widths = [content_width / n_cols] * n_cols

    return headers, rows, col_widths


def ast_to_flowables(tokens: list[dict]) -> list:
    story = []

    for token in tokens:
        ttype = token.get('type', '')

        if ttype == 'heading':
            level = token.get('attrs', {}).get('level', 1)
            accent = token.get('attrs', {}).get('accent', False)
            text = inline_to_reportlab(token.get('children', []))
            if level == 1:
                story.append(builder_h1(text))
            elif level == 2:
                result = builder_h2(text)
                story.extend(result)
            elif level == 3:
                if accent:
                    story.append(builder_h3_accent(text))
                else:
                    story.append(builder_h3(text))
            else:
                story.append(builder_h3(text))

        elif ttype == 'paragraph':
            text = inline_to_reportlab(token.get('children', []))
            if text.strip():
                story.append(builder_body(text))

        elif ttype == 'list':
            items = _extract_list_items(token)
            story.extend(builder_bullets(items))

        elif ttype == 'table':
            headers, rows, col_widths = _extract_table(token)
            story.append(builder_table_basic(headers, rows, col_widths))

        elif ttype == 'block_code':
            info = token.get('attrs', {}).get('info', '') or ''
            raw = token.get('raw', '').rstrip('\n')
            if info.strip().lower() == 'mermaid':
                png_path = _render_mermaid(raw)
                if png_path:
                    width_override = token.get('attrs', {}).get('mermaid_width')
                    max_w = width_override if width_override is not None else SIZES['mermaid_width']
                    max_w = min(max_w, content_width)
                    img = _proportional_image(png_path, max_width=max_w,
                                              max_height=_BODY_FRAME_HEIGHT,
                                              h_align='CENTER')
                    story.append(img)
                else:
                    story.append(builder_code_block(raw))
            else:
                story.append(builder_code_block(raw))

        elif ttype == 'block_quote':
            for child in token.get('children', []):
                if child['type'] in ('paragraph', 'block_text'):
                    text = inline_to_reportlab(child.get('children', []))
                    story.append(Paragraph(text, STYLES['BlockQuote']))

        elif ttype == 'admonition':
            kind = token.get('attrs', {}).get('kind', 'info')
            text = _escape_html(token.get('text', ''))
            story.append(builder_admonition(kind, text))

        elif ttype == 'thematic_break':
            story.append(Spacer(1, SPACING['s2']))
            story.append(HRFlowable(
                width='100%',
                thickness=RULES['hairline']['thickness'],
                color=RULES['hairline']['color'],
                spaceBefore=0,
                spaceAfter=0,
            ))
            story.append(Spacer(1, SPACING['s2']))

        elif ttype == 'pagebreak':
            story.append(PageBreak())

    return story

# ═══════════════════════════════════════════════════════════════════════════════
# ASSEMBLY
# ═══════════════════════════════════════════════════════════════════════════════


class DesignDocTemplate(BaseDocTemplate):
    def __init__(self, *args, toc_depth=0, **kwargs):
        super().__init__(*args, **kwargs)
        self._toc_depth = toc_depth

    def afterFlowable(self, flowable):
        if self._toc_depth < 1:
            return
        style_to_level = {'H1': 0, 'H2': 1, 'H3': 2}
        paragraphs = []
        if isinstance(flowable, KeepTogether):
            paragraphs = [c for c in flowable._content if isinstance(c, Paragraph)]
        elif isinstance(flowable, Paragraph):
            paragraphs = [flowable]
        for para in paragraphs:
            level = style_to_level.get(para.style.name)
            if level is not None and level < self._toc_depth:
                plain = para.getPlainText()
                if plain == TOC_TITLE_TEXT:
                    continue
                self.notify('TOCEntry', (level, plain, self.page))


def build_pdf(story: list, doc_vars: dict, output_path: Path, *,
              toc_enabled: bool = True, toc_depth: int = 1) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cover_frame = Frame(
        PAGE_CHROME['cover_margin'],
        80,
        PAGE_W - 2 * PAGE_CHROME['cover_margin'],
        PAGE_H - 320,
        id='cover',
        leftPadding=0, rightPadding=0,
        topPadding=0, bottomPadding=0,
    )

    top_inset = PAGE_CHROME['header_band'] + PAGE_CHROME['header_rule'] + 12
    bottom_inset = PAGE_CHROME['footer_band'] + PAGE_CHROME['footer_rule'] + 8
    body_frame = Frame(
        PAGE_CHROME['margin'],
        bottom_inset,
        content_width,
        PAGE_H - top_inset - bottom_inset,
        id='body',
        leftPadding=0, rightPadding=0,
        topPadding=0, bottomPadding=0,
    )

    toc_frame = Frame(
        PAGE_CHROME['margin'],
        bottom_inset,
        content_width,
        PAGE_H - top_inset - bottom_inset,
        id='toc',
        leftPadding=0, rightPadding=0,
        topPadding=0, bottomPadding=0,
    )

    cover_template = PageTemplate(
        id='cover',
        frames=[cover_frame],
        onPage=make_cover_page_callback(doc_vars),
    )
    body_template = PageTemplate(
        id='body',
        frames=[body_frame],
        onPage=make_body_page_callback(doc_vars),
    )
    toc_template = PageTemplate(
        id='toc',
        frames=[toc_frame],
        onPage=make_toc_page_callback(doc_vars),
    )

    doc = DesignDocTemplate(
        str(output_path),
        pagesize=LETTER,
        pageTemplates=[cover_template, toc_template, body_template],
        toc_depth=toc_depth if toc_enabled else 0,
        title=doc_vars.get('DocumentTitle', ''),
        author=doc_vars.get('Organization', ''),
        showBoundary=0,
    )

    doc.multiBuild(story)
    return output_path

# ═══════════════════════════════════════════════════════════════════════════════
# OVERRIDES
# ═══════════════════════════════════════════════════════════════════════════════


def set_accent(value: str) -> None:
    """Make `value` the colour of every accent-coloured element.

    RULES and STYLES captured the default accent's object when they were built,
    so every entry still holding that object is pointed at the new one. The page
    callbacks and builder_admonition read COLORS['accent'] when they draw.
    """
    old, new = COLORS['accent'], HexColor(value)
    COLORS['accent'] = new
    for rule in RULES.values():
        if rule['color'] is old:
            rule['color'] = new
    for style in STYLES.values():
        if style.textColor is old:
            style.textColor = new


def resolve_accent(flag: str | None, doc_vars: dict) -> tuple[str | None, str | None]:
    """`(accent, None)`, or `(None, error)` when the value that wins is not #RRGGBB.

    `--accent` wins over frontmatter `accent:`, which wins over DEFAULT_ACCENT.
    """
    if flag is not None:
        value, source = flag, 'argument'
    elif 'accent' in doc_vars:
        value, source = doc_vars['accent'], 'frontmatter'
    else:
        return DEFAULT_ACCENT, None
    if _HEX_COLOR_RE.fullmatch(value):
        return value, None
    hint = ' (quote it in YAML: an unquoted # starts a comment)' if value == 'None' else ''
    return None, f'Error: accent "{value}" from {source} is not #RRGGBB{hint}'


def resolve_logo(flag: str | None, doc_vars: dict,
                 base_dir: Path) -> tuple[str | None, str | None]:
    """`(path or None, None)`, or `(None, error)` when the logo that wins cannot be drawn.

    `--logo` wins over frontmatter `logo:`. A relative path resolves against the
    input file's directory, whichever of the two it came from.
    """
    if flag is not None:
        value, source = flag, 'argument'
    elif doc_vars.get('logo'):
        value, source = doc_vars['logo'], 'frontmatter'
    else:
        return None, None
    path = Path(value)
    if not path.is_absolute():
        path = base_dir / path
    if not path.is_file():
        return None, f'Error: logo "{value}" from {source} does not exist: {path}'
    try:
        ImageReader(str(path)).getSize()
    except Exception as e:
        return None, f'Error: logo "{value}" from {source} is not a readable image: {e}'
    return str(path), None

# ═══════════════════════════════════════════════════════════════════════════════
# CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog='render_pdf_cli.py',
        description='Convert a markdown file to PDF',
    )
    parser.add_argument('input', type=Path, help='Input markdown file')
    parser.add_argument('-o', '--output', type=Path, help='Output PDF path (default: input stem + .pdf)')
    parser.add_argument('--organization', help='Override Organization template variable')
    parser.add_argument('--client', help='Override Client template variable')
    parser.add_argument('--title', help='Override DocumentTitle template variable')
    parser.add_argument('--subtitle', help='Override Subtitle template variable')
    parser.add_argument('--classification', help='Override Classification template variable')
    parser.add_argument('--industry', help='Override Industry template variable')
    parser.add_argument('--date', help='Override date template variable')
    parser.add_argument('--logo',
                        help="Cover logo image, relative to the input file's directory"
                             ' (default: frontmatter logo:, else none)')
    parser.add_argument('--accent',
                        help='Accent colour as #RRGGBB'
                             f' (default: frontmatter accent:, else {DEFAULT_ACCENT})')
    parser.add_argument('--no-toc', action='store_true', help='Disable table of contents page')
    parser.add_argument('--toc-depth', type=int, default=1, choices=[1, 2, 3],
                        help='TOC heading depth: 1=H1, 2=H1+H2, 3=H1+H2+H3 (default: 1)')

    args = parser.parse_args(argv)

    if not args.input.is_file():
        print(f'Error: input file not found: {args.input}', file=sys.stderr)
        return 1

    try:
        text = args.input.read_text(encoding='utf-8')
    except Exception as e:
        print(f'Error reading {args.input}: {e}', file=sys.stderr)
        return 1

    doc_vars, ast_tokens, heading_offset = parse(text)

    accent, accent_error = resolve_accent(args.accent, doc_vars)
    logo, logo_error = resolve_logo(args.logo, doc_vars, args.input.parent)
    if accent_error or logo_error:
        for error in (accent_error, logo_error):
            if error:
                print(error, file=sys.stderr)
        return 1
    set_accent(accent)
    doc_vars['logo'] = logo

    defaults = {
        'Organization': '',
        'Client': '',
        'DocumentTitle': args.input.stem,
        'Subtitle': '',
        'Classification': '',
        'Industry': '',
        'date': date.today().isoformat(),
    }
    for key, default in defaults.items():
        if key not in doc_vars:
            doc_vars[key] = default

    overrides = {
        'Organization': args.organization,
        'Client': args.client,
        'DocumentTitle': args.title,
        'Subtitle': args.subtitle,
        'Classification': args.classification,
        'Industry': args.industry,
        'date': args.date,
    }
    for key, value in overrides.items():
        if value is not None:
            doc_vars[key] = value

    output_path = args.output or args.input.with_suffix('.pdf')

    toc_enabled = not args.no_toc
    next_tmpl = 'toc' if toc_enabled else 'body'

    # Inside the try, because ast_to_flowables is what renders mermaid blocks to
    # temporary files, and the finally below has to remove them on every path.
    try:
        story = (
            builder_cover_story(doc_vars, next_template=next_tmpl)
            + builder_toc_page(depth=args.toc_depth, enabled=toc_enabled)
            + ast_to_flowables(ast_tokens)
        )
        result = build_pdf(story, doc_vars, output_path,
                           toc_enabled=toc_enabled, toc_depth=args.toc_depth)
    except Exception as e:
        print(f'Error building PDF: {e}', file=sys.stderr)
        return 1
    finally:
        cleanup_mermaid_temps()

    size_kb = result.stat().st_size / 1024
    print(f'Wrote {result} ({size_kb:.1f} KB)')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
