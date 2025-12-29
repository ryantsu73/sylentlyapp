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
from services.experiments import PricingExperiment, summarize_pricing_experiment
from services.churn import estimate_monthly_churn, at_risk_heuristics
from ui.layout import (
    render_profile_header,
    render_baseline_card,
    render_pricing_test_card,
    render_dm_suggestions,
    render_whale_ideas,
)

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
# Caching (big performance win)
# -----------------------------
@st.cache_data(ttl=60 * 60, show_spinner=False)  # 1 hour
def cached_profile_lookup(handle: str, platform: str):
    return fetch_creator_profile_from_web(handle, platform)

@st.cache_data(ttl=24 * 60 * 60, show_spinner=False)  # 24 hours
def cached_synthetic_cohort(followers: int, avg_views: float, engagement: float, cpm: float, n: int = 1000):
    return generate_synthetic_cohort(followers, avg_views, engagement, cpm, n=n)

# -----------------------------
# Sidebar – inputs
# -----------------------------
st.sidebar.header("Connect / Lookup")
platform = st.sidebar.selectbox("Platform", ["OnlyFans", "Instagram", "TikTok", "YouTube"], index=0)
handle = st.sidebar.text_input("Creator handle / username", placeholder="@creatorname or creatorname")

if st.sidebar.button("Lookup from web"):
    try:
        with st.spinner(f"Looking up {handle} on {platform}..."):
            profile = cached_profile_lookup(handle, platform)
        st.session_state.web_profile = profile
        st.sidebar.success("Profile data fetched.")
    except NotImplementedError as e:
        st.sidebar.error(str(e))
    except Exception as e:
        st.sidebar.error(f"Lookup failed: {e}")

st.sidebar.markdown("---")
st.sidebar.header("Stats (override)")

wp = st.session_state.web_profile or {}
followers_input = st.sidebar.number_input("Followers / fans", min_value=1, value=int(wp.get("followers", 10_000)), step=100)
avg_views_input = st.sidebar.number_input("Avg views per post", min_value=1, value=int(wp.get("avg_views", 3_000)), step=100)
engagement_input = st.sidebar.number_input("Engagement rate (%)", min_value=0.1, max_value=100.0, value=float(wp.get("engagement_rate", 3.5)), step=0.1)
cpm_input = st.sidebar.number_input("Avg CPM (USD)", min_value=0.5, max_value=1000.0, value=float(wp.get("avg_cpm", 20.0)), step=0.5)

st.sidebar.markdown("---")
st.sidebar.header("Pricing inputs")
current_sub_price = st.sidebar.number_input("Current subscription price (USD)", min_value=1.0, max_value=200.0, value=12.0, step=0.5)
risk_profile = st.sidebar.selectbox("Risk profile", ["Conservative", "Balanced", "Aggressive"], index=1)

st.sidebar.markdown("---")
if st.sidebar.button("Generate cohort benchmarks"):
    with st.spinner("Generating synthetic cohort..."):
        st.session_state.cohort_df = cached_synthetic_cohort(
            int(followers_input),
            float(avg_views_input),
            float(engagement_input),
            float(cpm_input),
            n=1000,
        )

# -----------------------------
# Active profile
# -----------------------------
active_profile = st.session_state.web_profile or {
    "platform": platform,
    "handle": handle or "unknown",
    "profile_name": handle or "Creator",
}
est_subs = int(active_profile.get("estimated_subscribers", followers_input) or followers_input)
est_visits = active_profile.get("estimated_monthly_visits")

# -----------------------------
# Tabs UI (modern, fast navigation)
# -----------------------------
tab_overview, tab_pricing, tab_dms, tab_whales, tab_churn = st.tabs(
    ["Overview", "Pricing & A/B Tests", "DM Playbooks", "Whales", "Churn"]
)

