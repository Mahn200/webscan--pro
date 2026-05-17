"""
PDF Report Generator for WebScan Pro.
Generates bilingual (TR/EN) professional security reports using ReportLab with DejaVuSans TTF font.
Features: cover page, color-coded severity badges, vulnerability detail sections, page headers/footers.
"""

import logging
import os
from datetime import datetime, timezone
from io import BytesIO
from typing import Dict, List, Optional

from reportlab.lib import colors  # type: ignore
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT  # type: ignore
from reportlab.lib.fonts import addMapping  # type: ignore
from reportlab.lib.pagesizes import A4  # type: ignore
from reportlab.lib.styles import ParagraphStyle  # type: ignore
from reportlab.lib.units import inch, mm, cm  # type: ignore
from reportlab.platypus import (  # type: ignore
    BaseDocTemplate,
    Frame,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import Flowable  # type: ignore
from reportlab.pdfbase import pdfmetrics  # type: ignore
from reportlab.pdfbase.ttfonts import TTFont  # type: ignore
from reportlab.pdfgen import canvas  # type: ignore

logger = logging.getLogger("webscanpro.pdf_generator")

# ─── Font Registration ─────────────────────────────────────────────

FONT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets",
    "fonts",
    "DejaVuSans.ttf",
)

FONT_BOLD_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets",
    "fonts",
    "DejaVuSans-Bold.ttf",
)

FONT_REGISTERED = False


def _register_fonts() -> bool:
    """
    Register DejaVuSans TTF fonts with ReportLab as a font family.

    Registers all 4 variants (regular, bold, italic, bold-italic) and
    creates a font family mapping so ReportLab's Paragraph parser can
    resolve <b>, <i>, and <b><i> XML tags correctly.
    """
    global FONT_REGISTERED
    if FONT_REGISTERED:
        return True

    regular_path = FONT_PATH
    bold_path = FONT_BOLD_PATH

    try:
        if not os.path.exists(regular_path):
            logger.warning(
                f"DejaVuSans.ttf not found at {regular_path}. "
                "Falling back to Helvetica. Turkish characters may not render correctly."
            )
            return False

        # Register regular font
        pdfmetrics.registerFont(TTFont("DejaVuSans", regular_path))

        # Register bold font if it exists, otherwise fall back to regular
        if os.path.exists(bold_path):
            pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", bold_path))
        else:
            pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", regular_path))

        # Map italic to regular, bold-italic to bold (both files map their parent)
        pdfmetrics.registerFont(TTFont("DejaVuSans-Italic", regular_path))
        pdfmetrics.registerFont(
            TTFont(
                "DejaVuSans-BoldItalic",
                bold_path if os.path.exists(bold_path) else regular_path,
            )
        )

        # Register font family so ReportLab can resolve <b>/<i>/<b><i> XML tags
        addMapping("DejaVuSans", 0, 0, "DejaVuSans")  # regular
        addMapping("DejaVuSans", 1, 0, "DejaVuSans-Bold")  # bold
        addMapping("DejaVuSans", 0, 1, "DejaVuSans-Italic")  # italic
        addMapping("DejaVuSans", 1, 1, "DejaVuSans-BoldItalic")  # bold-italic
        logger.info(
            "Registered DejaVuSans font family (regular + bold, italic/oblique mapped to parent)."
        )

        FONT_REGISTERED = True
        return True

    except Exception as e:
        logger.error(f"Failed to register fonts: {e}", exc_info=True)
        return False


# ─── Color Constants ───────────────────────────────────────────────

SEVERITY_COLORS = {
    "critical": (
        colors.HexColor("#EF4444"),
        colors.HexColor("#FFFFFF"),
    ),  # red bg, white text
    "high": (
        colors.HexColor("#F59E0B"),
        colors.HexColor("#FFFFFF"),
    ),  # orange bg, white text
    "medium": (
        colors.HexColor("#3B82F6"),
        colors.HexColor("#FFFFFF"),
    ),  # blue bg, white text
    "low": (
        colors.HexColor("#22C55E"),
        colors.HexColor("#FFFFFF"),
    ),  # green bg, white text
    "info": (
        colors.HexColor("#6B7280"),
        colors.HexColor("#FFFFFF"),
    ),  # gray bg, white text
}

SCORE_COLORS = {
    "green": colors.HexColor("#22C55E"),
    "yellow": colors.HexColor("#F59E0B"),
    "orange": colors.HexColor("#F97316"),
    "red": colors.HexColor("#EF4444"),
}

DARK_BG = colors.HexColor("#0D1117")
DARK_TEXT = colors.HexColor("#F0F6FC")
CYAN = colors.HexColor("#00D4FF")
DARK_CARD = colors.HexColor("#161B22")
DARK_EVIDENCE = colors.HexColor("#1C2128")
GRAY_MUTED = colors.HexColor("#8B949E")


