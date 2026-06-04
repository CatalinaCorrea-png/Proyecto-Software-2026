import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import db.models  # noqa: registra los modelos con Base antes de create_all
from db.database import Base
from db.models import Mission, Detection, GridCell


@pytest.fixture
def db_session(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path}/test.db",
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def _make_mission(**kwargs) -> Mission:
    defaults = dict(
        name="Misión de prueba",
        status="completed",
        grid_rows=5,
        grid_cols=5,
        grid_center_lat=-33.0,
        grid_center_lng=-71.0,
    )
    defaults.update(kwargs)
    return Mission(**defaults)


# Verifica que una misión creada con valores mínimos reciba los defaults
# correctos: batería inicial al 100%, detecciones en 0 y status asignado
def test_mission_default_values(db_session):
    m = _make_mission()
    db_session.add(m)
    db_session.commit()
    db_session.refresh(m)
    assert m.id is not None
    assert m.initial_battery == 100.0
    assert m.detections_count == 0
    assert m.status == "completed"


# Verifica que borrar una misión elimine en cascada todas sus detecciones,
# para no dejar filas huérfanas en la tabla detections
def test_delete_mission_cascades_to_detections(db_session):
    m = _make_mission()
    db_session.add(m)
    db_session.flush()
    d = Detection(
        id="det-001",
        mission_id=m.id,
        timestamp=datetime.now(timezone.utc),
        position_lat=-33.0,
        position_lng=-71.0,
        position_altitude=25.0,
        confidence="high",
        source="fusion",
    )
    db_session.add(d)
    db_session.commit()
    assert db_session.query(Detection).count() == 1

    db_session.delete(m)
    db_session.commit()
    assert db_session.query(Detection).count() == 0


# Verifica que borrar una misión elimine en cascada todas sus celdas del grid,
# para no dejar filas huérfanas en la tabla grid_cells
def test_delete_mission_cascades_to_grid_cells(db_session):
    m = _make_mission()
    db_session.add(m)
    db_session.flush()
    cell = GridCell(
        mission_id=m.id, row=0, col=0,
        cell_lat=-33.0, cell_lng=-71.0,
        status="unexplored",
    )
    db_session.add(cell)
    db_session.commit()
    assert db_session.query(GridCell).count() == 1

    db_session.delete(m)
    db_session.commit()
    assert db_session.query(GridCell).count() == 0


# Verifica que la relación Detection → Mission funcione en ambas direcciones:
# se puede acceder a d.mission y a m.detections
def test_detection_bidirectional_relationship(db_session):
    m = _make_mission()
    db_session.add(m)
    db_session.flush()
    d = Detection(
        id="det-002",
        mission_id=m.id,
        timestamp=datetime.now(timezone.utc),
        position_lat=-33.1,
        position_lng=-71.1,
        position_altitude=20.0,
        confidence="medium",
        source="rgb",
    )
    db_session.add(d)
    db_session.commit()
    assert d.mission.id == m.id
    assert len(m.detections) == 1


# Verifica que Detection almacene correctamente valores opcionales nulos
# (temperature y rgb_confidence pueden ser None para detecciones solo RGB)
def test_detection_optional_fields_can_be_null(db_session):
    m = _make_mission()
    db_session.add(m)
    db_session.flush()
    d = Detection(
        id="det-003",
        mission_id=m.id,
        timestamp=datetime.now(timezone.utc),
        position_lat=-33.0,
        position_lng=-71.0,
        position_altitude=25.0,
        confidence="medium",
        source="rgb",
        temperature=None,
        rgb_confidence=None,
    )
    db_session.add(d)
    db_session.commit()
    assert d.temperature is None
    assert d.rgb_confidence is None


# Verifica que varias misiones coexistan en la base de datos sin interferirse
def test_multiple_missions_are_independent(db_session):
    m1 = _make_mission(name="M1")
    m2 = _make_mission(name="M2")
    db_session.add_all([m1, m2])
    db_session.commit()
    assert db_session.query(Mission).count() == 2
    assert db_session.query(Mission).filter_by(name="M1").first() is not None
    assert db_session.query(Mission).filter_by(name="M2").first() is not None
