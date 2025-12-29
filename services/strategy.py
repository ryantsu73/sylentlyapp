from typing import Dict, Any, List


def generate_dm_reachout_suggestions(
    profile: Dict[str, Any],
    followers: int,
    estimated_subscribers: int,
    engagement_rate: float,
) -> List[Dict[str, str]]:
    """
    Returns top-3 DM outreach suggestions (segments + example messages).
    This is intentionally high-level and text-only so you can swap in your
    own DM sending logic later.
    """
    name = profile.get("profile_name") or profile.get("handle") or "you"

    # Basic segmentation assumptions (unused in text but kept for future logic)
    subs = max(estimated_subscribers or followers, 1)
    eng = max(engagement_rate, 0.1)

    suggestions: List[Dict[str, str]] = []

    # 1) New / silent fans
    suggestions.append(
        {
            "segment": "New & silent fans (recent followers with low interaction)",
            "goal": "Convert silent followers into paying subs or PPV buyers.",
            "message": (
                f"Hey love, thanks for following {name}! 💕 "
                "I noticed you haven't seen my latest sets yet – "
                "I'm sending you an exclusive preview today. "
                "If you enjoy it, I have a full pack waiting just for you."
            ),
            "cta": "Link to a discounted intro bundle or trial subscription.",
            "timing": "Send within 24–72 hours after they follow or like for the first time.",
        }
    )

    # 2) Active engagers (high ER)
    suggestions.append(
        {
            "segment": "Highly engaged fans (frequent likes/messages)",
            "goal": "Upsell to higher-value bundles and customs.",
            "message": (
                f"You've been showing me so much love lately, thank you 🥰 "
                "I put together a VIP bundle just for my top supporters – "
                "full-length videos + behind-the-scenes, and a custom voice note from me."
            ),
            "cta": "High-value bundle / VIP tier DM with limited slots.",
            "timing": "Target top ~5–10% of engagers weekly.",
        }
    )

    # 3) Lapsed subs
    suggestions.append(
        {
            "segment": "Lapsed or at-risk subs (haven't opened content recently)",
            "goal": "Re-activate churn-risk subscribers with a time-limited offer.",
            "message": (
                "I haven't seen you around in a bit and I miss you 🥺 "
                "I'm doing a 48-hour comeback offer: custom photo + full access to "
                "my latest drop if you stay subscribed this month."
            ),
            "cta": "Retention incentive: custom piece or bundle if they keep/renew sub.",
            "timing": "Trigger 3–7 days before renewal or after 10–14 days of inactivity.",
        }
    )

    return suggestions


def generate_whale_upsell_ideas(
    profile: Dict[str, Any],
    estimated_subscribers: int,
    avg_cpm: float,
) -> List[Dict[str, str]]:
    """
    Returns strategy ideas aimed at 'whales' – your top spenders.
    Does not depend on private fan data; meant to be content/offer ideas.
    """
    name = profile.get("profile_name") or profile.get("handle") or "you"

    ideas: List[Dict[str, str]] = []

    ideas.append(
        {
            "name": "Monthly VIP whale club",
            "who": "Top 1–3% of spenders / most engaged fans.",
            "offer": (
                "Limited VIP list with priority DMs, 1 custom request per month, "
                "early access to new sets, and their name on a private thank-you list."
            ),
            "pricing": (
                "Price at 3–5x your base subscription. "
                "If your sub is $10, test $30–$50/month for VIP."
            ),
            "notes": "Cap the number of VIP spots to keep it exclusive and manageable.",
        }
    )

    ideas.append(
        {
            "name": "High-ticket custom bundles",
            "who": "Fans who already buy multiple PPVs or tip heavily.",
            "offer": (
                "Personalized photo/video bundles (e.g., 10–20 photos + 3–5 short videos) "
                "selected to their preferences, delivered over a week."
            ),
            "pricing": (
                "Bundle price in the $99–$249 range depending on your brand and demand. "
                "Anchor the value by comparing to individual PPV prices."
            ),
            "notes": "Audit past buyers and DM only those who already spent above a threshold.",
        }
    )

    ideas.append(
        {
            "name": "Whale live session / group show",
            "who": "Very small group of highest tippers.",
            "offer": (
                "Exclusive live session (group or 1:1), with recording access included, "
                "plus behind-the-scenes content."
            ),
            "pricing": (
                "Group: $50–$150 per seat with limited spots. "
                "1:1: $150–$500 depending on length and boundaries."
            ),
            "notes": "Use manual vetting: invite only fans you’re comfortable with.",
        }
    )

    return ideas
