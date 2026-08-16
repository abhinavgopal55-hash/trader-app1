from datetime import date, datetime
from typing import Optional

from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Trader
from .i18n import get_text

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Panchayat Trader Survey")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def calculate_status(has_licence: Optional[str], expiry: Optional[date]) -> str:
    if has_licence == "No":
        return "NO_LICENCE"
    if has_licence == "Don't Know":
        return "VERIFICATION_REQUIRED"
    if has_licence == "Yes":
        if not expiry:
            return "VERIFICATION_REQUIRED"
        if expiry < date.today():
            return "EXPIRED"
        return "VALID"
    return "VERIFICATION_REQUIRED"


def parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def next_trader_code(db: Session) -> str:
    max_id = db.query(func.max(Trader.id)).scalar() or 0
    return f"TR-{max_id + 1:06d}"


def base_ctx(request: Request, lang: str):
    return {"request": request, "t": get_text(lang), "lang": lang}


# ---------------------------------------------------------
# Home / New trader form
# ---------------------------------------------------------

@app.get("/")
def home(request: Request, lang: str = "en"):
    return templates.TemplateResponse("home.html", base_ctx(request, lang))


@app.post("/")
def save_trader(
    request: Request,
    lang: str = Form("en"),
    business_name: str = Form(...),
    owner_name: str = Form(...),
    mobile: str = Form(""),
    ward_no: Optional[str] = Form(None),
    building_no: str = Form(""),
    address: str = Form(""),
    trade_type: str = Form(""),
    has_licence: str = Form(...),
    licence_number: str = Form(""),
    licence_issue_date: str = Form(""),
    licence_expiry_date: str = Form(""),
    no_licence_reason: str = Form(""),
    remarks: str = Form(""),
    db: Session = Depends(get_db),
):
    trader = Trader(
        trader_code=next_trader_code(db),
        business_name=business_name,
        owner_name=owner_name,
        mobile=mobile,
        ward_no=int(ward_no) if ward_no else None,
        building_no=building_no,
        address=address,
        trade_type=trade_type,
        has_licence=has_licence,
        licence_number=licence_number,
        licence_issue_date=parse_date(licence_issue_date),
        licence_expiry_date=parse_date(licence_expiry_date),
        no_licence_reason=no_licence_reason,
        remarks=remarks,
    )
    db.add(trader)
    db.commit()
    db.refresh(trader)

    ctx = base_ctx(request, lang)
    ctx["heading"] = ctx["t"]["saved"]
    ctx["trader"] = trader
    return templates.TemplateResponse("success.html", ctx)


# ---------------------------------------------------------
# Trader register (list + search)
# ---------------------------------------------------------

@app.get("/traders")
def traders_page(request: Request, lang: str = "en", q: str = "", db: Session = Depends(get_db)):
    query = db.query(Trader)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Trader.business_name.ilike(like),
                Trader.owner_name.ilike(like),
                Trader.mobile.ilike(like),
                Trader.building_no.ilike(like),
                Trader.licence_number.ilike(like),
            )
        )
    traders = query.order_by(Trader.id.desc()).all()

    rows = [(tr, calculate_status(tr.has_licence, tr.licence_expiry_date)) for tr in traders]

    ctx = base_ctx(request, lang)
    ctx["rows"] = rows
    ctx["q"] = q
    return templates.TemplateResponse("traders.html", ctx)


# ---------------------------------------------------------
# View trader
# ---------------------------------------------------------

@app.get("/traders/{trader_id}")
def view_trader(request: Request, trader_id: int, lang: str = "en", db: Session = Depends(get_db)):
    trader = db.query(Trader).filter(Trader.id == trader_id).first()
    ctx = base_ctx(request, lang)
    if not trader:
        return templates.TemplateResponse("not_found.html", ctx)
    ctx["trader"] = trader
    ctx["status"] = calculate_status(trader.has_licence, trader.licence_expiry_date)
    return templates.TemplateResponse("view.html", ctx)


# ---------------------------------------------------------
# Edit trader
# ---------------------------------------------------------

