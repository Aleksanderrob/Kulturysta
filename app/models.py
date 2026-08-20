"""Shared, serializable domain models."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field, replace
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4


class QualityFlag(str, Enum):
    NO_CONNECTION = "brak_polaczenia"
    DATA_GAP = "przerwa_w_danych"
    STEP_OFF = "zejscie_z_platformy"
    LOW_LOAD = "obciazenie_ponizej_progu"
    MASS_JUMP = "nagly_skok_masy"
    COP_JUMP = "nagly_skok_cop"
    INVALID_VALUE = "nan_lub_inf"
    TOO_SHORT = "zbyt_krotki_pomiar"
    SENSOR_MISSING = "brak_danych_czujnika"
    SAMPLE_RATE_VARIATION = "duze_wahania_probkowania"
    STREAM_STOPPED = "zatrzymanie_strumienia"
    STOPPED_EARLY = "przerwano_przed_czasem"


class QualityRating(str, Enum):
    VALID = "poprawna"
    WARNING = "poprawna_z_ostrzezeniami"
    INVALID = "niewazna"


@dataclass(slots=True)
class BoardSample:
    """A backend-independent board sample.

    COP values keep the unit declared by ``cop_unit``. Missing hardware values stay ``None``.
    """

    timestamp_monotonic: float
    timestamp_wall: str
    top_left: float | None
    top_right: float | None
    bottom_left: float | None
    bottom_right: float | None
    total_weight_kg: float | None
    cop_x: float | None
    cop_y: float | None
    sequence_number: int
    connection_ok: bool = True
    quality_flags: tuple[QualityFlag, ...] = ()
    cop_unit: str = "normalized"
    synthetic_data: bool = False
    filtered_cop_x: float | None = None
    filtered_cop_y: float | None = None
    raw_total_weight_kg: float | None = None
    raw_cop_x: float | None = None
    raw_cop_y: float | None = None

    def with_flags(self, *flags: QualityFlag) -> BoardSample:
        return replace(self, quality_flags=tuple(dict.fromkeys((*self.quality_flags, *flags))))

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["quality_flags"] = [flag.value for flag in self.quality_flags]
        return result


@dataclass(slots=True)
class Participant:
    first_name: str = ""
    last_name: str = ""
    age: int | None = None
    birth_date: str | None = None
    sex: str | None = None
    height_cm: float | None = None
    body_mass_kg: float | None = None
    participant_id: str = field(default_factory=lambda: f"P-{uuid4().hex[:8].upper()}")
    notes: str = ""
    identifier_only: bool = False

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.age is not None and not 1 <= self.age <= 120:
            errors.append("Wiek musi mieścić się w zakresie 1–120 lat.")
        if self.height_cm is not None and not 30 <= self.height_cm <= 250:
            errors.append("Wzrost musi mieścić się w zakresie 30–250 cm.")
        if self.body_mass_kg is not None and not 1 <= self.body_mass_kg <= 300:
            errors.append("Masa musi mieścić się w zakresie 1–300 kg.")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", self.participant_id):
            errors.append("Identyfikator może zawierać tylko litery, cyfry, '-' i '_'.")
        if not self.identifier_only and (not self.first_name.strip() or not self.last_name.strip()):
            errors.append("Podaj imię i nazwisko albo wybierz tryb samego identyfikatora.")
        return errors

    @property
    def safe_id(self) -> str:
        return re.sub(r"[^A-Za-z0-9_-]", "_", self.participant_id)[:64]

    def to_dict(self, include_personal_data: bool = True) -> dict[str, Any]:
        data = asdict(self)
        if not include_personal_data or self.identifier_only:
            data.update(first_name="", last_name="", birth_date=None, notes="")
        return data


@dataclass(slots=True)
class FilterSettings:
    kind: str = "moving_average"
    moving_average_window: int = 5
    order: int = 4
    cutoff_hz: float = 5.0
    sample_rate_hz: float | None = None


@dataclass(slots=True)
class CalibrationSettings:
    applied: bool = False
    calibration_type: str = "none"
    mass_offset_kg: float = 0.0
    cop_x_offset: float = 0.0
    cop_y_offset: float = 0.0
    reference_mass_kg: float | None = None
    scale_factor: float = 1.0
    performed_at: str | None = None


@dataclass(slots=True)
class SessionConfig:
    mode: str = "measurement"
    duration_s: float = 30.0
    protocol: str = "Stanie swobodne, oczy otwarte"
    repetitions: int = 1
    break_s: float = 15.0
    eyes: str = "otwarte"
    foot_position: str = "swobodna"
    note: str = ""
    target_x: float = 0.0
    target_y: float = 0.0
    target_radius: float = 0.15
    cop_unit: str = "normalized"
    filter_settings: FilterSettings = field(default_factory=FilterSettings)


@dataclass(slots=True)
class SessionMetadata:
    participant: Participant
    config: SessionConfig
    backend: str
    session_uuid: str = field(default_factory=lambda: str(uuid4()))
    session_id: str = ""
    started_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    finished_at: str | None = None
    synthetic_data: bool = False
    calibration: CalibrationSettings = field(default_factory=CalibrationSettings)
    app_version: str = "0.1.0"
    quality_rating: QualityRating = QualityRating.INVALID
    quality_flags: list[QualityFlag] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.session_id:
            stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
            self.session_id = f"{self.participant.safe_id}-{stamp}-{self.session_uuid[:8]}"

    def to_dict(self, include_personal_data: bool = True) -> dict[str, Any]:
        data = asdict(self)
        data["participant"] = self.participant.to_dict(include_personal_data)
        data["quality_rating"] = self.quality_rating.value
        data["quality_flags"] = [flag.value for flag in self.quality_flags]
        return data


@dataclass(slots=True)
class SessionArtifacts:
    session_dir: Path
    csv_path: Path
    xlsx_path: Path
    json_path: Path
    markdown_path: Path
    pdf_path: Path | None = None
