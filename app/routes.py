from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, desc
from .database import get_db
from .models import Region, ServiceCategory, DemandSignal, LocalEvent, MarketInsight

router = APIRouter()


@router.get("/dashboard/overview")
async def overview(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    regions = (await db.execute(select(func.count(Region.id)))).scalar()
    categories = (await db.execute(select(func.count(ServiceCategory.id)))).scalar()
    signals = (await db.execute(select(func.count(DemandSignal.id)))).scalar()
    avg_demand = (await db.execute(select(func.avg(DemandSignal.demand_score)))).scalar()
    avg_budget = (await db.execute(select(func.avg(DemandSignal.avg_budget)))).scalar()
    max_demand = (await db.execute(select(func.max(DemandSignal.demand_score)))).scalar()
    total_search = (await db.execute(select(func.sum(DemandSignal.search_volume)))).scalar()
    avg_growth = (await db.execute(select(func.avg(DemandSignal.growth_rate)))).scalar()
    return {
        "total_regions": regions, "total_categories": categories,
        "total_signals": signals, "avg_demand_score": round(avg_demand or 0, 1),
        "avg_budget": round(avg_budget or 0, 2), "max_demand_score": round(max_demand or 0, 1),
        "total_search_volume": total_search or 0, "avg_growth_rate": round(avg_growth or 0, 1),
    }


@router.get("/dashboard/heatmap")
async def heatmap_data(category_id: int = Query(None), db: AsyncSession = Depends(get_db)):
    """Returns latest demand data per region for map visualization."""
    from sqlalchemy import select
    # Get latest month
    latest_month = (await db.execute(select(func.max(DemandSignal.month)))).scalar()
    
    q = select(
        Region.name, Region.state, Region.lat, Region.lng, Region.population, Region.median_income,
        func.avg(DemandSignal.demand_score).label("demand_score"),
        func.sum(DemandSignal.search_volume).label("search_volume"),
        func.sum(DemandSignal.job_postings).label("job_postings"),
        func.avg(DemandSignal.avg_budget).label("avg_budget"),
        func.avg(DemandSignal.growth_rate).label("growth_rate"),
    ).join(DemandSignal, Region.id == DemandSignal.region_id
    ).where(DemandSignal.month == latest_month)
    
    if category_id:
        q = q.where(DemandSignal.category_id == category_id)
    
    q = q.group_by(Region.id).order_by(desc("demand_score"))
    rows = (await db.execute(q)).all()
    
    return [
        {"name": r.name, "state": r.state, "lat": r.lat, "lng": r.lng,
         "population": r.population, "median_income": r.median_income,
         "demand_score": round(r.demand_score, 1), "search_volume": r.search_volume,
         "job_postings": r.job_postings, "avg_budget": round(r.avg_budget, 2),
         "growth_rate": round(r.growth_rate, 1)}
        for r in rows
    ]


@router.get("/dashboard/trends")
async def demand_trends(region_id: int = Query(None), category_id: int = Query(None),
                         db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    q = select(
        DemandSignal.month,
        func.avg(DemandSignal.demand_score).label("demand_score"),
        func.sum(DemandSignal.search_volume).label("search_volume"),
        func.sum(DemandSignal.job_postings).label("job_postings"),
        func.avg(DemandSignal.avg_budget).label("avg_budget"),
    )
    if region_id:
        q = q.where(DemandSignal.region_id == region_id)
    if category_id:
        q = q.where(DemandSignal.category_id == category_id)
    q = q.group_by(DemandSignal.month).order_by(DemandSignal.month)
    rows = (await db.execute(q)).all()
    return [
        {"month": r.month, "demand_score": round(r.demand_score, 1),
         "search_volume": r.search_volume, "job_postings": r.job_postings,
         "avg_budget": round(r.avg_budget, 2)}
        for r in rows
    ]


@router.get("/dashboard/categories")
async def category_breakdown(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    latest_month = (await db.execute(select(func.max(DemandSignal.month)))).scalar()
    q = select(
        ServiceCategory.name, ServiceCategory.icon,
        func.avg(DemandSignal.demand_score).label("demand_score"),
        func.sum(DemandSignal.search_volume).label("search_volume"),
        func.sum(DemandSignal.job_postings).label("job_postings"),
        func.avg(DemandSignal.avg_budget).label("avg_budget"),
        func.avg(DemandSignal.growth_rate).label("growth_rate"),
    ).join(DemandSignal, ServiceCategory.id == DemandSignal.category_id
    ).where(DemandSignal.month == latest_month
    ).group_by(ServiceCategory.id).order_by(desc("demand_score"))
    rows = (await db.execute(q)).all()
    return [
        {"name": r.name, "icon": r.icon, "demand_score": round(r.demand_score, 1),
         "search_volume": r.search_volume, "job_postings": r.job_postings,
         "avg_budget": round(r.avg_budget, 2), "growth_rate": round(r.growth_rate, 1)}
        for r in rows
    ]


@router.get("/dashboard/top-markets")
async def top_markets(limit: int = 10, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    latest_month = (await db.execute(select(func.max(DemandSignal.month)))).scalar()
    q = select(
        Region.name, Region.state, ServiceCategory.name.label("category"),
        DemandSignal.demand_score, DemandSignal.avg_budget, DemandSignal.growth_rate,
        DemandSignal.search_volume, DemandSignal.job_postings,
    ).join(Region, DemandSignal.region_id == Region.id
    ).join(ServiceCategory, DemandSignal.category_id == ServiceCategory.id
    ).where(DemandSignal.month == latest_month
    ).order_by(desc(DemandSignal.demand_score)).limit(limit)
    rows = (await db.execute(q)).all()
    return [
        {"region": r.name, "state": r.state, "category": r.category,
         "demand_score": round(r.demand_score, 1), "avg_budget": round(r.avg_budget, 2),
         "growth_rate": round(r.growth_rate, 1), "search_volume": r.search_volume,
         "job_postings": r.job_postings}
        for r in rows
    ]


@router.get("/dashboard/events")
async def events(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    q = select(LocalEvent, Region.name.label("region_name")).join(
        Region, LocalEvent.region_id == Region.id
    ).order_by(desc(LocalEvent.date)).limit(20)
    rows = (await db.execute(q)).all()
    return [
        {"title": r.LocalEvent.title, "event_type": r.LocalEvent.event_type,
         "date": r.LocalEvent.date.strftime("%Y-%m-%d"), "impact_score": r.LocalEvent.impact_score,
         "description": r.LocalEvent.description, "region": r.region_name}
        for r in rows
    ]


@router.get("/dashboard/insights")
async def insights(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    q = select(MarketInsight).order_by(desc(MarketInsight.relevance_score)).limit(15)
    rows = (await db.execute(q)).scalars().all()
    return [
        {"title": r.title, "type": r.insight_type, "description": r.description,
         "relevance_score": r.relevance_score, "region": r.region_name,
         "category": r.category_name}
        for r in rows
    ]


@router.get("/dashboard/region-compare")
async def region_compare(db: AsyncSession = Depends(get_db)):
    """Compare all regions across all categories for the latest month."""
    from sqlalchemy import select
    latest_month = (await db.execute(select(func.max(DemandSignal.month)))).scalar()
    q = select(
        Region.name.label("region"), ServiceCategory.name.label("category"),
        DemandSignal.demand_score
    ).join(Region, DemandSignal.region_id == Region.id
    ).join(ServiceCategory, DemandSignal.category_id == ServiceCategory.id
    ).where(DemandSignal.month == latest_month)
    rows = (await db.execute(q)).all()
    return [{"region": r.region, "category": r.category, "demand_score": round(r.demand_score, 1)} for r in rows]


@router.get("/categories")
async def list_categories(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    rows = (await db.execute(select(ServiceCategory))).scalars().all()
    return [{"id": c.id, "name": c.name, "icon": c.icon} for c in rows]


@router.get("/regions")
async def list_regions(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    rows = (await db.execute(select(Region))).scalars().all()
    return [{"id": r.id, "name": r.name, "state": r.state} for r in rows]
