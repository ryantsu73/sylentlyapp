from typing import Dict, Any

import numpy as np


def run_pricing_engine(
    followers: int,
    estimated_subscribers: int,
    avg_views: float,
    engagement_rate: float,
    avg_cpm: float,
    current_price: float,
    risk_profile: str = "balanced",
) -> Dict[str, Any]:
    """
    Pricing engine v2:

    - Suggests a baseline subscription price from audience + CPM.
    - Suggests PPV low/high bounds.
    - Estimates ARPU, target penetration, implied revenue per fan.
    - Proposes a concrete A/B test:
        * recommended new price
        * duration
        * segment (e.g. new subs)
        * estimated uplift & risk level

    risk_profile: "conservative" | "balanced" | "aggressive"
    """
    followers = max(int(followers), 1)
    subs = max(int(estimated_subscribers or followers), 1)
    views = max(float(avg_views), 1.0)
    eng = max(float(engagement_rate), 0.1)
    cpm = max(float(avg_cpm), 0.5)
    current_price = max(float(current_price), 1.0)

    # Approx revenue-per-fan implied by CPM (very rough)
    monthly_impressions = views * 30  # 30 posts or story-equivalents / month
    implied_revenue_per_fan = (monthly_impressions / 1000.0 * cpm) / followers

    # Assume 15–35% of followers are/will be subs, linked to engagement
    target_sub_penetration = np.clip(eng / 10.0, 0.15, 0.35)
    if target_sub_penetration <= 0:
        target_sub_penetration = 0.2

    # Target ARPU from subs (scale CPM signal)
    target_arpu = implied_revenue_per_fan * 4  # convert soft ad-value to direct pay
    target_arpu = np.clip(target_arpu, 3.0, 30.0)

    # Suggested subscription price: ARPU / penetration
    suggested_sub_price = target_arpu / target_sub_penetration
    suggested_sub_price = float(np.clip(suggested_sub_price, 5.0, 50.0))
    suggested_sub_price = round(suggested_sub_price * 2) / 2.0  # .0 or .5

    # PPV pricing suggestions: fractions of sub price
    ppv_low = round(max(4.0, suggested_sub_price * 0.6), 2)
    ppv_high = round(max(ppv_low + 2.0, suggested_sub_price * 2.0), 2)

    # Basic uplift estimate vs current price
    uplift_ratio = suggested_sub_price / current_price if current_price else 1.0
    uplift_pct = round((uplift_ratio - 1.0) * 100.0, 2)

    # ----------------------------
    # Pricing test recommendation
    # ----------------------------
    risk_profile = (risk_profile or "balanced").lower()
    if risk_profile not in {"conservative", "balanced", "aggressive"}:
        risk_profile = "balanced"

    # How far is suggested from current, as %
    delta_pct = (suggested_sub_price - current_price) / current_price * 100.0

    # For OnlyFans, we typically lean into *price down* tests for new subs
    # when suggested < current, or modest price up tests when suggested > current.
    if delta_pct < -10:
        # Big price decrease → easier win, low risk, but we can be conservative
        test_price = round(current_price * 0.8 * 2) / 2.0
    elif -10 <= delta_pct <= 10:
        # Subtle difference → test suggested directly
        test_price = suggested_sub_price
    else:
        # Big price increase; scale back based on risk profile
        if risk_profile == "conservative":
            test_price = round(current_price * 1.15 * 2) / 2.0
        elif risk_profile == "aggressive":
            test_price = suggested_sub_price
        else:
            test_price = round(current_price * 1.25 * 2) / 2.0

    # Clamp test price to OF range
    test_price = float(np.clip(test_price, 3.0, 100.0))

    # Test duration based on risk profile
    if risk_profile == "conservative":
        duration_days = 21
        traffic_fraction = 0.3  # % of new signups seeing test
    elif risk_profile == "aggressive":
        duration_days = 10
        traffic_fraction = 0.8
    else:
        duration_days = 14
        traffic_fraction = 0.5

    # Heuristic expectations: price down → more conversion; price up → fewer subs but more ARPU.
    price_change_pct = (test_price - current_price) / current_price * 100.0
    if price_change_pct < 0:
        expected_conv_change = min(abs(price_change_pct) * 0.8, 40.0)  # e.g. -20% price → +16% conv
        expected_mrr_change = max(expected_conv_change * 0.6, 3.0)
        risk_level = "low"
    elif 0 <= price_change_pct <= 20:
        expected_conv_change = -price_change_pct * 0.5  # small drop in conv
        expected_mrr_change = max(price_change_pct * 0.4, 2.0)
        risk_level = "medium"
    else:
        expected_conv_change = -min(price_change_pct * 0.8, 50.0)
        expected_mrr_change = max(price_change_pct * 0.3, 5.0)
        risk_level = "high"

    test_recommendation = {
        "tier_name": "Main subscription tier",
        "current_price": round(current_price, 2),
        "test_price": round(test_price, 2),
        "segment": "New subscribers only",
        "traffic_fraction": int(traffic_fraction * 100.0),  # %
        "duration_days": duration_days,
        "expected_conversion_change_pct": round(expected_conv_change, 1),
        "expected_mrr_change_pct": round(expected_mrr_change, 1),
        "risk_level": risk_level,
        "fallback_rule": "Revert to current price if churn on existing subs rises >5%.",
    }

    return {
        # legacy keys (kept for compatibility)
        "suggested_sub_price": suggested_sub_price,
        "ppv_low": ppv_low,
        "ppv_high": ppv_high,
        "implied_revenue_per_fan": round(implied_revenue_per_fan, 2),
        "target_sub_penetration": round(target_sub_penetration * 100.0, 1),
        "target_arpu": round(target_arpu, 2),
        "uplift_pct_vs_current": uplift_pct,
        # new structured recommendation
        "pricing_test": test_recommendation,
    }
