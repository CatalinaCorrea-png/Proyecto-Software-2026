from datetime import datetime, timezone
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.database import Base


class Mission(Base):
    __tablename__ = "missions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String, default="active")
    initial_battery: Mapped[float] = mapped_column(Float, default=100.0)
    final_battery: Mapped[float | None] = mapped_column(Float, nullable=True)
    coverage_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    detections_count: Mapped[int] = mapped_column(Integer, default=0)
    grid_rows: Mapped[int] = mapped_column(Integer)
    grid_cols: Mapped[int] = mapped_column(Integer)
    grid_center_lat: Mapped[float] = mapped_column(Float)
    grid_center_lng: Mapped[float] = mapped_column(Float)

    detections: Mapped[list["Detection"]] = relationship(
        back_populates="mission", cascade="all, delete-orphan"
    )
    grid_cells: Mapped[list["GridCell"]] = relationship(
        back_populates="mission", cascade="all, delete-orphan"
    )


class Detection(Base):
    __tablename__ = "detections"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    mission_id: Mapped[int] = mapped_column(Integer, ForeignKey("missions.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime)
    position_lat: Mapped[float] = mapped_column(Float)
    position_lng: Mapped[float] = mapped_column(Float)
    position_altitude: Mapped[float] = mapped_column(Float)
    confidence: Mapped[str] = mapped_column(String)
    source: Mapped[str] = mapped_column(String)
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    rgb_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    mission: Mapped["Mission"] = relationship(back_populates="detections")


class GridCell(Base):
    __tablename__ = "grid_cells"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mission_id: Mapped[int] = mapped_column(Integer, ForeignKey("missions.id"))
    row: Mapped[int] = mapped_column(Integer)
    col: Mapped[int] = mapped_column(Integer)
    cell_lat: Mapped[float] = mapped_column(Float)
    cell_lng: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String)
    explored_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    mission: Mapped["Mission"] = relationship(back_populates="grid_cells")