with tab_overview:
    st.subheader("Creator overview")
    render_profile_header(active_profile)

    col_a, col_b = st.columns([2, 1])
    with col_a:
        render_baseline_card(
            followers=followers_input,
            est_subs=est_subs,
            current_price=current_sub_price,
            est_monthly_visits=est_visits,
        )

    with col_b:
        st.markdown("#### Quick earnings calculator")
        monthly_posts = st.number_input("Posts per month", min_value=1, max_value=1000, value=30, key="posts_per_month_overview")
        total_impressions, est_earnings = estimate_earnings(monthly_posts, avg_views_input, cpm_input)
        st.metric("Monthly impressions", f"{total_impressions:,.0f}")
        st.metric("Est. earnings (USD)", f"${est_earnings:,.2f}")

    st.markdown("---")
    st.subheader("Benchmarks vs similar creators")

    df = st.session_state.cohort_df
    if df is not None and len(df) > 0:
        p_followers = percentile_rank(df["followers"], followers_input)
        p_views = percentile_rank(df["avg_views"], avg_views_input)
        p_eng = percentile_rank(df["engagement_rate"], engagement_input)
        p_cpm = percentile_rank(df["avg_cpm"], cpm_input)

        st.write(
            f"- Followers: **{p_followers}th** percentile\n"
            f"- Avg views: **{p_views}th** percentile\n"
            f"- Engagement: **{p_eng}th** percentile\n"
            f"- CPM: **{p_cpm}th** percentile"
        )
        with st.expander("See sample cohort rows"):
            st.dataframe(df.head(25))
    else:
        st.info("Click **Generate cohort benchmarks** in the sidebar to see percentile positioning.")

    with st.expander("Raw profile data (debug)"):
        if st.session_state.web_profile:
            st.json(st.session_state.web_profile)
        else:
            st.write("No web profile loaded yet.")

with tab_pricing:
    st.subheader("Pricing engine + recommended test")

    pe = run_pricing_engine(
        followers=int(followers_input),
        estimated_subscribers=int(est_subs),
        avg_views=float(avg_views_input),
        engagement_rate=float(engagement_input),
        avg_cpm=float(cpm_input),
        current_price=float(current_sub_price),
        risk_profile=risk_profile.lower(),
    )

    m1, m2, m3 = st.columns(3)
    m1.metric("Suggested sub price", f"${pe['suggested_sub_price']:.2f}")
    m2.metric("PPV range", f"${pe['ppv_low']:.2f} – ${pe['ppv_high']:.2f}")
    m3.metric("Uplift vs current", f"{pe['uplift_pct_vs_current']:+.1f}%")

    render_pricing_test_card(pe["pricing_test"])

    st.markdown("---")
    st.subheader("A/B test tracker (manual logging MVP)")

    st.caption(
        "Since this MVP isn’t connected to OnlyFans private analytics, you can track a pricing test here by entering counts. "
        "This gives you a structured way to declare a winner and keep notes."
    )

    with st.container(border=True):
        exp_name = st.text_input("Experiment name", value="Pricing Test #1 (new subs)", key="exp_name")
        c_price = st.number_input("Control price ($)", min_value=1.0, max_value=200.0, value=float(current_sub_price), step=0.5, key="c_price")
        t_price = st.number_input("Test price ($)", min_value=1.0, max_value=200.0, value=float(pe["pricing_test"]["test_price"]), step=0.5, key="t_price")
        days = st.number_input("Days running", min_value=1, max_value=90, value=int(pe["pricing_test"]["duration_days"]), key="days_running")

        colx, coly = st.columns(2)
        with colx:
            c_new = st.number_input("Control new subs", min_value=0, max_value=1000000, value=0, key="c_new_subs")
            c_seen = st.number_input("Control exposures (optional)", min_value=0, max_value=100000000, value=0, key="c_seen")
        with coly:
            t_new = st.number_input("Test new subs", min_value=0, max_value=1000000, value=0, key="t_new_subs")
            t_seen = st.number_input("Test exposures (optional)", min_value=0, max_value=100000000, value=0, key="t_seen")

        if st.button("Evaluate winner"):
            exp = PricingExperiment(
                name=exp_name,
                control_price=c_price,
                test_price=t_price,
                control_new_subs=c_new,
                test_new_subs=t_new,
                days_running=int(days),
                control_seen=(c_seen or None),
                test_seen=(t_seen or None),
            )
            summary = summarize_pricing_experiment(exp)

            st.success(f"Winner (revenue proxy): {summary['winner'].upper()}")
            st.write(f"Control revenue proxy: **${summary['control_revenue_proxy']:,.2f}**")
            st.write(f"Test revenue proxy: **${summary['test_revenue_proxy']:,.2f}**")
            st.write(f"Revenue uplift: **{summary['revenue_uplift_pct']}%**")
            if summary["uplift_pct"] is not None:
                st.write(f"Outcome uplift: **{summary['uplift_pct']}%** (metric type: {summary['metric_type']})")
            st.caption(summary["notes"])