@app.get("/traders/{trader_id}/edit")
def edit_trader_form(request: Request, trader_id: int, lang: str = "en", db: Session = Depends(get_db)):
    trader = db.query(Trader).filter(Trader.id == trader_id).first()
    ctx = base_ctx(request, lang)
    if not trader:
        return templates.TemplateResponse("not_found.html", ctx)
    ctx["trader"] = trader
    return templates.TemplateResponse("edit.html", ctx)


@app.post("/traders/{trader_id}/edit")
def edit_trader_submit(
    request: Request,
    trader_id: int,
    lang: str = Form("en"),
    business_name: str = Form(...),
    owner_name: str = Form(...),
    mobile: str = Form(""),
    ward_no: Optional[str] = Form(None),
    building_no: str = Form(""),
    address: str = Form(""),
    trade_type: str = Form(""),
    has_licence: str = Form(...),
    licence_number: str = Form(""),
    licence_issue_date: str = Form(""),
    licence_expiry_date: str = Form(""),
    no_licence_reason: str = Form(""),
    remarks: str = Form(""),
    db: Session = Depends(get_db),
):
    trader = db.query(Trader).filter(Trader.id == trader_id).first()
    ctx = base_ctx(request, lang)
    if not trader:
        return templates.TemplateResponse("not_found.html", ctx)

    trader.business_name = business_name
    trader.owner_name = owner_name
    trader.mobile = mobile
    trader.ward_no = int(ward_no) if ward_no else None
    trader.building_no = building_no
    trader.address = address
    trader.trade_type = trade_type
    trader.has_licence = has_licence
    trader.licence_number = licence_number
    trader.licence_issue_date = parse_date(licence_issue_date)
    trader.licence_expiry_date = parse_date(licence_expiry_date)
    trader.no_licence_reason = no_licence_reason
    trader.remarks = remarks
    db.commit()
    db.refresh(trader)

    ctx["heading"] = ctx["t"]["updated"]
    ctx["trader"] = trader
    return templates.TemplateResponse("success.html", ctx)


# ---------------------------------------------------------
# Delete trader
# ---------------------------------------------------------

@app.get("/traders/{trader_id}/delete")
def delete_confirm(request: Request, trader_id: int, lang: str = "en", db: Session = Depends(get_db)):
    trader = db.query(Trader).filter(Trader.id == trader_id).first()
    ctx = base_ctx(request, lang)
    if not trader:
        return templates.TemplateResponse("not_found.html", ctx)
    ctx["trader"] = trader
    return templates.TemplateResponse("delete_confirm.html", ctx)


@app.post("/traders/{trader_id}/delete")
def delete_trader(request: Request, trader_id: int, lang: str = Form("en"), db: Session = Depends(get_db)):
    trader = db.query(Trader).filter(Trader.id == trader_id).first()
    if trader:
        db.delete(trader)
        db.commit()
    return RedirectResponse(url=f"/traders?lang={lang}", status_code=303)


# ---------------------------------------------------------
# Dashboard
# ---------------------------------------------------------

@app.get("/dashboard")
def dashboard(request: Request, lang: str = "en", db: Session = Depends(get_db)):
    traders = db.query(Trader).all()

    total = len(traders)
    licensed = expired = no_licence = verification = 0
    ward_counts: dict[int, int] = {}

    for tr in traders:
        status = calculate_status(tr.has_licence, tr.licence_expiry_date)
        if status == "VALID":
            licensed += 1
        elif status == "NO_LICENCE":
            no_licence += 1
        elif status == "EXPIRED":
            expired += 1
        elif status == "VERIFICATION_REQUIRED":
            verification += 1

        if tr.ward_no:
            ward_counts[tr.ward_no] = ward_counts.get(tr.ward_no, 0) + 1

    ctx = base_ctx(request, lang)
    ctx.update(
        total=total,
        licensed=licensed,
        expired=expired,
        no_licence=no_licence,
        verification=verification,
        ward_counts=sorted(ward_counts.items()),
    )
    return templates.TemplateResponse("dashboard.html", ctx)


@app.get("/health")
def health():
    return {"status": "ok"}