# ─── Strings for bilingual support ────────────────────────────────

STRINGS = {
    "en": {
        "title": "WebScan Pro Security Report",
        "subtitle": "Security Report",
        "generated": "Generated:",
        "target": "Target URL",
        "score": "Security Score",
        "risk": "Risk Level",
        "summary": "Executive Summary",
        "findings_title": "Vulnerability Findings",
        "remediation_title": "Top Remediation Steps",
        "footer": "WebScan Pro v2.0 \u2014 AI-Powered Security Scanner",
        "no_findings": "No vulnerabilities found.",
        "severity": "Severity",
        "type": "Type",
        "title_col": "Title",
        "recommendation": "Recommendation",
        "confidential": "Confidential \u2014 Security Report",
        "ai_fix": "AI Fix:",
        "detail_title": "Detailed Vulnerability Analysis",
    },
    "tr": {
        "title": "WebScan Pro G\u00fcvenlik Raporu",
        "subtitle": "G\u00fcvenlik Raporu",
        "generated": "Olu\u015fturulma:",
        "target": "Hedef URL",
        "score": "G\u00fcvenlik Skoru",
        "risk": "Risk Seviyesi",
        "summary": "Y\u00f6netici \u00d6zeti",
        "findings_title": "G\u00fcvenlik A\u00e7\u0131klar\u0131",
        "remediation_title": "\u00d6nemli D\u00fczeltme Ad\u0131mlar\u0131",
        "footer": "WebScan Pro v2.0 \u2014 AI Destekli G\u00fcvenlik Taray\u0131c\u0131s\u0131",
        "no_findings": "G\u00fcvenlik a\u00e7\u0131\u011f\u0131 bulunamad\u0131.",
        "severity": "Seviye",
        "type": "T\u00fcr",
        "title_col": "Ba\u015fl\u0131k",
        "recommendation": "\u00d6neri",
        "confidential": "Gizli \u2014 G\u00fcvenlik Raporu",
        "ai_fix": "AI \u00c7\u00f6z\u00fcm\u00fc:",
        "detail_title": "Detayl\u0131 G\u00fcvenlik A\u00e7\u0131\u011f\u0131 Analizi",
    },
}

REMEDIATION_STEPS = {
    "en": [
        "Fix all critical and high severity vulnerabilities immediately.",
        "Implement input validation and output encoding on all user inputs.",
        "Configure security headers (HSTS, CSP, X-Frame-Options, etc.).",
        "Use parameterized queries to prevent SQL injection.",
        "Conduct regular security scanning and monitoring.",
    ],
    "tr": [
        "T\u00fcm kritik ve y\u00fcksek \u00f6ncelikli a\u00e7\u0131klar\u0131 hemen d\u00fczeltin.",
        "T\u00fcm kullan\u0131c\u0131 girdilerinde do\u011frulama ve \u00e7\u0131kt\u0131 kodlamas\u0131 uygulay\u0131n.",
        "G\u00fcvenlik ba\u015fl\u0131klar\u0131n\u0131 yap\u0131land\u0131r\u0131n (HSTS, CSP, X-Frame-Options, vb.).",
        "SQL enjeksiyonunu \u00f6nlemek i\u00e7in parametreli sorgular kullan\u0131n.",
        "D\u00fczenli g\u00fcvenlik taramas\u0131 ve izleme yap\u0131n.",
    ],
}


# ─── Helper: Get score color based on value ────────────────────────


def _get_score_color(score: float) -> colors.Color:
    """Return a color based on the security score range."""
    if score >= 80:
        return SCORE_COLORS["green"]
    elif score >= 50:
        return SCORE_COLORS["yellow"]
    elif score >= 25:
        return SCORE_COLORS["orange"]
    else:
        return SCORE_COLORS["red"]


# ─── Custom Flowable: Cover Page ───────────────────────────────────


