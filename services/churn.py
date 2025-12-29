from typing import Dict, Any


def estimate_monthly_churn(active_subs: int, cancels_30d: int) -> Dict[str, Any]:
    """
    Basic churn estimate from manual inputs.
    churn_rate = cancels / active_subs
    """
    active_subs = max(int(active_subs), 1)
    cancels_30d = max(int(cancels_30d), 0)

    churn_rate = cancels_30d / active_subs
    return {
        "active_subs": active_subs,
        "cancels_30d": cancels_30d,
        "monthly_churn_rate_pct": round(churn_rate * 100.0, 2),
        "health_label": (
            "healthy" if churn_rate < 0.05 else
            "watch" if churn_rate < 0.10 else
            "risk"
        )
    }


def at_risk_heuristics(payment_fails: int, inactive_14d: int) -> Dict[str, Any]:
    """
    Lightweight heuristic scoring for churn risk signals (manual inputs).
    """
    payment_fails = max(int(payment_fails), 0)
    inactive_14d = max(int(inactive_14d), 0)

    risk_score = payment_fails * 2 + inactive_14d * 1
    band = "low" if risk_score < 5 else "medium" if risk_score < 15 else "high"

    return {
        "payment_fails": payment_fails,
        "inactive_14d": inactive_14d,
        "risk_score": risk_score,
        "risk_band": band,
        "recommended_actions": [
            "Send payment-fail reminder + quick-resub incentive" if payment_fails else None,
            "Send re-engagement DM with preview + limited-time offer" if inactive_14d else None,
            "Post a high-performing content type within 24–48h to re-activate lurkers",
        ],
    }
