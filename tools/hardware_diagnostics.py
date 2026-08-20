"""Interactive, read-only diagnostics for a physical Wii Balance Board."""

from __future__ import annotations

import argparse
import json
import logging
import statistics
import sys
from itertools import pairwise
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.logging_config import configure_logging
from app.models import BoardSample
from hardware.wii_board_adapter import WiiBoardAdapter

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Diagnostyka lokalnego wbb-module i Wii Balance Board"
    )
    parser.add_argument("--samples", type=int, default=100, help="liczba próbek do zebrania")
    parser.add_argument(
        "--cop-unit", default="unknown", help="jednostka COP potwierdzona w dokumentacji sterownika"
    )
    parser.add_argument("--interactive", action="store_true", help="wyświetl checklistę wychyleń")
    return parser.parse_args()


def _summary(samples: list[BoardSample]) -> dict[str, float | int | None]:
    def mean(name: str) -> float | None:
        values = [getattr(sample, name) for sample in samples]
        finite = [float(value) for value in values if value is not None]
        return statistics.fmean(finite) if finite else None

    return {
        "sample_count": len(samples),
        "mean_weight_kg": mean("total_weight_kg"),
        "mean_cop_x": mean("cop_x"),
        "mean_cop_y": mean("cop_y"),
        "complete_sensor_samples": sum(
            None not in (sample.top_left, sample.top_right, sample.bottom_left, sample.bottom_right)
            for sample in samples
        ),
    }


def _interactive_phases(
    board: WiiBoardAdapter, samples_per_phase: int
) -> tuple[list[BoardSample], dict[str, dict[str, float | int | None]]]:
    phases = [
        ("center", "Stań stabilnie na środku"),
        ("left", "Przenieś ciężar w LEWO"),
        ("right", "Przenieś ciężar w PRAWO"),
        ("front", "Przenieś ciężar w PRZÓD"),
        ("back", "Przenieś ciężar w TYŁ"),
        ("step_off", "Zejdź z platformy z asekuracją"),
    ]
    all_samples: list[BoardSample] = []
    summaries: dict[str, dict[str, float | int | None]] = {}
    for key, instruction in phases:
        input(f"\n{instruction}. Naciśnij Enter, gdy pozycja jest gotowa…")
        phase_samples = [board.get_sample() for _ in range(samples_per_phase)]
        all_samples.extend(phase_samples)
        summaries[key] = _summary(phase_samples)
        print(key, summaries[key])
    return all_samples, summaries


def _direction_checks(
    summaries: dict[str, dict[str, float | int | None]], minimum_load_kg: float = 5.0
) -> dict[str, bool]:
    center = summaries["center"]
    cx, cy = center["mean_cop_x"], center["mean_cop_y"]
    if not isinstance(cx, float) or not isinstance(cy, float):
        return {"cop_available": False}
    return {
        "cop_available": True,
        "left_direction": float(summaries["left"]["mean_cop_x"] or cx) < cx,
        "right_direction": float(summaries["right"]["mean_cop_x"] or cx) > cx,
        "front_direction": float(summaries["front"]["mean_cop_y"] or cy) > cy,
        "back_direction": float(summaries["back"]["mean_cop_y"] or cy) < cy,
        "step_off_detected": float(summaries["step_off"]["mean_weight_kg"] or 0.0)
        < minimum_load_kg,
    }


def main() -> int:
    args = parse_args()
    log_path = Path("data/logs/hardware_diagnostics.log")
    configure_logging(log_path)
    print(f"Log: {log_path.resolve()}")
    try:
        facts = WiiBoardAdapter.inspect_installed_api()
        print("API wbb-module:")
        print(json.dumps(facts, ensure_ascii=False, indent=2))
    except Exception as exc:
        logger.exception("Brak importu wbb")
        print(f"BŁĄD: nie można zaimportować lub sprawdzić wbb-module: {exc}", file=sys.stderr)
        return 2
    board = WiiBoardAdapter(cop_unit=args.cop_unit)
    samples: list[BoardSample] = []
    phase_summaries: dict[str, dict[str, float | int | None]] = {}
    try:
        print("Łączenie z platformą…")
        board.connect(timeout_s=10.0)
        print("Połączono. Dane urządzenia:", board.get_device_info())
        board.start_stream()
        if args.interactive:
            samples, phase_summaries = _interactive_phases(board, max(10, args.samples // 6))
        else:
            for index in range(args.samples):
                sample = board.get_sample()
                samples.append(sample)
                if index % max(1, args.samples // 10) == 0:
                    print(
                        f"{index + 1:4d}: masa={sample.total_weight_kg!r} "
                        f"COP=({sample.cop_x!r}, {sample.cop_y!r}) "
                        f"czujniki={(sample.top_left, sample.top_right, sample.bottom_left, sample.bottom_right)}"
                    )
    except Exception as exc:
        logger.exception("Diagnostyka przerwana")
        print(f"BŁĄD: {exc}", file=sys.stderr)
        return 3
    finally:
        try:
            board.disconnect()
        except Exception:
            logger.exception("Błąd rozłączania po diagnostyce")
    if len(samples) > 1:
        intervals = [
            b.timestamp_monotonic - a.timestamp_monotonic
            for a, b in pairwise(samples)
            if b.timestamp_monotonic > a.timestamp_monotonic
        ]
        if intervals:
            print(
                f"Częstotliwość średnia: {1 / statistics.fmean(intervals):.2f} Hz; odchylenie odstępów: {statistics.pstdev(intervals):.4f} s"
            )
    if args.interactive:
        checks = _direction_checks(phase_summaries)
        summary_path = Path("data/logs/hardware_diagnostics_summary.json")
        summary_path.write_text(
            json.dumps(
                {"phases": phase_summaries, "checks": checks, "cop_unit": args.cop_unit},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print("Kontrole kierunków:", checks)
        print("Podsumowanie:", summary_path.resolve())
    print(
        "Diagnostyka programowa zakończona. Kierunki COP należy potwierdzić według MANUAL_TEST_CHECKLIST.md."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
