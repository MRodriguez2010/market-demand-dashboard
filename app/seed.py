import random
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Region, ServiceCategory, DemandSignal, LocalEvent, MarketInsight

REGIONS = [
    ("San Francisco", "CA", 37.7749, -122.4194, 874961, 112449),
    ("New York", "NY", 40.7128, -74.0060, 8336817, 67844),
    ("Austin", "TX", 30.2672, -97.7431, 978908, 71576),
    ("Seattle", "WA", 47.6062, -122.3321, 737015, 97185),
    ("Denver", "CO", 39.7392, -104.9903, 727211, 68592),
    ("Miami", "FL", 25.7617, -80.1918, 467963, 44268),
    ("Chicago", "IL", 41.8781, -87.6298, 2693976, 58247),
    ("Boston", "MA", 42.3601, -71.0589, 692600, 76298),
    ("Los Angeles", "CA", 34.0522, -118.2437, 3979576, 62142),
    ("Portland", "OR", 45.5152, -122.6784, 652503, 65740),
    ("Nashville", "TN", 36.1627, -86.7816, 689447, 55873),
    ("Raleigh", "NC", 35.7796, -78.6382, 467665, 63891),
    ("Phoenix", "AZ", 33.4484, -112.0740, 1680992, 52340),
    ("Atlanta", "GA", 33.7490, -84.3880, 498715, 59948),
    ("Minneapolis", "MN", 44.9778, -93.2650, 429606, 60438),
    ("Salt Lake City", "UT", 40.7608, -111.8910, 200133, 56370),
    ("Charlotte", "NC", 35.2271, -80.8431, 874579, 60886),
    ("Pittsburgh", "PA", 40.4406, -79.9959, 302971, 48711),
    ("San Diego", "CA", 32.7157, -117.1611, 1423851, 79646),
    ("Dallas", "TX", 32.7767, -96.7970, 1304379, 52210),
]

CATEGORIES = [
    ("Data Analytics & BI", "📊", "Business intelligence, dashboards, data visualization"),
    ("Web Development", "🌐", "Full-stack, frontend, backend web development"),
    ("Mobile App Dev", "📱", "iOS, Android, cross-platform mobile development"),
    ("AI & Machine Learning", "🤖", "ML models, NLP, computer vision, LLM integration"),
    ("Cloud & DevOps", "☁️", "AWS, Azure, GCP, CI/CD, infrastructure"),
    ("Cybersecurity", "🔒", "Penetration testing, compliance, security audits"),
    ("UI/UX Design", "🎨", "User research, wireframing, design systems"),
    ("Digital Marketing", "📈", "SEO, SEM, social media, content marketing"),
]

# Tech hub multipliers - some cities have higher demand for certain categories
CITY_CATEGORY_BIAS = {
    "San Francisco": {"AI & Machine Learning": 1.8, "Cloud & DevOps": 1.5, "Data Analytics & BI": 1.4},
    "New York": {"Digital Marketing": 1.6, "UI/UX Design": 1.5, "Data Analytics & BI": 1.3},
    "Austin": {"Web Development": 1.5, "AI & Machine Learning": 1.3, "Cloud & DevOps": 1.3},
    "Seattle": {"Cloud & DevOps": 1.7, "AI & Machine Learning": 1.5, "Data Analytics & BI": 1.3},
    "Miami": {"Digital Marketing": 1.4, "UI/UX Design": 1.3, "Mobile App Dev": 1.2},
    "Boston": {"AI & Machine Learning": 1.4, "Cybersecurity": 1.5, "Data Analytics & BI": 1.3},
    "Raleigh": {"Cloud & DevOps": 1.3, "Cybersecurity": 1.3, "Data Analytics & BI": 1.2},
    "Denver": {"Cybersecurity": 1.3, "Cloud & DevOps": 1.2},
}

EVENT_TEMPLATES = [
    ("{city} Tech Summit 2025", "conference", "Major tech conference attracting 5000+ attendees"),
    ("{cat} Hiring Surge in {city}", "hiring_surge", "Multiple companies expanding {cat} teams"),
    ("Series B Funding: {city} Startup", "funding", "Local startup raises $40M, expanding tech team"),
    ("{city} {cat} Meetup Group Launch", "meetup", "New professional community for {cat} practitioners"),
    ("{city} Innovation Hub Opens", "conference", "New co-working space with startup incubator"),
    ("Fortune 500 Opens {city} Office", "hiring_surge", "Major employer announces 500+ tech positions"),
    ("{cat} Bootcamp Launches in {city}", "meetup", "New training program signals growing demand"),
    ("Government Contract: {cat} in {city}", "funding", "Federal contract drives local demand"),
]

