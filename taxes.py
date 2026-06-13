"""
Federal and state tax calculations for self-employed / freelance income.
Includes self-employment tax, estimated quarterly payments, and deductions.
All bracket data targets the 2024 tax year (verify before filing).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from config import load_config, FILING_STATUSES
from db import Database

# ====================================================================
#  FEDERAL DATA (2024)
# ====================================================================

FEDERAL_BRACKETS: dict[str, list[tuple[float, float]]] = {
    "single": [
        (11_600, 0.10), (47_150, 0.12), (100_525, 0.22),
        (191_950, 0.24), (243_725, 0.32), (609_350, 0.35),
        (float("inf"), 0.37),
    ],
    "married_jointly": [
        (23_200, 0.10), (94_300, 0.12), (201_050, 0.22),
        (383_900, 0.24), (487_450, 0.32), (731_200, 0.35),
        (float("inf"), 0.37),
    ],
    "married_separately": [
        (11_600, 0.10), (47_150, 0.12), (100_525, 0.22),
        (191_950, 0.24), (243_725, 0.32), (365_600, 0.35),
        (float("inf"), 0.37),
    ],
    "head_of_household": [
        (16_550, 0.10), (63_100, 0.12), (100_500, 0.22),
        (191_950, 0.24), (243_700, 0.32), (609_350, 0.35),
        (float("inf"), 0.37),
    ],
}

STANDARD_DEDUCTION: dict[str, float] = {
    "single": 14_600,
    "married_jointly": 29_200,
    "married_separately": 14_600,
    "head_of_household": 21_900,
}

# Social-Security wage base 2024
SS_WAGE_BASE = 168_600
SS_RATE = 0.124
MEDICARE_RATE = 0.029
ADDITIONAL_MEDICARE_RATE = 0.009
ADDITIONAL_MEDICARE_THRESHOLD: dict[str, float] = {
    "single": 200_000, "married_jointly": 250_000,
    "married_separately": 125_000, "head_of_household": 200_000,
}

# SE tax is computed on 92.35 % of net earnings
SE_TAXABLE_FRACTION = 0.9235

# Quarterly estimated-tax due dates (month, day)
# Format: (quarter_number, period_label, due_month, due_day)
QUARTERLY_DATES = [
    (1, "01/01 – 03/31", 4, 15),   # Q1 → Apr 15
    (2, "04/01 – 05/31", 6, 15),   # Q2 → Jun 15
    (3, "06/01 – 08/31", 9, 15),   # Q3 → Sep 15
    (4, "09/01 – 12/31", 1, 15),   # Q4 → Jan 15 next year
]

# ====================================================================
#  STATE DATA (2024 estimates – single-filer; verify before filing)
# ====================================================================

_INF = float("inf")

# Format:
#   "XX": ("none",)
#   "XX": ("flat", rate)
#   "XX": ("graduated", [(upper, rate), ...])

STATE_TAX_DATA: dict[str, tuple] = {
    "AL": ("graduated", [(500, .02), (3_000, .04), (_INF, .05)]),
    "AK": ("none",),
    "AZ": ("flat", .025),
    "AR": ("graduated", [(4_300, .02), (8_500, .04), (_INF, .039)]),
    "CA": ("graduated", [
        (10_412, .01), (24_684, .02), (38_959, .04), (54_081, .06),
        (68_350, .08), (349_137, .093), (418_961, .103),
        (698_271, .113), (_INF, .133),
    ]),
    "CO": ("flat", .044),
    "CT": ("graduated", [
        (10_000, .03), (50_000, .05), (100_000, .055),
        (200_000, .06), (250_000, .065), (500_000, .069), (_INF, .0699),
    ]),
    "DE": ("graduated", [
        (2_000, .0), (5_000, .022), (10_000, .039),
        (20_000, .048), (25_000, .052), (60_000, .0555), (_INF, .066),
    ]),
    "DC": ("graduated", [
        (10_000, .04), (40_000, .06), (60_000, .065),
        (250_000, .085), (500_000, .0925), (1_000_000, .0975), (_INF, .1075),
    ]),
    "FL": ("none",),
    "GA": ("flat", .0549),
    "HI": ("graduated", [
        (2_400, .014), (4_800, .032), (9_600, .055),
        (14_400, .064), (19_200, .068), (24_000, .072),
        (36_000, .076), (48_000, .079), (150_000, .0825),
        (175_000, .09), (200_000, .10), (_INF, .11),
    ]),
    "ID": ("flat", .058),
    "IL": ("flat", .0495),
    "IN": ("flat", .0305),
    "IA": ("flat", .038),
    "KS": ("graduated", [(15_000, .031), (30_000, .0525), (_INF, .057)]),
    "KY": ("flat", .04),
    "LA": ("graduated", [(12_500, .0185), (50_000, .035), (_INF, .0425)]),
    "ME": ("graduated", [(24_500, .058), (58_050, .0675), (_INF, .0715)]),
    "MD": ("graduated", [
        (1_000, .02), (2_000, .03), (3_000, .04),
        (100_000, .0475), (125_000, .05), (150_000, .0525),
        (250_000, .055), (_INF, .0575),
    ]),
    "MA": ("flat", .05),
    "MI": ("flat", .0425),
    "MN": ("graduated", [
        (30_070, .0535), (98_760, .068), (183_340, .0785), (_INF, .0985),
    ]),
    "MS": ("flat", .047),
    "MO": ("graduated", [
        (1_207, .02), (2_414, .025), (3_621, .03),
        (4_828, .035), (6_035, .04), (7_242, .045),
        (8_449, .05), (9_656, .054), (_INF, .048),
    ]),
    "MT": ("flat", .059),
    "NE": ("graduated", [
        (3_700, .0246), (22_170, .0351), (35_730, .0501), (_INF, .0584),
    ]),
    "NV": ("none",),
    "NH": ("none",),
    "NJ": ("graduated", [
        (20_000, .014), (35_000, .0175), (40_000, .035),
        (75_000, .05525), (500_000, .0637), (1_000_000, .0897),
        (_INF, .1075),
    ]),
    "NM": ("graduated", [
        (5_500, .017), (11_000, .032), (16_000, .047),
        (210_000, .049), (_INF, .059),
    ]),
    "NY": ("graduated", [
        (8_500, .04), (11_700, .045), (13_900, .0525),
        (80_650, .055), (215_400, .06), (1_077_550, .0685),
        (5_000_000, .0965), (25_000_000, .103), (_INF, .109),
    ]),
    "NC": ("flat", .045),
    "ND": ("flat", .0195),
    "OH": ("graduated", [
        (26_050, .0), (100_000, .028), (_INF, .035),
    ]),
    "OK": ("graduated", [
        (1_000, .0025), (2_500, .0075), (3_750, .0175),
        (4_900, .0275), (7_200, .0375), (_INF, .0475),
    ]),
    "OR": ("graduated", [
        (4_050, .0475), (10_200, .0675), (125_000, .0875), (_INF, .099),
    ]),
    "PA": ("flat", .0307),
    "RI": ("graduated", [(73_450, .0375), (166_950, .0475), (_INF, .0599)]),
    "SC": ("graduated", [
        (3_200, .0), (6_410, .03), (9_620, .04),
        (12_820, .05), (16_040, .06), (_INF, .064),
    ]),
    "SD": ("none",),
    "TN": ("none",),
    "TX": ("none",),
    "UT": ("flat", .0465),
    "VT": ("graduated", [
        (45_400, .0335), (110_450, .066), (229_550, .076), (_INF, .0875),
    ]),
    "VA": ("graduated", [
        (3_000, .02), (5_000, .03), (17_000, .05), (_INF, .0575),
    ]),
    "WA": ("none",),
    "WV": ("graduated", [
        (10_000, .0236), (25_000, .0315), (40_000, .0354),
        (60_000, .0472), (_INF, .0512),
    ]),
    "WI": ("graduated", [
        (14_320, .035), (28_640, .044), (315_310, .053), (_INF, .0765),
    ]),
    "WY": ("none",),
}

# ====================================================================
#  CALCULATION FUNCTIONS
# ====================================================================


def _apply_brackets(taxable: float, brackets: list[tuple[float, float]]) -> float:
    """Compute tax using marginal brackets: [(upper_limit, rate), …]."""
    tax = 0.0
    prev = 0.0
    for upper, rate in brackets:
        if taxable <= 0:
            break
        span = min(taxable, upper - prev)
        tax += span * rate
        taxable -= span
        prev = upper
    return round(tax, 2)


def compute_self_employment_tax(
    net_earnings: float, filing_status: str = "single"
) -> dict:
    """Return a dict with SE tax components."""
    se_income = net_earnings * SE_TAXABLE_FRACTION
    if se_income <= 0:
        return {"ss_tax": 0, "medicare_tax": 0, "additional_medicare": 0,
                "total_se_tax": 0, "se_deduction": 0, "se_income": 0}

    ss_tax = min(se_income, SS_WAGE_BASE) * SS_RATE
    medicare_tax = se_income * MEDICARE_RATE
    threshold = ADDITIONAL_MEDICARE_THRESHOLD.get(filing_status, 200_000)
    additional = max(0, se_income - threshold) * ADDITIONAL_MEDICARE_RATE

    total = ss_tax + medicare_tax + additional
    return {
        "ss_tax": round(ss_tax, 2),
        "medicare_tax": round(medicare_tax, 2),
        "additional_medicare": round(additional, 2),
        "total_se_tax": round(total, 2),
        "se_deduction": round(total / 2, 2),
        "se_income": round(se_income, 2),
    }


def compute_federal_tax(taxable_income: float, filing_status: str) -> float:
    brackets = FEDERAL_BRACKETS.get(filing_status, FEDERAL_BRACKETS["single"])
    return _apply_brackets(max(taxable_income, 0), brackets)


def compute_state_tax(taxable_income: float, state: str) -> float:
    info = STATE_TAX_DATA.get(state)
    if info is None or info[0] == "none":
        return 0.0
    if info[0] == "flat":
        return round(max(taxable_income, 0) * info[1], 2)
    # graduated
    return _apply_brackets(max(taxable_income, 0), info[1])


def compute_full_tax(
    gross_income: float,
    filing_status: str = "single",
    state: str = "CA",
    deductions_cfg: Optional[dict] = None,
    tax_year: Optional[int] = None,
) -> dict:
    """
    Run the full tax pipeline and return a comprehensive breakdown.
    
    Args:
        gross_income: Total freelance/self-employed income
        filing_status: One of "single", "married_jointly", etc.
        state: Two-letter state code
        deductions_cfg: Dictionary of above-line deductions
        tax_year: The tax year for which estimates are being computed.
                  If None, uses the current year for quarterly due dates.
    """
    cfg = deductions_cfg or {}

    # --- Self-employment tax first (needed for the deduction) -----------
    se = compute_self_employment_tax(gross_income, filing_status)

    # --- Deductions -----------------------------------------------------
    if cfg.get("use_standard", True):
        base_deduction = STANDARD_DEDUCTION.get(filing_status, 14_600)
    else:
        base_deduction = cfg.get("custom_deduction", 0.0)

    business = cfg.get("business_expenses", 0.0)
    health = cfg.get("health_insurance", 0.0)
    retirement = cfg.get("retirement_contributions", 0.0)
    home_office = cfg.get("home_office", 0.0)
    other = cfg.get("other_deductions", 0.0)
    above_line = se["se_deduction"] + health + retirement

    agi = gross_income - above_line - business - home_office - other
    taxable_income = max(agi - base_deduction, 0)

    federal = compute_federal_tax(taxable_income, filing_status)
    state_tax = compute_state_tax(taxable_income, state)

    total_tax = federal + state_tax + se["total_se_tax"]
    effective_rate = (total_tax / gross_income * 100) if gross_income > 0 else 0

    # --- Quarterly estimates (use tax_year if provided, else today's year) ---
    quarterly_amount = round(total_tax / 4, 2)
    
    # Determine which year to use for quarterly due dates
    if tax_year is not None:
        ref_year = tax_year
    else:
        ref_year = date.today().year
    
    today = date.today()
    quarterly_schedule = []
    
    for q_num, period_label, due_m, due_d in QUARTERLY_DATES:
        # Q4 of current tax_year is due in January of next year
        due_year = ref_year if q_num < 4 else ref_year + 1
        due_date = date(due_year, due_m, due_d)
        
        # Status is based on today's date, not the tax year
        status = "Paid / Past" if today > due_date else (
            "Due Soon" if (due_date - today).days <= 30 else "Upcoming"
        )
        
        quarterly_schedule.append({
            "quarter": f"Q{q_num}",
            "period": period_label,
            "due_date": due_date.strftime("%B %d, %Y"),
            "amount": quarterly_amount,
            "status": status,
        })

    return {
        "gross_income": round(gross_income, 2),
        "agi": round(agi, 2),
        "total_deductions_above": round(above_line + business + home_office + other, 2),
        "standard_or_itemized": round(base_deduction, 2),
        "taxable_income": round(taxable_income, 2),
        "federal_tax": round(federal, 2),
        "state_tax": round(state_tax, 2),
        "se_tax": se,
        "total_tax": round(total_tax, 2),
        "effective_rate": round(effective_rate, 2),
        "quarterly_schedule": quarterly_schedule,
        "quarterly_amount": quarterly_amount,
        "filing_status": FILING_STATUSES.get(filing_status, filing_status),
        "state": state,
    }


def estimate_taxes_from_data(db: Database, config: Optional[dict] = None) -> dict:
    """Convenience: pull income from the DB and compute taxes."""
    cfg = config or load_config()
    tax_cfg = cfg.get("tax", {})
    year = tax_cfg.get("tax_year", date.today().year)
    entries = db.get_entries_for_year(year)
    gross = sum(e.get("total", 0) for e in entries)
    return compute_full_tax(
        gross_income=gross,
        filing_status=tax_cfg.get("filing_status", "single"),
        state=tax_cfg.get("state", "CA"),
        deductions_cfg=tax_cfg.get("deductions", {}),
        tax_year=year,
    )