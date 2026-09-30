"""Deterministic Risk Scoring Model.

Provides centralized, documented, and deterministic risk calculation rules
for invoices and scenario simulations.

Core Invariant:
Risk scores are calculated via explicit mathematical weights and business rules.
No probabilistic LLMs are involved in scoring.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from decimal import Decimal

from backend.domain.controls.metadata import (
    CONTROL_METADATA_REGISTRY,
    format_expected_value,
    format_actual_value,
    format_variance_str,
)


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskCategory(str, Enum):
    VENDOR_RISK = "VENDOR_RISK"
    PURCHASE_ORDER_RISK = "PURCHASE_ORDER_RISK"
    RECEIPT_RISK = "RECEIPT_RISK"
    FINANCIAL_RISK = "FINANCIAL_RISK"
    DUPLICATE_RISK = "DUPLICATE_RISK"
    APPROVAL_RISK = "APPROVAL_RISK"
    PAYMENT_RISK = "PAYMENT_RISK"


@dataclass
class RiskFactor:
    code: str
    title: str
    severity: str
    category: str
    description: str
    evidence: str
    source: str  # "CONTROL" | "EXCEPTION" | "RISK_SIGNAL"
    why_it_matters: str
    recommended_action: str
    score_contribution: int


class RiskScoringModel:
    """Explicit, documented scoring model for Accounts Payable risk intelligence."""

    # Weights by control failure severity
    SEVERITY_WEIGHTS: Dict[str, int] = {
        "CRITICAL": 35,
        "HIGH": 25,
        "MEDIUM": 15,
        "LOW": 10,
    }

    WARNING_WEIGHT: int = 5
    OPEN_EXCEPTION_WEIGHT: int = 20
    DUPLICATE_MATCH_WEIGHT: int = 30
    VENDOR_MISMATCH_WEIGHT: int = 25
    ACTIVE_RISK_SIGNAL_WEIGHT: int = 15

    # Thresholds for risk levels
    LOW_THRESHOLD: int = 20
    MEDIUM_THRESHOLD: int = 50
    HIGH_THRESHOLD: int = 80

    # Category mapping from control category / code
    CONTROL_CATEGORY_MAP: Dict[str, str] = {
        "VENDOR": RiskCategory.VENDOR_RISK.value,
        "PO": RiskCategory.PURCHASE_ORDER_RISK.value,
        "RECEIPT": RiskCategory.RECEIPT_RISK.value,
        "FINANCIAL": RiskCategory.FINANCIAL_RISK.value,
        "DUPLICATE": RiskCategory.DUPLICATE_RISK.value,
        "RISK": RiskCategory.APPROVAL_RISK.value,
    }

    SPECIAL_CODE_MAP: Dict[str, str] = {
        "BANK_DETAILS_MATCH": RiskCategory.PAYMENT_RISK.value,
        "BANK_DETAILS_MISMATCH": RiskCategory.PAYMENT_RISK.value,
        "DUPLICATE_EXACT": RiskCategory.DUPLICATE_RISK.value,
        "DUPLICATE_SEMANTIC": RiskCategory.DUPLICATE_RISK.value,
        "DUPLICATE_INVOICE": RiskCategory.DUPLICATE_RISK.value,
        "THRESHOLD_PROXIMITY": RiskCategory.APPROVAL_RISK.value,
        "UNUSUAL_AMOUNT": RiskCategory.FINANCIAL_RISK.value,
    }

    def get_risk_category(self, control_or_exc_code: str, fallback_category: Optional[str] = None) -> str:
        """Map a control code or exception code to a finance risk category."""
        if control_or_exc_code in self.SPECIAL_CODE_MAP:
            return self.SPECIAL_CODE_MAP[control_or_exc_code]
        if fallback_category and fallback_category in self.CONTROL_CATEGORY_MAP:
            return self.CONTROL_CATEGORY_MAP[fallback_category]
        return RiskCategory.FINANCIAL_RISK.value

    def score_to_level(self, score: int) -> RiskLevel:
        """Map a normalized 0-100 score to a qualitative RiskLevel."""
        if score < self.LOW_THRESHOLD:
            return RiskLevel.LOW
        if score < self.MEDIUM_THRESHOLD:
            return RiskLevel.MEDIUM
        if score < self.HIGH_THRESHOLD:
            return RiskLevel.HIGH
        return RiskLevel.CRITICAL

    def build_control_factor(
        self,
        control_code: str,
        category: str,
        status: str,
        severity: str,
        message: Optional[str] = None,
        expected_value: Any = None,
        actual_value: Any = None,
        variance_value: Any = None,
    ) -> RiskFactor:
        """Construct a standardized RiskFactor from an evaluated control."""
        meta = CONTROL_METADATA_REGISTRY.get(control_code)
        title = meta.title if meta else control_code.replace("_", " ").title()
        risk_cat = self.get_risk_category(control_code, category)

        # Determine weight
        sev_upper = (severity or "MEDIUM").upper()
        if status == "FAIL":
            contribution = self.SEVERITY_WEIGHTS.get(sev_upper, 15)
            if control_code in ("DUPLICATE_EXACT", "DUPLICATE_SEMANTIC"):
                contribution = max(contribution, self.DUPLICATE_MATCH_WEIGHT)
            elif control_code in ("BANK_DETAILS_MATCH", "PO_VENDOR_MATCH"):
                contribution = max(contribution, self.VENDOR_MISMATCH_WEIGHT)
        elif status == "WARNING":
            contribution = self.WARNING_WEIGHT
        else:
            contribution = 0

        # Build evidence text
        exp_str = format_expected_value(control_code, expected_value)
        act_str = format_actual_value(control_code, actual_value)
        var_dec = Decimal(str(variance_value)) if variance_value is not None else None
        var_str = format_variance_str(var_dec, None, control_code) if var_dec is not None else ""
        if var_str == "None":
            var_str = ""

        if var_str:
            evidence = f"Expected: {exp_str}, Actual: {act_str} ({var_str})"
        elif exp_str and act_str:
            evidence = f"Expected: {exp_str}, Actual: {act_str}"
        elif message:
            evidence = message
        else:
            evidence = f"Control check failed with status {status}"

        description = message or (meta.failed_message if meta and status == "FAIL" else f"Control check {title}")
        why = meta.why_it_matters if meta else "Control check variance poses operational and compliance risks."
        action = meta.recommended_action if meta else "Review the variance and take appropriate corrective action."

        return RiskFactor(
            code=control_code,
            title=title,
            severity=sev_upper if status == "FAIL" else ("LOW" if status == "WARNING" else "INFO"),
            category=risk_cat,
            description=description,
            evidence=evidence,
            source="CONTROL",
            why_it_matters=why,
            recommended_action=action,
            score_contribution=contribution,
        )

    def calculate_profile(
        self,
        control_results: List[Any],
        exceptions: List[Any],
        risk_signals: List[Any],
    ) -> Dict[str, Any]:
        """Compute complete deterministic risk profile from results, exceptions, and signals."""
        raw_score = 0
        risk_factors: List[RiskFactor] = []
        seen_factor_codes = set()

        passed_count = 0
        failed_count = 0
        warning_count = 0
        na_count = 0

        # 1. Evaluate Control Results
        for cr in control_results:
            status = getattr(cr, "status", None)
            if hasattr(status, "value"):
                status = status.value
            status = str(status).upper()

            code = getattr(cr, "control_code", "")
            category = getattr(cr, "category", getattr(cr, "control_category", "FINANCIAL"))
            severity = getattr(cr, "severity", "MEDIUM")
            if hasattr(severity, "value"):
                severity = severity.value
            severity = str(severity).upper()

            msg = getattr(cr, "message", None)
            exp = getattr(cr, "expected_value", None)
            act = getattr(cr, "actual_value", None)
            var = getattr(cr, "variance_value", None)

            if status in ("PASS", "PASSED"):
                passed_count += 1
            elif status in ("FAIL", "FAILED", "ERROR"):
                failed_count += 1
                factor = self.build_control_factor(code, category, "FAIL", severity, msg, exp, act, var)
                raw_score += factor.score_contribution
                if code not in seen_factor_codes:
                    risk_factors.append(factor)
                    seen_factor_codes.add(code)
            elif status in ("WARNING", "WARN"):
                warning_count += 1
                factor = self.build_control_factor(code, category, status, severity, msg, exp, act, var)
                raw_score += factor.score_contribution
                if code not in seen_factor_codes:
                    risk_factors.append(factor)
                    seen_factor_codes.add(code)
            elif status in ("NOT_APPLICABLE", "SKIPPED"):
                na_count += 1

        # 2. Evaluate Open Exceptions (if any)
        for exc in exceptions:
            exc_status = getattr(exc, "status", "OPEN")
            if hasattr(exc_status, "value"):
                exc_status = exc_status.value
            exc_status = str(exc_status).upper()

            if exc_status in ("OPEN", "IN_REVIEW"):
                exc_code = getattr(exc, "exception_code", "EXCEPTION")
                exc_sev = getattr(exc, "severity", "HIGH")
                if hasattr(exc_sev, "value"):
                    exc_sev = exc_sev.value
                exc_title = getattr(exc, "title", exc_code)
                exc_desc = getattr(exc, "description", "")

                # If this code wasn't already covered by a failed control
                if exc_code not in seen_factor_codes:
                    factor = RiskFactor(
                        code=exc_code,
                        title=exc_title,
                        severity=str(exc_sev).upper(),
                        category=self.get_risk_category(exc_code),
                        description=exc_desc or f"Open exception requiring manual resolution: {exc_title}",
                        evidence=f"Active exception recorded: {exc_code}",
                        source="EXCEPTION",
                        why_it_matters="Unresolved exceptions block statutory compliance and payable generation.",
                        recommended_action="Resolve or waive the exception with documented business justification.",
                        score_contribution=self.OPEN_EXCEPTION_WEIGHT,
                    )
                    raw_score += self.OPEN_EXCEPTION_WEIGHT
                    risk_factors.append(factor)
                    seen_factor_codes.add(exc_code)
                else:
                    # Boost score slightly for having a formal open exception recorded
                    raw_score += 10

        # 3. Evaluate Active Risk Signals (if any)
        for sig in risk_signals:
            sig_status = getattr(sig, "status", "ACTIVE")
            if hasattr(sig_status, "value"):
                sig_status = sig_status.value
            sig_status = str(sig_status).upper()

            if sig_status == "ACTIVE":
                sig_code = getattr(sig, "signal_code", "RISK_SIGNAL")
                sig_sev = getattr(sig, "severity", "MEDIUM")
                if hasattr(sig_sev, "value"):
                    sig_sev = sig_sev.value
                sig_desc = getattr(sig, "description", "")
                sig_evidence = getattr(sig, "evidence", {})

                if sig_code not in seen_factor_codes:
                    ev_str = str(sig_evidence) if sig_evidence else "Active behavioral risk signal detected"
                    factor = RiskFactor(
                        code=sig_code,
                        title=sig_code.replace("_", " ").title(),
                        severity=str(sig_sev).upper(),
                        category=self.get_risk_category(sig_code),
                        description=sig_desc or f"Risk signal: {sig_code}",
                        evidence=ev_str,
                        source="RISK_SIGNAL",
                        why_it_matters="Statistical or velocity patterns indicate heightened exposure to policy bypass.",
                        recommended_action="Inspect audit history and cross-verify with authorized approvers.",
                        score_contribution=self.ACTIVE_RISK_SIGNAL_WEIGHT,
                    )
                    raw_score += self.ACTIVE_RISK_SIGNAL_WEIGHT
                    risk_factors.append(factor)
                    seen_factor_codes.add(sig_code)

        # Normalize score between 0 and 100
        normalized_score = min(max(raw_score, 0), 100)
        risk_level = self.score_to_level(normalized_score)

        recommended_attention = (
            normalized_score >= self.MEDIUM_THRESHOLD
            or risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
            or failed_count > 0
            or len(exceptions) > 0
        )

        return {
            "risk_score": normalized_score,
            "risk_level": risk_level.value,
            "risk_factors": risk_factors,
            "control_summary": {
                "passed": passed_count,
                "failed": failed_count,
                "warnings": warning_count,
                "not_applicable": na_count,
            },
            "recommended_attention": recommended_attention,
        }


default_scoring_model = RiskScoringModel()
