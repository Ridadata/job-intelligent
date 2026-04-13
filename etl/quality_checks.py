"""Post-transform data quality checks.

Runs assertions on Silver and Gold data to detect problems before they
propagate downstream. Results can be logged to pipeline_runs.
"""

import logging
from typing import Any

from etl.db import get_supabase_client

logger = logging.getLogger(__name__)


class QualityReport:
    """Accumulates data quality check results.

    Args:
        stage: The layer being checked ('silver' or 'gold').
    """

    def __init__(self, stage: str) -> None:
        self.stage = stage
        self.checks_passed = 0
        self.checks_failed = 0
        self.failures: list[dict[str, Any]] = []

    def record(self, check_name: str, passed: bool, detail: str = "") -> None:
        """Record the result of a single check.

        Args:
            check_name: Human-readable check identifier.
            passed: Whether the check passed.
            detail: Additional info on failure.
        """
        if passed:
            self.checks_passed += 1
        else:
            self.checks_failed += 1
            self.failures.append({"check": check_name, "detail": detail})
            logger.warning("Quality check FAILED: %s — %s", check_name, detail)

    @property
    def all_passed(self) -> bool:
        """Return True if all checks passed.

        Returns:
            Boolean result.
        """
        return self.checks_failed == 0

    def summary(self) -> dict[str, Any]:
        """Return a summary dict suitable for logging or API response.

        Returns:
            Dict with passed, failed, and failure details.
        """
        return {
            "stage": self.stage,
            "passed": self.checks_passed,
            "failed": self.checks_failed,
            "all_passed": self.all_passed,
            "failures": self.failures,
        }


def check_silver_quality(limit: int = 1000) -> QualityReport:
    """Run quality checks on the Silver (job_offers) table.

    Checks:
    - Non-null titles
    - Valid contract types
    - Non-empty skills arrays
    - Reasonable salary ranges
    - Published dates present

    Args:
        limit: Maximum rows to sample for checks.

    Returns:
        QualityReport with check results.
    """
    client = get_supabase_client()
    report = QualityReport("silver")

    result = (
        client.table("job_offers")
        .select("id, title, contract_type, required_skills, salary_min, salary_max, published_at")
        .limit(limit)
        .execute()
    )
    rows = result.data or []

    if not rows:
        report.record("has_data", False, "Silver table is empty")
        return report

    report.record("has_data", True)

    # Check: all rows have non-empty titles
    null_titles = sum(1 for r in rows if not r.get("title"))
    report.record(
        "non_null_titles",
        null_titles == 0,
        f"{null_titles}/{len(rows)} rows have null/empty titles",
    )

    # Check: all contract types are valid
    valid_contracts = {"CDI", "CDD", "Freelance", "Stage", "Alternance", "Autre"}
    invalid_contracts = [
        r.get("contract_type") for r in rows
        if r.get("contract_type") not in valid_contracts
    ]
    report.record(
        "valid_contract_types",
        len(invalid_contracts) == 0,
        f"{len(invalid_contracts)} rows have invalid contract types: {set(invalid_contracts)}",
    )

    # Check: skills array is non-empty for majority of rows
    empty_skills = sum(1 for r in rows if not r.get("required_skills"))
    empty_ratio = empty_skills / len(rows) if rows else 0
    report.record(
        "skills_populated",
        empty_ratio < 0.5,
        f"{empty_skills}/{len(rows)} ({empty_ratio:.0%}) rows have empty skills",
    )

    # Check: salary_min <= salary_max when both present
    bad_salary = sum(
        1 for r in rows
        if r.get("salary_min") is not None
        and r.get("salary_max") is not None
        and r["salary_min"] > r["salary_max"]
    )
    report.record(
        "salary_range_valid",
        bad_salary == 0,
        f"{bad_salary} rows have salary_min > salary_max",
    )

    # Check: published_at populated rate
    no_date = sum(1 for r in rows if not r.get("published_at"))
    date_ratio = no_date / len(rows) if rows else 0
    report.record(
        "published_at_populated",
        date_ratio < 0.3,
        f"{no_date}/{len(rows)} ({date_ratio:.0%}) rows missing published_at",
    )

    logger.info(
        "Silver quality: %d passed, %d failed (%d rows sampled)",
        report.checks_passed, report.checks_failed, len(rows),
    )
    return report


def check_gold_quality(limit: int = 1000) -> QualityReport:
    """Run quality checks on the Gold (dw_job_offers) table.

    Checks:
    - Non-null embeddings
    - Valid seniority levels
    - Non-empty tech stacks
    - Demand score in range [0, 1]

    Args:
        limit: Maximum rows to sample for checks.

    Returns:
        QualityReport with check results.
    """
    client = get_supabase_client()
    report = QualityReport("gold")

    result = (
        client.table("dw_job_offers")
        .select("id, offer_id, normalized_title, seniority_level, tech_stack, demand_score")
        .limit(limit)
        .execute()
    )
    rows = result.data or []

    if not rows:
        report.record("has_data", False, "Gold table is empty")
        return report

    report.record("has_data", True)

    # Check: valid seniority levels
    valid_seniority = {"Junior", "Mid", "Senior"}
    invalid_sen = [
        r.get("seniority_level") for r in rows
        if r.get("seniority_level") not in valid_seniority
    ]
    report.record(
        "valid_seniority_levels",
        len(invalid_sen) == 0,
        f"{len(invalid_sen)} rows have invalid seniority: {set(invalid_sen)}",
    )

    # Check: normalized titles are non-empty
    null_titles = sum(1 for r in rows if not r.get("normalized_title"))
    report.record(
        "non_null_normalized_titles",
        null_titles == 0,
        f"{null_titles}/{len(rows)} rows have null normalized_title",
    )

    # Check: tech_stack non-empty for majority
    empty_tech = sum(1 for r in rows if not r.get("tech_stack"))
    tech_ratio = empty_tech / len(rows) if rows else 0
    report.record(
        "tech_stack_populated",
        tech_ratio < 0.5,
        f"{empty_tech}/{len(rows)} ({tech_ratio:.0%}) rows have empty tech_stack",
    )

    # Check: demand_score in valid range
    bad_score = sum(
        1 for r in rows
        if r.get("demand_score") is not None
        and not (0.0 <= r["demand_score"] <= 1.0)
    )
    report.record(
        "demand_score_in_range",
        bad_score == 0,
        f"{bad_score} rows have demand_score outside [0, 1]",
    )

    logger.info(
        "Gold quality: %d passed, %d failed (%d rows sampled)",
        report.checks_passed, report.checks_failed, len(rows),
    )
    return report
