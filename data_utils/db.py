"""
data_utils/db.py
SQLite database with SQLAlchemy ORM.
Tables: Product, PrintJob
"""
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

Base = declarative_base()
_engine = None
_SessionLocal = None

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "agislabels.db")


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(f"sqlite:///{os.path.abspath(DB_PATH)}", echo=False,
                                connect_args={"check_same_thread": False})
        Base.metadata.create_all(_engine)
    return _engine


def get_session() -> Session:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine())
    return _SessionLocal()


# ─── Models ──────────────────────────────────────────────────────────────────

class Product(Base):
    __tablename__ = "products"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    name        = Column(String(255), nullable=False)
    barcode     = Column(String(64),  nullable=True)
    price       = Column(Float,       nullable=True)
    category    = Column(String(128), nullable=True)
    description = Column(Text,        nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "barcode": self.barcode or "",
            "price": self.price or 0.0,
            "category": self.category or "",
            "description": self.description or "",
        }


class PrintJob(Base):
    __tablename__ = "print_jobs"
    id             = Column(Integer,  primary_key=True, autoincrement=True)
    timestamp      = Column(DateTime, default=datetime.now)
    template_name  = Column(String(255), nullable=True)
    printer_name   = Column(String(255), nullable=True)
    rows_printed   = Column(Integer,  default=0)
    status         = Column(String(32), default="ok")   # ok | error | partial
    notes          = Column(Text,     nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S") if self.timestamp else "",
            "template_name": self.template_name or "",
            "printer_name": self.printer_name or "",
            "rows_printed": self.rows_printed,
            "status": self.status,
            "notes": self.notes or "",
        }


# ─── Product CRUD ─────────────────────────────────────────────────────────────

def list_products(search: str = "") -> list:
    with get_session() as s:
        q = s.query(Product)
        if search:
            q = q.filter(Product.name.ilike(f"%{search}%"))
        return [p.to_dict() for p in q.order_by(Product.name).all()]


def add_product(name, barcode="", price=0.0, category="", description="") -> dict:
    with get_session() as s:
        p = Product(name=name, barcode=barcode, price=price,
                    category=category, description=description)
        s.add(p)
        s.commit()
        s.refresh(p)
        return p.to_dict()


def update_product(pid: int, **kwargs):
    with get_session() as s:
        p = s.query(Product).filter_by(id=pid).first()
        if p:
            for k, v in kwargs.items():
                setattr(p, k, v)
            s.commit()


def delete_product(pid: int):
    with get_session() as s:
        p = s.query(Product).filter_by(id=pid).first()
        if p:
            s.delete(p)
            s.commit()


# ─── PrintJob helpers ─────────────────────────────────────────────────────────

def log_print_job(template_name: str, printer_name: str, rows: int,
                  status: str = "ok", notes: str = ""):
    with get_session() as s:
        job = PrintJob(template_name=template_name, printer_name=printer_name,
                       rows_printed=rows, status=status, notes=notes,
                       timestamp=datetime.now())
        s.add(job)
        s.commit()
        s.refresh(job)
        return job.to_dict()


def list_print_jobs(limit: int = 200) -> list:
    with get_session() as s:
        jobs = s.query(PrintJob).order_by(PrintJob.timestamp.desc()).limit(limit).all()
        return [j.to_dict() for j in jobs]
