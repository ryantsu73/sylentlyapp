import streamlit as st

from services.onlyfans import fetch_creator_profile_from_web
from services.analytics import (
    generate_synthetic_cohort,
    percentile_rank,
    estimate_earnings,
)
from services.strategy import (
    generate_dm_reachout_suggestions,
    generate_whale_upsell_ideas,
)
from services.pricing import run_pricing_engine
from ui.layout import (
    render_profile_header,
    render_baseline_card,
    render_pricing_test_card,
    render_dm_suggestions,
    render_whale_ideas,
)

# -----------------------------
# Streamlit page config
# -----------------------------

st.set_page_config(
    page_title="Silent Partner – Creator Revenue Co-pilot",
    page_icon="📊",
    layout="wide",
)

st.title("Silent Partner – Creator Revenue Co‑pilot (MVP)")


# -----------------------------
# Session state
# -----------------------------
if "web_profile" not in st.session_state:
    st.session_state.web_profile = None
if "cohort_df" not in st.session_state:
    st.session_state.cohort_df = None


# -----------------------------
# Sidebar – Onboarding & inputs
# -----------------------------

st.sidebar.header("1. Connect / Lookup your creator profile")

platform = st.sidebar.selectbox(
    "Platform",
    options=["OnlyFans", "Instagram", "TikTok", "YouTube"],
    index=0,
)

handle = st.sidebar.text_input(
    "Creator handle / username",
    placeholder="@creatorname or creatorname",
)

if st.sidebar.button("Lookup from web"):
    try:
        with st.spinner(f"Looking up {handle} on {platform}..."):
            profile = fetch_creator_profile_from_web(handle, platform)
        st.session_state.web_profile = profile
        st.sidebar.success("Profile data fetched from web.")
    except NotImplementedError as e:
        st.sidebar.error(str(e))
    except Exception as e:
        st.sidebar.error(f"Lookup failed: {e}")

st.sidebar.markdown("---")
st.sidebar.header("2. Confirm / override core audience stats")

wp = st.session_state.web_profile or {}

followers_default = int(wp.get("followers", 10_000))
avg_views_default = int(wp.get("avg_views", 3_000))
engagement_default = float(wp.get("engagement_rate", 3.5))
cpm_default = float(wp.get("avg_cpm", 20.0))

followers_input = st.sidebar.number_input(
    "Followers / fans",
    min_value=1,
    value=followers_default,
    step=100,
    help="If web lookup failed or is approximate, set this manually.",
)

avg_views_input = st.sidebar.number_input(
    "Average views per post",
    min_value=1,
    value=avg_views_default,
    step=100,
)

engagement_input = st.sidebar.number_input(
    "Engagement rate (%)",
    min_value=0.1,
    max_value=100.0,
    value=engagement_default,
    step=0.1,
)

cpm_input = st.sidebar.number_input(
    "Average CPM (USD)",
    min_value=0.5,
    max_value=1000.0,
    value=cpm_default,
    step=0.5,
)

st.sidebar.markdown("---")
st.sidebar.header("3. Subscription pricing input")

current_sub_price = st.sidebar.number_input(
    "Current subscription price (USD)",
    min_value=1.0,
    max_value=200.0,
    value=12.0,
    step=0.5,
)

risk_profile = st.sidebar.selectbox(
    "Pricing test risk profile",
    options=["Conservative", "Balanced", "Aggressive"],
    index=1,
    help="Controls how bold the recommended pricing test is.",
)

st.sidebar.markdown("---")
generate_btn = st.sidebar.button("Generate synthetic cohort & benchmarks")


# -----------------------------
# Main layout
# -----------------------------

col_main, col_side = st.columns([3, 2])