INSIGHT_TEMPLATES = [
    ("opportunity", "🔥 {cat} demand surging in {city}", "{cat} searches up {pct}% in {city}. Average project budget: ${budget}. Low competition window."),
    ("trend", "📈 {city} emerging as {cat} hub", "Consistent 3-month growth in {cat} demand. Job postings up {pct}% month-over-month."),
    ("warning", "⚠️ {cat} market saturating in {city}", "Supply of {cat} freelancers outpacing demand growth. Consider adjacent markets."),
    ("opportunity", "💎 Underserved: {cat} in {city}", "High demand score ({score}/100) but few active freelancers. First-mover advantage."),
    ("trend", "🏢 Enterprise {cat} demand in {city}", "Large enterprises in {city} increasingly outsourcing {cat} work to freelancers."),
]


async def seed_data(session: AsyncSession):
    random.seed(42)

    # Create regions
    regions = []
    for name, state, lat, lng, pop, income in REGIONS:
        r = Region(name=name, state=state, lat=lat, lng=lng, population=pop, median_income=income)
        session.add(r)
        regions.append(r)
    await session.flush()

    # Create categories
    categories = []
    for name, icon, desc in CATEGORIES:
        c = ServiceCategory(name=name, icon=icon, description=desc)
        session.add(c)
        categories.append(c)
    await session.flush()

    # Generate 12 months of demand signals for each region x category
    base_date = datetime(2025, 4, 1)
    for region in regions:
        biases = CITY_CATEGORY_BIAS.get(region.name, {})
        for cat in categories:
            bias = biases.get(cat.name, 1.0)
            base_search = random.randint(200, 2000) * bias
            base_jobs = random.randint(10, 150) * bias
            base_social = random.randint(50, 500) * bias
            base_budget = random.uniform(2000, 15000) * bias

            for m in range(12):
                month_index = base_date.year * 12 + base_date.month - 1 - (11 - m)
                month_date = datetime(month_index // 12, month_index % 12 + 1, 1)
                month_str = month_date.strftime("%Y-%m")
                # Add growth trend + noise
                growth_factor = 1 + (m * random.uniform(0.01, 0.05))
                noise = random.uniform(0.8, 1.2)

                sv = int(base_search * growth_factor * noise)
                jp = int(base_jobs * growth_factor * noise)
                sm = int(base_social * growth_factor * noise)
                budget = round(base_budget * growth_factor * random.uniform(0.9, 1.1), 2)

                # Composite demand score
                demand_score = min(100, round(
                    (sv / 3000) * 30 + (jp / 200) * 35 + (sm / 600) * 15 + (budget / 15000) * 20, 1
                ) * bias)

                prev_growth = random.uniform(-5, 15) if m > 0 else 0

                signal = DemandSignal(
                    region_id=region.id, category_id=cat.id, month=month_str,
                    search_volume=sv, job_postings=jp, social_mentions=sm,
                    demand_score=round(demand_score, 1), growth_rate=round(prev_growth, 1),
                    avg_budget=budget
                )
                session.add(signal)

    await session.flush()

    # Generate local events
    for _ in range(40):
        region = random.choice(regions)
        cat = random.choice(categories)
        tmpl = random.choice(EVENT_TEMPLATES)
        title = tmpl[0].format(city=region.name, cat=cat.name)
        desc = tmpl[2].format(city=region.name, cat=cat.name)
        evt = LocalEvent(
            region_id=region.id, title=title, event_type=tmpl[1],
            date=base_date - timedelta(days=random.randint(0, 180)),
            impact_score=round(random.uniform(3, 10), 1),
            description=desc
        )
        session.add(evt)

    # Generate insights
    for _ in range(25):
        region = random.choice(regions)
        cat = random.choice(categories)
        tmpl = random.choice(INSIGHT_TEMPLATES)
        title = tmpl[1].format(city=region.name, cat=cat.name, pct=random.randint(15, 85),
                                budget=random.randint(3000, 15000), score=random.randint(60, 95))
        desc = tmpl[2].format(city=region.name, cat=cat.name, pct=random.randint(15, 85),
                               budget=random.randint(3000, 15000), score=random.randint(60, 95))
        insight = MarketInsight(
            title=title, insight_type=tmpl[0], description=desc,
            relevance_score=round(random.uniform(5, 10), 1),
            region_name=region.name, category_name=cat.name
        )
        session.add(insight)

    await session.commit()
    print(f"Seeded: {len(regions)} regions, {len(categories)} categories, {len(regions)*len(categories)*12} demand signals, 40 events, 25 insights")
