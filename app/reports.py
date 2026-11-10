from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from pydantic import BaseModel
from typing import Optional
import io
from .database import get_db
from .models import Region, ServiceCategory, DemandSignal, MarketInsight

router = APIRouter()


class ReportRequest(BaseModel):
    format: str = "pdf"
    category_id: Optional[int] = None


async def _get_report_data(db: AsyncSession, category_id=None):
    latest_month = (await db.execute(select(func.max(DemandSignal.month)))).scalar()
    
    # Overview stats
    avg_demand = (await db.execute(select(func.avg(DemandSignal.demand_score)))).scalar()
    total_regions = (await db.execute(select(func.count(Region.id)))).scalar()
    
    # Top markets
    q = select(
        Region.name, ServiceCategory.name.label("category"),
        DemandSignal.demand_score, DemandSignal.avg_budget
    ).select_from(DemandSignal).join(Region, Region.id == DemandSignal.region_id).join(ServiceCategory, ServiceCategory.id == DemandSignal.category_id).where(
        DemandSignal.month == latest_month
    ).order_by(desc(DemandSignal.demand_score)).limit(15)
    if category_id:
        q = q.where(DemandSignal.category_id == category_id)
    top_markets = (await db.execute(q)).all()
    
    # Category stats
    cq = select(
        ServiceCategory.name,
        func.avg(DemandSignal.demand_score).label("score"),
        func.avg(DemandSignal.avg_budget).label("budget"),
    ).join(DemandSignal).where(DemandSignal.month == latest_month).group_by(ServiceCategory.id)
    cat_stats = (await db.execute(cq)).all()
    
    return {
        "latest_month": latest_month,
        "avg_demand": round(avg_demand or 0, 1),
        "total_regions": total_regions,
        "top_markets": [{"region": m.name, "category": m.category,
                         "score": round(m.demand_score, 1), "budget": round(m.avg_budget, 2)}
                        for m in top_markets],
        "categories": [{"name": c.name, "score": round(c.score, 1), "budget": round(c.budget, 2)}
                       for c in cat_stats],
    }


@router.post("/reports/generate")
async def generate_report(req: ReportRequest, db: AsyncSession = Depends(get_db)):
    data = await _get_report_data(db, req.category_id)

    if req.format == "pdf":
        return _generate_pdf(data)
    elif req.format == "pptx":
        return _generate_pptx(data)
    elif req.format == "xlsx":
        return _generate_xlsx(data)
    return {"error": "Unsupported format"}


def _generate_pdf(data):
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Synthetic Market Demand Report", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Report Period: {data['latest_month']} | Regions: {data['total_regions']} | Avg Demand: {data['avg_demand']}/100", styles["Normal"]))
    story.append(Spacer(1, 20))

    # Category summary
    story.append(Paragraph("Category Demand Summary", styles["Heading2"]))
    cat_data = [["Category", "Demand Score", "Avg Budget"]]
    for c in data["categories"]:
        cat_data.append([c["name"], str(c["score"]), f"${c['budget']:,.0f}"])
    t = Table(cat_data, colWidths=[200, 100, 100])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
    ]))
    story.append(t)
    story.append(Spacer(1, 20))

    # Top markets
    story.append(Paragraph("Top Market Opportunities", styles["Heading2"]))
    mkt_data = [["Region", "Category", "Demand Score", "Avg Budget"]]
    for m in data["top_markets"][:10]:
        mkt_data.append([m["region"], m["category"], str(m["score"]), f"${m['budget']:,.0f}"])
    t2 = Table(mkt_data, colWidths=[120, 150, 100, 100])
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#10b981")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    story.append(t2)

    doc.build(story)
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/pdf",
                             headers={"Content-Disposition": "attachment; filename=market_heatmap_report.pdf"})


def _generate_pptx(data):
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Title slide
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    txBox = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(11), Inches(3))
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = "Synthetic Market Demand"
    p.font.size = Pt(40)
    p.font.bold = True
    p.font.color.rgb = RGBColor(0x1E, 0x3A, 0x5F)
    p2 = tf.add_paragraph()
    p2.text = f"Period: {data['latest_month']} | {data['total_regions']} Regions Analyzed"
    p2.font.size = Pt(18)

    # Category slide
    slide2 = prs.slides.add_slide(prs.slide_layouts[6])
    txBox2 = slide2.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12), Inches(1))
    txBox2.text_frame.paragraphs[0].text = "Service Category Demand"
    txBox2.text_frame.paragraphs[0].font.size = Pt(28)
    txBox2.text_frame.paragraphs[0].font.bold = True

    from pptx.util import Emu
    rows = len(data["categories"]) + 1
    table = slide2.shapes.add_table(rows, 3, Inches(1), Inches(1.5), Inches(10), Inches(0.5 * rows)).table
    table.columns[0].width = Inches(5)
    table.columns[1].width = Inches(2.5)
    table.columns[2].width = Inches(2.5)
    for i, h in enumerate(["Category", "Demand Score", "Avg Budget"]):
        table.cell(0, i).text = h
    for i, c in enumerate(data["categories"]):
        table.cell(i + 1, 0).text = c["name"]
        table.cell(i + 1, 1).text = str(c["score"])
        table.cell(i + 1, 2).text = f"${c['budget']:,.0f}"

    # Top markets slide
    slide3 = prs.slides.add_slide(prs.slide_layouts[6])
    txBox3 = slide3.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12), Inches(1))
    txBox3.text_frame.paragraphs[0].text = "Top Market Opportunities"
    txBox3.text_frame.paragraphs[0].font.size = Pt(28)
    txBox3.text_frame.paragraphs[0].font.bold = True

    mkt_rows = min(10, len(data["top_markets"])) + 1
    table2 = slide3.shapes.add_table(mkt_rows, 4, Inches(0.5), Inches(1.5), Inches(12), Inches(0.45 * mkt_rows)).table
    for i, h in enumerate(["Region", "Category", "Score", "Budget"]):
        table2.cell(0, i).text = h
    for i, m in enumerate(data["top_markets"][:10]):
        table2.cell(i + 1, 0).text = m["region"]
        table2.cell(i + 1, 1).text = m["category"]
        table2.cell(i + 1, 2).text = str(m["score"])
        table2.cell(i + 1, 3).text = f"${m['budget']:,.0f}"

    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                             headers={"Content-Disposition": "attachment; filename=market_heatmap_report.pptx"})


def _generate_xlsx(data):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill

    wb = Workbook()
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1E3A5F", end_color="1E3A5F", fill_type="solid")

    # Categories sheet
    ws = wb.active
    ws.title = "Categories"
    for i, h in enumerate(["Category", "Demand Score", "Avg Budget"], 1):
        ws.cell(1, i, h).font = header_font
        ws.cell(1, i).fill = header_fill
    for i, c in enumerate(data["categories"], 2):
        ws.cell(i, 1, c["name"])
        ws.cell(i, 2, c["score"])
        ws.cell(i, 3, c["budget"])

    # Top markets sheet
    ws2 = wb.create_sheet("Top Markets")
    for i, h in enumerate(["Region", "Category", "Demand Score", "Avg Budget"], 1):
        ws2.cell(1, i, h).font = header_font
        ws2.cell(1, i).fill = header_fill
    for i, m in enumerate(data["top_markets"], 2):
        ws2.cell(i, 1, m["region"])
        ws2.cell(i, 2, m["category"])
        ws2.cell(i, 3, m["score"])
        ws2.cell(i, 4, m["budget"])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": "attachment; filename=market_heatmap_report.xlsx"})