class CoverPage(Flowable):
    """A full-page cover with dark background, title, score, and metadata."""

    def __init__(self, strings: dict, session_data: dict, vulnerabilities: list):
        Flowable.__init__(self)
        self.strings = strings
        self.session_data = session_data
        self.vulnerabilities = vulnerabilities
        self.width = A4[0]
        self.height = A4[1]

    def draw(self):
        c = self.canv
        page_w = self.width
        page_h = self.height

        # Dark background
        c.setFillColor(DARK_BG)
        c.rect(0, 0, page_w, page_h, stroke=0, fill=1)

        # ─── Title ───────────────────────────────────────────────
        c.setFillColor(DARK_TEXT)
        font_bold = "DejaVuSans-Bold" if FONT_REGISTERED else "Helvetica-Bold"
        font_normal = "DejaVuSans" if FONT_REGISTERED else "Helvetica"

        c.setFont(font_bold, 36)
        c.drawCentredString(page_w / 2, page_h - 100, "WebScan Pro")

        # ─── Subtitle ────────────────────────────────────────────
        c.setFont(font_normal, 18)
        c.setFillColor(CYAN)
        c.drawCentredString(page_w / 2, page_h - 140, self.strings["subtitle"])

        # ─── Separator line ──────────────────────────────────────
        c.setStrokeColor(CYAN)
        c.setLineWidth(1.5)
        c.line(page_w * 0.2, page_h - 160, page_w * 0.8, page_h - 160)

        # ─── Target URL ──────────────────────────────────────────
        target_url = self.session_data.get("target_url", "N/A")
        c.setFillColor(DARK_TEXT)
        c.setFont(font_normal, 14)
        c.drawCentredString(page_w / 2, page_h - 200, target_url)

        # ─── Security Score ──────────────────────────────────────
        score = self.session_data.get("security_score", 0)
        score_color = _get_score_color(score)

        c.setFillColor(score_color)
        c.setFont(font_bold, 64)
        c.drawCentredString(page_w / 2, page_h - 290, f"{score:.0f}")

        c.setFillColor(GRAY_MUTED)
        c.setFont(font_normal, 14)
        c.drawCentredString(page_w / 2, page_h - 315, self.strings["score"])

        # ─── Risk Level Badge ────────────────────────────────────
        risk_level = self.session_data.get("risk_level", "info")
        risk_bg, risk_text = SEVERITY_COLORS.get(risk_level, SEVERITY_COLORS["info"])

        badge_w = 120
        badge_h = 28
        badge_x = (page_w - badge_w) / 2
        badge_y = page_h - 355

        c.setFillColor(risk_bg)
        c.roundRect(badge_x, badge_y, badge_w, badge_h, 4, stroke=0, fill=1)

        c.setFillColor(colors.white)
        c.setFont(font_bold, 11)
        c.drawCentredString(page_w / 2, badge_y + 8, risk_level.upper())

        c.setFillColor(GRAY_MUTED)
        c.setFont(font_normal, 10)
        c.drawCentredString(page_w / 2, badge_y - 16, self.strings["risk"])

        # ─── Generation date ─────────────────────────────────────
        gen_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        c.setFillColor(GRAY_MUTED)
        c.setFont(font_normal, 9)
        c.drawCentredString(
            page_w / 2, badge_y - 50, f"{self.strings['generated']} {gen_date}"
        )

        # ─── Warning text ─────────────────────────────────────────
        c.setFont(font_normal, 10)
        c.setFillColor(GRAY_MUTED)
        warning_text = (
            f"{len(self.vulnerabilities)} vulnerability findings detected"
            if self.strings == STRINGS["en"]
            else f"{len(self.vulnerabilities)} g\u00fcvenlik a\u00e7\u0131\u011f\u0131 tespit edildi"
        )
        c.drawCentredString(page_w / 2, badge_y - 80, warning_text)

        # ─── Footer ──────────────────────────────────────────────
        c.setFont(font_normal, 8)
        c.setFillColor(GRAY_MUTED)
        c.drawCentredString(page_w / 2, 30, self.strings["footer"])


# ─── Custom Flowable: Severity Badge ──────────────────────────────


class SeverityBadge(Flowable):
    """A colored rectangle badge for severity display."""

    def __init__(self, severity: str, text: str = ""):
        Flowable.__init__(self)
        self.severity = severity
        self.label = (text or severity).upper()
        self.width = 70
        self.height = 16

    def draw(self):
        c = self.canv
        bg_color, _ = SEVERITY_COLORS.get(self.severity, SEVERITY_COLORS["info"])
        c.setFillColor(bg_color)
        c.roundRect(0, 0, self.width, self.height, 3, stroke=0, fill=1)
        c.setFillColor(colors.white)
        font_bold = "DejaVuSans-Bold" if FONT_REGISTERED else "Helvetica-Bold"
        c.setFont(font_bold, 7)
        c.drawCentredString(self.width / 2, 4, self.label)


# ─── Custom Flowable: Horizontal Divider with Color ───────────────


class ColoredDivider(Flowable):
    """A horizontal line divider in a specified color."""

    def __init__(self, color: colors.Color = GRAY_MUTED, width_ratio: float = 1.0):
        Flowable.__init__(self)
        self.div_color = color
        self.width_ratio = width_ratio
        self.width = A4[0] - 30 * mm  # Will be adjusted in draw

    def draw(self):
        c = self.canv
        c.setStrokeColor(self.div_color)
        c.setLineWidth(0.5)
        c.line(0, 0, self.width * self.width_ratio, 0)


# ─── Custom Flowable: Evidence Box ────────────────────────────────