with col_main:
    st.subheader("Creator overview & baseline")

    active_profile = st.session_state.web_profile or {
        "platform": platform,
        "handle": handle or "unknown",
        "profile_name": handle or "Creator",
    }

    # -- Profile header
    render_profile_header(active_profile)

    # Estimated subs & visits
    est_subs = active_profile.get("estimated_subscribers", followers_input)
    est_visits = active_profile.get("estimated_monthly_visits")

    # Baseline card – approximate MRR
    render_baseline_card(
        followers=followers_input,
        est_subs=int(est_subs or followers_input),
        current_price=current_sub_price,
        est_monthly_visits=est_visits,
    )

    st.markdown("---")
    st.subheader("Benchmarks vs similar creators")

    if generate_btn:
        with st.spinner("Generating synthetic cohort and benchmarks..."):
            df = generate_synthetic_cohort(
                followers=int(followers_input),
                avg_views=float(avg_views_input),
                engagement_rate=float(engagement_input),
                avg_cpm=float(cpm_input),
                n=1000,
            )
            st.session_state.cohort_df = df

    df = st.session_state.cohort_df

    if df is not None and len(df) > 0:
        p_followers = percentile_rank(df["followers"], followers_input)
        p_views = percentile_rank(df["avg_views"], avg_views_input)
        p_eng = percentile_rank(df["engagement_rate"], engagement_input)
        p_cpm = percentile_rank(df["avg_cpm"], cpm_input)

        st.markdown("### Percentile positioning (synthetic cohort)")
        st.write(
            f"- Followers: **{p_followers}th** percentile\n"
            f"- Average views: **{p_views}th** percentile\n"
            f"- Engagement rate: **{p_eng}th** percentile\n"
            f"- CPM: **{p_cpm}th** percentile"
        )

        st.markdown("### Sample of synthetic cohort")
        st.dataframe(df.head(20))
    else:
        st.info("Generate the synthetic cohort from the sidebar to see benchmarks here.")

    # -------------------------
    # Pricing Lab (new engine)
    # -------------------------
    st.markdown("---")
    st.subheader("Pricing Lab – subscription & PPV strategy")

    pe = run_pricing_engine(
        followers=int(followers_input),
        estimated_subscribers=int(est_subs or followers_input),
        avg_views=float(avg_views_input),
        engagement_rate=float(engagement_input),
        avg_cpm=float(cpm_input),
        current_price=float(current_sub_price),
        risk_profile=risk_profile.lower(),
    )

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("Suggested sub price", f"${pe['suggested_sub_price']:.2f}")
    with col_b:
        st.metric("PPV range (low–high)", f"${pe['ppv_low']:.2f} – ${pe['ppv_high']:.2f}")
    with col_c:
        uplift_str = f"{pe['uplift_pct_vs_current']:+.1f}%"
        st.metric("Potential revenue uplift vs current", uplift_str)

    st.markdown("### Model assumptions")
    st.write(
        f"- Implied revenue per fan (from CPM): **${pe['implied_revenue_per_fan']:.2f}** / month\n"
        f"- Target sub penetration: **{pe['target_sub_penetration']:.1f}%** of followers\n"
        f"- Target ARPU from subs: **${pe['target_arpu']:.2f}** / month"
    )
    st.caption(
        "These are heuristic estimates. In a full Silent Partner build, this engine "
        "would be calibrated against your real subscriber & revenue history."
    )

    st.markdown("### Recommended pricing test")
    render_pricing_test_card(pe["pricing_test"])

    # -------------------------
    # Strategy & outreach
    # -------------------------
    st.markdown("---")
    st.subheader("Revenue strategy & outreach")

    dm_suggestions = generate_dm_reachout_suggestions(
        profile=active_profile,
        followers=int(followers_input),
        estimated_subscribers=int(est_subs or followers_input),
        engagement_rate=float(engagement_input),
    )

    whale_ideas = generate_whale_upsell_ideas(
        profile=active_profile,
        estimated_subscribers=int(est_subs or followers_input),
        avg_cpm=float(cpm_input),
    )

    dm_tab, whale_tab = st.tabs(["DM outreach (top 3)", "Whale offers"])

    with dm_tab:
        render_dm_suggestions(dm_suggestions)

    with whale_tab:
        render_whale_ideas(whale_ideas)


with col_side:
    st.subheader("Quick earnings calculator")

    st.markdown(
        "Back-of-the-envelope estimate of your monthly earnings from content impressions."
    )

    monthly_posts = st.number_input(
        "Estimated posts per month",
        min_value=1,
        max_value=1000,
        value=30,
    )

    total_impressions, est_earnings = estimate_earnings(
        monthly_posts=monthly_posts,
        avg_views_per_post=avg_views_input,
        cpm=cpm_input,
    )

    st.metric(
        label="Estimated monthly impressions",
        value=f"{total_impressions:,.0f}",
    )
    st.metric(
        label="Estimated monthly earnings (USD)",
        value=f"${est_earnings:,.2f}",
    )

    st.caption(
        "These are rough estimates only. For serious forecasting, plug in your real "
        "impression data and a more sophisticated revenue model."
    )

    st.markdown("---")
    st.subheader("Raw profile data (debug)")

    if st.session_state.web_profile:
        st.json(st.session_state.web_profile)
    else:
        st.info("No web profile loaded yet. Use the sidebar to look up a creator.")

# Footer
st.markdown("---")
st.caption(
    "Note: OnlyFans scraping is based on public meta information and may break "
    "if the site changes its structure. Always respect the platform's terms of service. "
    "Subscriber and visit metrics shown here are estimates derived from public data. "
    "DM outreach, whale offers, and pricing suggestions are heuristics that should be "
    "validated before making big pricing moves."
)
