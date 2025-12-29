from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional


@dataclass
class PricingExperiment:
    name: str
    control_price: float
    test_price: float
    control_new_subs: int
    test_new_subs: int
    days_running: int
    control_seen: Optional[int] = None   # optional: number of visitors/new-subs exposed
    test_seen: Optional[int] = None


def summarize_pricing_experiment(exp: PricingExperiment) -> Dict[str, Any]:
    """
    Heuristic summary for an A/B price test when we only have new subs counts.
    If seen/exposed counts are provided, we compute conversion rates too.
    """
    c_subs = max(int(exp.control_new_subs), 0)
    t_subs = max(int(exp.test_new_subs), 0)

    # If exposures known, compute conversion rates; else treat new subs as outcome proxy.
    if exp.control_seen and exp.test_seen and exp.control_seen > 0 and exp.test_seen > 0:
        c_rate = c_subs / exp.control_seen
        t_rate = t_subs / exp.test_seen
        uplift = (t_rate / c_rate - 1.0) * 100.0 if c_rate > 0 else None
        metric_type = "conversion_rate"
    else:
        c_rate = None
        t_rate = None
        uplift = (t_subs / c_subs - 1.0) * 100.0 if c_subs > 0 else None
        metric_type = "new_subs_proxy"

    # Revenue proxy from subscriptions only (no churn modeling here)
    control_rev = c_subs * float(exp.control_price)
    test_rev = t_subs * float(exp.test_price)
    rev_uplift = (test_rev / control_rev - 1.0) * 100.0 if control_rev > 0 else None

    winner = "test" if (rev_uplift is not None and rev_uplift > 0) else "control"

    return {
        "experiment": asdict(exp),
        "metric_type": metric_type,
        "control_conversion_rate": c_rate,
        "test_conversion_rate": t_rate,
        "uplift_pct": round(uplift, 2) if uplift is not None else None,
        "control_revenue_proxy": round(control_rev, 2),
        "test_revenue_proxy": round(test_rev, 2),
        "revenue_uplift_pct": round(rev_uplift, 2) if rev_uplift is not None else None,
        "winner": winner,
        "notes": (
            "This is a simplified A/B evaluator. For real pricing optimization you’d want "
            "exposures (visitors/new-signups), churn impact, and longer time windows."
        ),
    }
