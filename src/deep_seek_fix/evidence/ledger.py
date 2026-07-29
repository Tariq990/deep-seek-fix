from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from deep_seek_fix.evidence.models import EvidenceRecord


class Base(DeclarativeBase):
    pass


class EvidenceRow(Base):
    __tablename__ = "evidence_records"

    sequence: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evidence_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False)


class EvidenceLedger:
    def __init__(self, database_url: str) -> None:
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)

    @classmethod
    def from_path(cls, path: Path) -> EvidenceLedger:
        path.parent.mkdir(parents=True, exist_ok=True)
        return cls(f"sqlite:///{path.as_posix()}")

    def append(self, record: EvidenceRecord) -> None:
        with Session(self.engine) as session:
            existing = session.scalars(
                select(EvidenceRow).where(EvidenceRow.evidence_id == record.evidence_id)
            ).first()
            if existing is not None:
                raise ValueError(f"evidence already exists: {record.evidence_id}")
            row = EvidenceRow(
                evidence_id=record.evidence_id,
                payload=json.dumps(record.model_dump(mode="json"), sort_keys=True),
            )
            session.add(row)
            session.commit()

    def get(self, evidence_id: str) -> EvidenceRecord:
        with Session(self.engine) as session:
            row = session.scalars(
                select(EvidenceRow).where(EvidenceRow.evidence_id == evidence_id)
            ).first()
            if row is None:
                raise KeyError(evidence_id)
            return EvidenceRecord.model_validate_json(row.payload)

    def list(self, run_id: str | None = None) -> list[EvidenceRecord]:
        with Session(self.engine) as session:
            rows = session.scalars(select(EvidenceRow).order_by(EvidenceRow.sequence)).all()
        records = [EvidenceRecord.model_validate_json(row.payload) for row in rows]
        if run_id is not None:
            return [record for record in records if record.run_id == run_id]
        return records
