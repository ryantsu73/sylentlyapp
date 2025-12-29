from typing import Dict, Any, Optional

import streamlit as st


def render_profile_header(profile: Dict[str, Any]) -> None:
    """
    Renders the top profile header: image, name, handle, basic stats.
    """
    header_cols = st.columns([1, 3])
    with header_cols[0]:
        if profile.get("profile_image_url"):
            st.image(profile["profile_image_url"], width=140)
    with header_cols[1]:
        display_name = profile.get("profile_name") or profile.get("handle") or "Creator"
        st.markdown(f"### {display_name}")
        st.markdown(f"*Platform:* **{profile.get('platform', 'Unknown')}**")
        handle_display = profile.get("handle") or "unknown"
        st.markdown(f"*Handle:* `@{handle_display}`")

        extra_bits = []
        if profile.get("followers") is not None:
            extra_bits.append(f"**{profile['followers']:,}** fans")
        if profile.get("likes") is not None:
            extra_bits.append(f"**{profile['likes']:,}** likes")
        if profile.get("posts_count") is not None:
            extra_bits.append(f"**{profile['posts_count']:,}** posts")
        if profile.get("photos_count") is not None:
            extra_bits.append(f"**{profile['photos_count']:,}** photos")
        if profile.get("videos_count") is not None:
            extra_bits.append(f"**{profile['videos_count']:,}** videos")

        if extra_bits:
            st.markdown(" • ".join(extra_bits))


def render_baseline_card(
    followers: int,
    est_subs: int,
    current_price: float,
    est_monthly_visits: Optional[int],
) -> None:
    """
    Simple baseline revenue card inspired by your Screen 2.
    """
    mrr_estimate = est_subs * current_price
    avg_tier_price = current_price  # Single-tier approximation

    st.markdown("#### Baseline – Here's your money today (estimate)")
    with st.container(border=True):
        st.write("**YOUR CURRENT MONTHLY REVENUE (ESTIMATED)**")
        st.write(f"**${mrr_estimate:,.0f}**")
        st.write("")
        st.write(f"- Active subscribers (est): **{est_subs:,.0f}**")
        st.write(f"- Avg. tier price (approx): **${avg_tier_price:,.2f}**")
        if est_monthly_visits is not None:
            st.write(f"- Estimated monthly visits: **{est_monthly_visits:,.0f}**")
        st.caption(
            "These are estimates based on your public metrics and the subscription price "
            "you entered in the sidebar."
        )


def render_pricing_test_card(test: Dict[str, Any]) -> None:
    """
    Visual card for the pricing test recommendation.
    Mirrors the feel of Screen 3's 'Tier Pricing Test' card.
    """
    with st.container(border=True):
        st.write("📊 **TIER PRICING TEST**")
        st.write("Status: **Recommended** · Target: **New subscribers**")
        st.write("---")

        st.write(f"**Current price:** ${test['current_price']:.2f}")
        st.write(f"**Suggested test price:** ${test['test_price']:.2f}")

        # Directional explanation
        price_change_pct = (
            (test["test_price"] - test["current_price"]) / test["current_price"] * 100.0
        )
        direction = "lower" if price_change_pct < 0 else "higher"
        st.write(
            f"Why: Testing a {abs(price_change_pct):.1f}% {direction} price "
            "on a subset of new signups to find your sweet spot."
        )
        st.write("")
        st.write(
            f"Estimated conversion change: **{test['expected_conversion_change_pct']:+.1f}%**"
        )
        st.write(
            f"Estimated MRR impact (new subs): **{test['expected_mrr_change_pct']:+.1f}%**"
        )
        st.write("")

        st.write(f"Duration: **{test['duration_days']} days**")
        st.write(f"Traffic split: **{test['traffic_fraction']}%** of new subs see test.")
        st.write(f"Risk level: **{test['risk_level'].upper()}**")
        st.write(f"Fallback: {test['fallback_rule']}")
        st.write("")
        st.button("Approve test (conceptual)", key="approve_test_button", help="In a full Silent Partner build, this would spin up a real A/B test in the background.")


def render_dm_suggestions(dm_suggestions) -> None:
    st.markdown("Use these as **DM templates / playbooks**. Plug them into your own DM sender.")
    for i, s in enumerate(dm_suggestions, start=1):
        st.markdown(f"#### #{i} – {s['segment']}")
        st.markdown(f"**Goal:** {s['goal']}")
        st.markdown(f"**Message idea:** {s['message']}")
        st.markdown(f"**CTA:** {s['cta']}")
        st.markdown(f"**Timing:** {s['timing']}")
        st.markdown("---")


def render_whale_ideas(whale_ideas) -> None:
    st.markdown("Ideas focused on **high-value 'whale' fans**.")
    for idea in whale_ideas:
        st.markdown(f"#### {idea['name']}")
        st.markdown(f"**Who:** {idea['who']}")
        st.markdown(f"**Offer:** {idea['offer']}")
        st.markdown(f"**Pricing guidance:** {idea['pricing']}")
        st.markdown(f"**Notes:** {idea['notes']}")
        st.markdown("---")