with tab_dms:
    st.subheader("DM playbooks")
    dm_suggestions = generate_dm_reachout_suggestions(
        profile=active_profile,
        followers=int(followers_input),
        estimated_subscribers=int(est_subs),
        engagement_rate=float(engagement_input),
    )
    render_dm_suggestions(dm_suggestions)

with tab_whales:
    st.subheader("Whale offers + top ways to earn more")
    whale_ideas = generate_whale_upsell_ideas(
        profile=active_profile,
        estimated_subscribers=int(est_subs),
        avg_cpm=float(cpm_input),
    )
    render_whale_ideas(whale_ideas)

    st.markdown("#### Whale revenue levers (MVP heuristics)")
    with st.container(border=True):
        st.write("- VIP tier (3–5× base price) for top 1–3%")
        st.write("- High-ticket customs bundle ($99–$249)")
        st.write("- Limited-seat group show ($50–$150/seat)")
        st.caption("When you add real spend distribution data later, this tab becomes true whale analytics.")

with tab_churn:
    st.subheader("Churn signals (MVP)")
    st.caption(
        "Without subscriber-level data, we model churn using manual inputs and heuristics. "
        "This still gives creators a ‘churn radar’ and recommended win-back actions."
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Churn estimate")
        active_subs = st.number_input("Active subscribers", min_value=1, value=int(est_subs), step=1)
        cancels_30d = st.number_input("Cancels last 30 days", min_value=0, value=0, step=1)
        churn = estimate_monthly_churn(active_subs, cancels_30d)
        st.metric("Monthly churn rate", f"{churn['monthly_churn_rate_pct']:.2f}%")
        st.write(f"Health: **{churn['health_label'].upper()}**")

    with col2:
        st.markdown("#### At-risk signals")
        payment_fails = st.number_input("Payment fails (current)", min_value=0, value=0, step=1)
        inactive_14d = st.number_input("Inactive 14+ days (count)", min_value=0, value=0, step=1)
        risk = at_risk_heuristics(payment_fails, inactive_14d)
        st.metric("Risk band", risk["risk_band"].upper())
        st.write(f"Risk score: **{risk['risk_score']}**")

    st.markdown("---")
    st.markdown("#### Recommended win-back actions")
    actions = [a for a in risk["recommended_actions"] if a]
    for a in actions:
        st.write(f"- {a}")

    st.markdown("---")
    st.markdown("#### Win-back DM templates (from DM playbooks)")
    dm_suggestions = generate_dm_reachout_suggestions(
        profile=active_profile,
        followers=int(followers_input),
        estimated_subscribers=int(est_subs),
        engagement_rate=float(engagement_input),
    )
    # Show just the lapsed/at-risk one prominently
    st.write("Best match: **Lapsed or at-risk subs**")
    st.write(dm_suggestions[-1]["message"])
    st.caption(f"CTA: {dm_suggestions[-1]['cta']} · Timing: {dm_suggestions[-1]['timing']}")

st.markdown("---")
st.caption(
    "Note: OnlyFans scraping is based on public meta information and may break if the site changes. "
    "All churn and experiment tracking here is MVP-grade unless connected to real subscriber data."
)