class EvidenceBox(Flowable):
    """A gray-background box for evidence text with monospace font."""

    def __init__(self, text: str, max_width: float):
        Flowable.__init__(self)
        self.text = text
        self.max_width = max_width
        self.width = max_width
        # Estimate height based on text length
        chars_per_line = max(40, int(max_width / 4.5))
        num_lines = max(1, (len(text) // chars_per_line) + 1)
        self.height = max(30, num_lines * 11 + 10)

    def draw(self):
        c = self.canv
        # Background
        c.setFillColor(DARK_EVIDENCE)
        c.roundRect(0, 0, self.width, self.height, 4, stroke=0, fill=1)
        # Border
        c.setStrokeColor(GRAY_MUTED)
        c.setLineWidth(0.5)
        c.roundRect(0, 0, self.width, self.height, 4, stroke=1, fill=0)
        # Text - wrap manually
        c.setFillColor(DARK_TEXT)
        c.setFont("Courier", 7)
        chars_per_line = max(40, int(self.width / 4.5))
        y = self.height - 12
        for i in range(0, len(self.text), chars_per_line):
            line = self.text[i : i + chars_per_line]
            c.drawString(8, y, line)
            y -= 11
            if y < 5:
                break


# ─── Custom Flowable: Executive Summary Card ──────────────────────


class SummaryCard(Flowable):
    """A styled card for executive summary with cyan left border."""

    def __init__(self, text: str, width: float):
        Flowable.__init__(self)
        self.text = text
        self.max_width = width
        self.width = width
        font_normal = "DejaVuSans" if FONT_REGISTERED else "Helvetica"
        # Estimate height
        chars_per_line = max(50, int(width / 4.2))
        num_lines = max(1, (len(text) // chars_per_line) + 1)
        self.height = max(40, num_lines * 13 + 20)

    def draw(self):
        c = self.canv
        h = self.height
        w = self.width

        # Background
        c.setFillColor(DARK_CARD)
        c.roundRect(0, 0, w, h, 4, stroke=0, fill=1)

        # Left border (3px cyan line)
        c.setStrokeColor(CYAN)
        c.setLineWidth(3)
        c.line(6, 4, 6, h - 4)

        # Text
        c.setFillColor(DARK_TEXT)
        font_normal = "DejaVuSans" if FONT_REGISTERED else "Helvetica"
        c.setFont(font_normal, 9)

        chars_per_line = max(50, int((w - 20) / 4.2))
        y = h - 14
        for i in range(0, len(self.text), chars_per_line):
            line = self.text[i : i + chars_per_line]
            c.drawString(16, y, line)
            y -= 13
            if y < 5:
                break


# ─── Custom Flowable: Vulnerability Detail Section ────────────────


class VulnerabilityDetail(Flowable):
    """A detailed section for a single HIGH/CRITICAL vulnerability."""

    def __init__(self, vuln: dict, strings: dict, width: float):
        Flowable.__init__(self)
        self.vuln = vuln
        self.strings = strings
        self.max_width = width
        self.width = width
        self._calculate_height()

    def _calculate_height(self):
        """Estimate the total height needed for this detail section."""
        h = 0
        # Severity badge + title line
        h += 24
        # Divider
        h += 12
        # Description
        desc = self.vuln.get("description", "")
        desc_lines = max(1, len(desc) // 60 + 1)
        h += desc_lines * 13 + 10
        # Evidence box
        evidence = self.vuln.get("evidence", "")
        ev_lines = max(1, len(evidence) // 40 + 1)
        h += ev_lines * 11 + 20
        # Remediation
        h += 20
        # Bottom spacing
        h += 16
        self.height = h

    def draw(self):
        c = self.canv
        y = self.height
        font_bold = "DejaVuSans-Bold" if FONT_REGISTERED else "Helvetica-Bold"
        font_normal = "DejaVuSans" if FONT_REGISTERED else "Helvetica"

        # ─── Severity badge + Title ──────────────────────────────
        severity = self.vuln.get("severity", "info")
        sev_bg, _ = SEVERITY_COLORS.get(severity, SEVERITY_COLORS["info"])
        badge_w = 70
        badge_h = 18
        c.setFillColor(sev_bg)
        c.roundRect(0, y - badge_h - 2, badge_w, badge_h, 3, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont(font_bold, 8)
        c.drawCentredString(badge_w / 2, y - badge_h + 4, severity.upper())

        # Title text next to badge
        title_text = self.vuln.get("title", "")
        c.setFillColor(DARK_TEXT)
        c.setFont(font_bold, 11)
        # Truncate title if too long
        max_title_chars = int((self.max_width - badge_w - 12) / 5.5)
        truncated_title = title_text[:max_title_chars]
        c.drawString(badge_w + 10, y - badge_h + 3, truncated_title)

        y -= badge_h + 10

        # ─── Divider ─────────────────────────────────────────────
        c.setStrokeColor(GRAY_MUTED)
        c.setLineWidth(0.5)
        c.line(0, y, self.max_width, y)
        y -= 8

        # ─── Description ─────────────────────────────────────────
        desc = self.vuln.get("description", "")
        c.setFillColor(DARK_TEXT)
        c.setFont(font_normal, 8)
        chars_per_line = int(self.max_width / 4.5)
        for i in range(0, len(desc), chars_per_line):
            line = desc[i : i + chars_per_line]
            c.drawString(4, y, line)
            y -= 13
            if y < 5:
                break
        y -= 4

        # ─── Evidence box ────────────────────────────────────────
        evidence = self.vuln.get("evidence", "")
        ev_lines = max(1, len(evidence) // 40 + 1)
        ev_height = ev_lines * 11 + 10

        if evidence:
            c.setFillColor(DARK_EVIDENCE)
            c.roundRect(
                4, y - ev_height, self.max_width - 8, ev_height, 4, stroke=0, fill=1
            )
            c.setStrokeColor(GRAY_MUTED)
            c.setLineWidth(0.5)
            c.roundRect(
                4, y - ev_height, self.max_width - 8, ev_height, 4, stroke=1, fill=0
            )

            c.setFillColor(DARK_TEXT)
            c.setFont("Courier", 7)
            ev_chars = int((self.max_width - 20) / 4.5)
            ev_y = y - 12
            for i in range(0, len(evidence), ev_chars):
                line = evidence[i : i + ev_chars]
                c.drawString(12, ev_y, line)
                ev_y -= 11
                if ev_y < y - ev_height + 5:
                    break
            y -= ev_height + 6

        # ─── AI Fix Recommendation ──────────────────────────────
        remediation = self.vuln.get("remediation", "")
        if remediation:
            c.setFillColor(CYAN)
            c.setFont(font_bold, 9)
            c.drawString(4, y, self.strings["ai_fix"])
            y -= 13

            c.setFillColor(DARK_TEXT)
            c.setFont(font_normal, 8)
            rem_chars = int(self.max_width / 4.5)
            for i in range(0, len(remediation), rem_chars):
                line = remediation[i : i + rem_chars]
                c.drawString(4, y, line)
                y -= 13
                if y < 5:
                    break


# ─── Two-Pass Canvas for accurate "Page X of Y" ─────────────────


class PageNumCanvas(canvas.Canvas):
    """
    A canvas that does a two-pass build to get the accurate total page count.

    On the first pass, it captures the state of every page via showPage().
    On save(), it replays all pages with the correct total page count drawn
    as "Page X of Y".
    """

    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        """Capture current page state instead of finalizing."""
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """
        Final save: redraw each page with correct total page count.

        Iterates through saved page states, restores each, draws the
        page number footer, then writes the page.
        """
        num_pages = len(self._saved_page_states)
        for page_state in self._saved_page_states:
            self.__dict__.update(page_state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count: int):
        """Draw 'Page X of Y' centered in the footer area."""
        page_w = A4[0]
        margin_bottom = 18 * mm
        self.setFont("DejaVuSans", 7)
        self.setFillColor(GRAY_MUTED)
        self.drawCentredString(
            page_w / 2,
            margin_bottom - 10,
            f"Page {self._pageNumber} of {page_count}",
        )


# ─── Page Template Callbacks ──────────────────────────────────────


def _cover_page_before(canvas_obj: canvas.Canvas, doc):
    """Paint dark background on the cover page."""
    canvas_obj.saveState()
    canvas_obj.setFillColor(colors.HexColor("#0D1117"))
    canvas_obj.rect(0, 0, doc.pagesize[0], doc.pagesize[1], fill=1)
    canvas_obj.restoreState()


def _content_header_footer(canvas_obj: canvas.Canvas, doc):
    """Draw dark background, header and footer on every content page."""
    # Paint full-page dark background
    canvas_obj.saveState()
    canvas_obj.setFillColor(colors.HexColor("#0D1117"))
    canvas_obj.rect(0, 0, doc.pagesize[0], doc.pagesize[1], fill=1)
    canvas_obj.restoreState()

    page_w = A4[0]
    page_h = A4[1]
    margin_left = 15 * mm
    margin_right = page_w - 15 * mm
    margin_top = page_h - 18 * mm
    margin_bottom = 18 * mm

    font_normal = "DejaVuSans" if FONT_REGISTERED else "Helvetica"
    font_bold = "DejaVuSans-Bold" if FONT_REGISTERED else "Helvetica-Bold"

    strings = getattr(doc, "_strings", STRINGS["en"])
    target_url = getattr(doc, "_target_url", "")

    # ─── Header ──────────────────────────────────────────────────
    # Left: "WebScan Pro" in cyan
    canvas_obj.setFillColor(CYAN)
    canvas_obj.setFont(font_bold, 8)
    canvas_obj.drawString(margin_left, margin_top, "WebScan Pro")

    # Right: Target URL in gray
    canvas_obj.setFillColor(GRAY_MUTED)
    canvas_obj.setFont(font_normal, 7)
    # Truncate long URLs
    display_url = target_url if len(target_url) < 60 else target_url[:57] + "..."
    canvas_obj.drawRightString(margin_right, margin_top, display_url)

    # Bottom border for header (1px dark border color)
    canvas_obj.setStrokeColor(colors.HexColor("#30363D"))
    canvas_obj.setLineWidth(1)
    canvas_obj.line(margin_left, margin_top - 4, margin_right, margin_top - 4)

    # ─── Footer ──────────────────────────────────────────────────
    # Left: Generation date
    gen_date = getattr(doc, "_gen_date", "")
    canvas_obj.setFillColor(GRAY_MUTED)
    canvas_obj.setFont(font_normal, 7)
    canvas_obj.drawString(margin_left, margin_bottom - 10, gen_date)

    # Right: Confidential (page number is drawn by PageNumCanvas.draw_page_number)
    canvas_obj.drawRightString(
        margin_right, margin_bottom - 10, strings["confidential"]
    )

    # Top border for footer (1px dark border color)
    canvas_obj.setStrokeColor(colors.HexColor("#30363D"))
    canvas_obj.setLineWidth(0.5)
    canvas_obj.line(margin_left, margin_bottom - 4, margin_right, margin_bottom - 4)


# ─── Styles ───────────────────────────────────────────────────────


def _get_style_sheet() -> dict:
    """Create a dictionary of paragraph styles using DejaVuSans if available."""
    font_name = "DejaVuSans" if FONT_REGISTERED else "Helvetica"
    font_bold = "DejaVuSans-Bold" if FONT_REGISTERED else "Helvetica-Bold"

    return {
        "heading": ParagraphStyle(
            "Heading",
            fontName=font_bold,
            fontSize=13,
            leading=17,
            spaceBefore=15,
            spaceAfter=10,
            textColor=CYAN,
        ),
        "normal": ParagraphStyle(
            "Normal",
            fontName=font_name,
            fontSize=10,
            leading=14,
            spaceBefore=4,
            spaceAfter=4,
            textColor=colors.HexColor("#C9D1D9"),
        ),
        "small": ParagraphStyle(
            "Small",
            fontName=font_name,
            fontSize=8,
            leading=10,
            spaceBefore=2,
            spaceAfter=2,
            textColor=colors.HexColor("#C9D1D9"),
        ),
        "table_header": ParagraphStyle(
            "TableHeader",
            fontName=font_bold,
            fontSize=8,
            leading=10,
            textColor=colors.white,
        ),
        "table_cell": ParagraphStyle(
            "TableCell",
            fontName=font_name,
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#C9D1D9"),
        ),
        "remediation": ParagraphStyle(
            "Remediation",
            fontName=font_name,
            fontSize=10,
            leading=14,
            spaceBefore=4,
            spaceAfter=4,
            textColor=colors.HexColor("#C9D1D9"),
            leftIndent=10,
        ),
        "footer_style": ParagraphStyle(
            "Footer",
            fontName=font_name,
            fontSize=7,
            leading=9,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#8B949E"),
        ),
    }


# ─── Main PDF Generation ──────────────────────────────────────────


def generate_pdf(
    session_data: Dict,
    vulnerabilities: List[Dict],
    language: str = "en",
) -> bytes:
    """
    Generate a professional PDF security report.

    Args:
        session_data: Dict with scan session metadata.
        vulnerabilities: List of vulnerability dicts.
        language: 'en' or 'tr'.

    Returns:
        PDF as bytes.
    """
    # Register fonts
    _register_fonts()
    logger.info(f"Generating PDF in language: {language}")

    strings = STRINGS.get(language, STRINGS["en"])
    styles = _get_style_sheet()

    buffer = BytesIO()
    page_w = A4[0]
    usable_width = A4[0] - 30 * mm

    # ─── Build document with two page templates ──────────────────

    # Frame for the cover page — zero padding so CoverPage (A4 size) fits exactly
    cover_frame = Frame(
        0,
        0,
        page_w,
        A4[1],
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
        id="cover",
    )
    cover_template = PageTemplate(
        id="cover",
        frames=[cover_frame],
        onPage=_cover_page_before,
        pagesize=A4,
    )

    # Frame for content pages (with margins for header/footer)
    content_frame = Frame(
        15 * mm,
        22 * mm,  # bottom margin (footer area)
        A4[0] - 30 * mm,
        A4[1] - 40 * mm,  # top margin (header area)
        id="content",
    )
    content_template = PageTemplate(
        id="content",
        frames=[content_frame],
        onPage=_content_header_footer,
        pagesize=A4,
    )

    # Build with our custom doc template
    class WebScanDoc(BaseDocTemplate):
        def __init__(self, *args, **kwargs):
            BaseDocTemplate.__init__(self, *args, **kwargs)
            self._strings = strings
            self._target_url = session_data.get("target_url", "")
            self._gen_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        def afterPage(self):
            pass

        def handle_pageBegin(self):
            BaseDocTemplate.handle_pageBegin(self)

    doc = WebScanDoc(
        buffer,
        pagesize=A4,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
    )
    doc.addPageTemplates([cover_template, content_template])

    elements = []
    current_step = "initializing"

    try:
        # ═══════════════════════════════════════════════════════════════
        # PAGE 1: COVER PAGE
        # ═══════════════════════════════════════════════════════════════
        current_step = "cover_page"
        # CoverPage first — cover_template is already the default first template
        elements.append(CoverPage(strings, session_data, vulnerabilities))
        # Switch to content template for remaining pages
        elements.append(NextPageTemplate("content"))
        elements.append(PageBreak())

        # ═══════════════════════════════════════════════════════════════
        # PAGE 2+: EXECUTIVE SUMMARY
        # ═══════════════════════════════════════════════════════════════
        current_step = "executive_summary"

        # Section title
        elements.append(Paragraph(strings["summary"], styles["heading"]))

        # Summary card
        SUMMARY_FALLBACK = {
            "en": (
                f"Scan completed with {len(vulnerabilities)} findings. "
                f"Security score: {session_data.get('security_score', 0):.1f}/100."
            ),
            "tr": (
                f"Tarama tamamland\u0131, {len(vulnerabilities)} g\u00fcvenlik a\u00e7\u0131\u011f\u0131 bulundu. "
                f"G\u00fcvenlik skoru: {session_data.get('security_score', 0):.1f}/100."
            ),
        }
        summary_text = session_data.get("ai_summary") or SUMMARY_FALLBACK.get(
            language, SUMMARY_FALLBACK["en"]
        )
        elements.append(SummaryCard(summary_text, usable_width))
        elements.append(Spacer(1, 12))

        # ─── Meta Information ────────────────────────────────────────
        score = session_data.get("security_score", 0)
        score_color = _get_score_color(score)
        risk_level = session_data.get("risk_level", "info")
        risk_bg, risk_text = SEVERITY_COLORS.get(risk_level, SEVERITY_COLORS["info"])

        meta_data = [
            [
                Paragraph(f"<b>{strings['target']}</b>", styles["table_cell"]),
                Paragraph(
                    str(session_data.get("target_url", "N/A")), styles["table_cell"]
                ),
            ],
            [
                Paragraph(f"<b>{strings['generated']}</b>", styles["table_cell"]),
                Paragraph(
                    datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                    styles["table_cell"],
                ),
            ],
            [
                Paragraph(f"<b>{strings['score']}</b>", styles["table_cell"]),
                Paragraph(
                    f'<font color="{score_color.hexval()}">{score:.1f}/100</font>',
                    styles["table_cell"],
                ),
            ],
            [
                Paragraph(f"<b>{strings['risk']}</b>", styles["table_cell"]),
                Paragraph(
                    f'<font color="{risk_bg.hexval()}">{risk_level.upper()}</font>',
                    styles["table_cell"],
                ),
            ],
        ]

        meta_table = Table(
            meta_data, colWidths=[usable_width * 0.25, usable_width * 0.75]
        )
        meta_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), DARK_CARD),
                    ("BOX", (0, 0), (-1, -1), 0.5, GRAY_MUTED),
                    ("GRID", (0, 0), (-1, -1), 0.25, GRAY_MUTED),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        elements.append(meta_table)
        elements.append(Spacer(1, 18))

        # ═══════════════════════════════════════════════════════════════
        # VULNERABILITY FINDINGS TABLE
        # ═══════════════════════════════════════════════════════════════
        current_step = "vulnerability_table"

        # ─── Table text styles ───────────────────────────────────────────
        table_header_style = ParagraphStyle(
            name="TableHeader",
            fontName="DejaVuSans-Bold",
            fontSize=10,
            textColor=colors.HexColor("#58A6FF"),
            alignment=1,  # CENTER
            leading=14,
        )

        table_body_style = ParagraphStyle(
            name="TableBody",
            fontName="DejaVuSans",
            fontSize=9,
            textColor=colors.HexColor("#C9D1D9"),
            leading=12,
            wordWrap="CJK",
        )

        table_severity_style = ParagraphStyle(
            name="TableSeverity",
            fontName="DejaVuSans-Bold",
            fontSize=8,
            alignment=1,  # CENTER
            leading=12,
        )

        # ─── Severity badge helper using existing SEVERITY_COLORS ───────
        def make_severity_badge(severity: str) -> Paragraph:
            bg_color, text_color = SEVERITY_COLORS.get(
                severity.lower(),
                (colors.HexColor("#6B7280"), colors.HexColor("#FFFFFF")),
            )
            style = ParagraphStyle(
                name=f"Badge_{severity}",
                fontName="DejaVuSans-Bold",
                fontSize=8,
                textColor=text_color,
                backColor=bg_color,
                alignment=1,
                leading=12,
                borderPadding=(3, 6, 3, 6),
                borderRadius=3,
            )
            return Paragraph(severity.upper(), style)

        elements.append(Paragraph(strings["findings_title"], styles["heading"]))

        if not vulnerabilities:
            elements.append(Paragraph(strings["no_findings"], styles["normal"]))
        else:
            # ─── Build table data with Paragraphs ────────────────────────
            table_data = [
                [
                    Paragraph(strings["severity"], table_header_style),
                    Paragraph(strings["type"], table_header_style),
                    Paragraph(strings["title_col"], table_header_style),
                    Paragraph(strings["recommendation"], table_header_style),
                ]
            ]

            for vuln in vulnerabilities:
                table_data.append(
                    [
                        make_severity_badge(vuln.get("severity", "info")),
                        Paragraph(vuln.get("type", ""), table_body_style),
                        Paragraph(vuln.get("title", ""), table_body_style),
                        Paragraph(vuln.get("remediation", ""), table_body_style),
                    ]
                )

            # ─── Explicit column widths ─────────────────────────────────
            col_widths = [1.1 * inch, 1.1 * inch, 2.4 * inch, 2.4 * inch]

            # ─── TableStyle dark theme ───────────────────────────────────
            row_count = len(table_data)

            table_style_commands = [
                # Header row
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#161B22")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#58A6FF")),
                ("FONTNAME", (0, 0), (-1, 0), "DejaVuSans-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                # Borders
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#21262D")),
                ("BOX", (0, 0), (-1, -1), 1.0, colors.HexColor("#30363D")),
                # Padding
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]

            # Zebra striping for data rows
            for row_idx in range(1, row_count):
                bg = "#0D1117" if row_idx % 2 == 1 else "#11161D"
                table_style_commands.append(
                    ("BACKGROUND", (0, row_idx), (-1, row_idx), colors.HexColor(bg))
                )

            vuln_table = Table(table_data, colWidths=col_widths, repeatRows=1)
            vuln_table.setStyle(TableStyle(table_style_commands))
            elements.append(vuln_table)

        elements.append(Spacer(1, 20))

        # ═══════════════════════════════════════════════════════════════
        # DETAILED VULNERABILITY SECTIONS (CRITICAL & HIGH only)
        # ═══════════════════════════════════════════════════════════════
        current_step = "detail_sections"

        critical_high = [
            v for v in vulnerabilities if v.get("severity") in ("critical", "high")
        ]

        if critical_high:
            elements.append(Paragraph(strings["detail_title"], styles["heading"]))
            elements.append(Spacer(1, 6))

            for vuln in critical_high:
                elements.append(VulnerabilityDetail(vuln, strings, usable_width))
                elements.append(Spacer(1, 14))

        # ═══════════════════════════════════════════════════════════════
        # TOP REMEDIATION STEPS
        # ═══════════════════════════════════════════════════════════════
        current_step = "remediation_steps"

        elements.append(Paragraph(strings["remediation_title"], styles["heading"]))

        remediation = session_data.get("remediation_steps", [])
        if not remediation:
            remediation = REMEDIATION_STEPS.get(language, REMEDIATION_STEPS["en"])

        for i, step in enumerate(remediation, 1):
            elements.append(Paragraph(f"{i}. {step}", styles["remediation"]))

        elements.append(Spacer(1, 20))

        # ─── Build PDF ────────────────────────────────────────────────
        current_step = "pdf_build"

        # Remove trailing PageBreak or Spacer that causes empty last page
        if elements and isinstance(elements[-1], (PageBreak, Spacer)):
            elements.pop()
        # Remove any preceding Spacer before the last element if it's empty
        if elements and isinstance(elements[-1], Spacer):
            elements.pop()

        # Final build — use PageNumCanvas for two-pass "Page X of Y"
        final_buffer = BytesIO()
        final_doc = WebScanDoc(
            final_buffer,
            pagesize=A4,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
            leftMargin=15 * mm,
            rightMargin=15 * mm,
        )
        final_doc._strings = strings
        final_doc._target_url = session_data.get("target_url", "")
        final_doc._gen_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        final_doc.addPageTemplates([cover_template, content_template])

        final_doc.build(elements, canvasmaker=PageNumCanvas)

        pdf_bytes = final_buffer.getvalue()
        final_buffer.close()

        logger.info(
            f"PDF report generated: {len(vulnerabilities)} findings, "
            f"{len(pdf_bytes)} bytes"
        )
        return pdf_bytes

    except Exception as e:
        logger.error(
            f"PDF builder error at step '{current_step}': {type(e).__name__}: {e}",
            exc_info=True,
        )
        raise
