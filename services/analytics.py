from typing import Tuple

import numpy as np
import pandas as pd


def generate_synthetic_cohort(
    followers: int,
    avg_views: float,
    engagement_rate: float,
    avg_cpm: float,
    n: int = 1000,
) -> pd.DataFrame:
    """
    Generate a synthetic cohort of similar creators to benchmark against.
    Very simple probabilistic model around the given stats.
    """

    followers = max(followers, 1)
    base_log = np.log(followers)

    # Followers: log-normal spread around the creator's follower count
    followers_dist = np.random.lognormal(mean=base_log, sigma=0.4, size=n).astype(int)

    # Views: normally 20–50% of followers, centered around creator's ratio
    creator_view_ratio = avg_views / followers if followers > 0 else 0.3
    creator_view_ratio = np.clip(creator_view_ratio, 0.05, 0.8)
    view_ratios = np.random.normal(loc=creator_view_ratio, scale=0.05, size=n)
    view_ratios = np.clip(view_ratios, 0.02, 0.9)
    views_dist = (followers_dist * view_ratios).astype(int)

    # Engagement rate: normal around creator's ER ± 1.5pp
    er_mean = np.clip(engagement_rate, 0.1, 50.0)
    er_dist = np.random.normal(loc=er_mean, scale=1.5, size=n)
    er_dist = np.clip(er_dist, 0.1, 80.0)

    # CPM: log-normal around creator's CPM
    cpm_base = max(avg_cpm, 0.5)
    log_cpm_mean = np.log(cpm_base)
    cpm_dist = np.random.lognormal(mean=log_cpm_mean, sigma=0.35, size=n)

    df = pd.DataFrame(
        {
            "followers": followers_dist,
            "avg_views": views_dist,
            "engagement_rate": er_dist,
            "avg_cpm": cpm_dist,
        }
    )

    return df


def percentile_rank(series: pd.Series, value: float) -> float:
    """Return the percentile rank of `value` within `series`."""
    if len(series) == 0:
        return 0.0
    return round(100.0 * (series < value).mean(), 2)


def estimate_earnings(
    monthly_posts: int,
    avg_views_per_post: float,
    cpm: float,
) -> Tuple[int, float]:
    """
    Simple back-of-the-envelope earnings estimate:
      total_impressions = posts * avg_views_per_post
      earnings = (impressions / 1000) * cpm
    """
    monthly_posts = max(int(monthly_posts), 1)
    avg_views_per_post = max(float(avg_views_per_post), 1.0)
    cpm = max(float(cpm), 0.5)

    total_impressions = int(monthly_posts * avg_views_per_post)
    earnings = (total_impressions / 1000.0) * cpm

    return total_impressions, earnings
