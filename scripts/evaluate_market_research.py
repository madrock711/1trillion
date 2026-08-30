#!/usr/bin/env python3
"""Validate and score sealed KOSPI forecast contracts.

Forecasts and outcomes deliberately live in separate files.  This keeps a
post-close review from silently rewriting what was known before the close.
The script has no network dependency; it only evaluates records that another
step has already sourced and sealed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, time, timezone, timedelta
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVALUATION_ROOT = ROOT / "research" / "evaluation"
SEOUL = timezone(timedelta(hours=9), name="KST")
SCENARIOS = ("bull", "base", "bear")
CLOSE_ENVELOPE_COVERAGE = 0.90
PATH_ENVELOPE_COVERAGE = 0.90
MAX_DATA_LAG_MINUTES = 20.0
MAX_POSTCLOSE_DATA_LAG_MINUTES = 30.0
MAX_PUBLICATION_LAG_MINUTES = 5.0
MAX_DEPLOY_VERIFY_LAG_MINUTES = 10.0
MAX_LIVE_REFERENCE_LAG_MINUTES = 5.0
MIN_INTRADAY_PATH_COVERAGE_RATE = 0.90
MIN_ACTIVE_LIFT_BPS = 10.0
MIN_ACTIVE_SUPPORT_RATE = 0.60
MIN_ACTIVE_REGIME_SESSIONS = 5
HYPOTHESIS_REGIMES = {"risk_on", "risk_off", "mixed", "event_shock"}
BASELINE_IDS = {"reference_carry"}
TRIGGER_OPERATORS = {"gt", "gte", "lt", "lte", "between", "outside"}
TRIGGER_METRICS = {
    "kospi_price": "지수",
    "kodex_price": "원",
    "samsung_price": "원",
    "sk_hynix_price": "원",
    "usdkrw": "원",
    "foreign_cash": "억원",
    "institution_cash": "억원",
    "program_total": "억원",
    "program_non_arbitrage": "억원",
    "foreign_kospi200_futures": "계약",
    "breadth_up_ratio": "%",
}
MARKET_STATES = {"preopen", "intraday", "postclose"}
VISIBILITIES = {"public", "internal"}
PATH_SOURCE_STATUSES = {"unavailable", "incomplete", "invalid"}
FLOW_TRAJECTORY_CONTRACT = "flow_trajectory_v1"
FLOW_ANCHORS = ("open30", "open60", "at1400", "close")
FLOW_ANCHOR_TIMES = {
    "open30": time(9, 30),
    "open60": time(10, 0),
    "at1400": time(14, 0),
    "close": time(15, 30),
}
FLOW_METRICS = ("foreignCash", "programNonArbitrage", "programTotal")
FLOW_PROMOTION_RECENT_SESSIONS = 20
FLOW_HYPOTHESIS_IDS = {
    "domestic-flow-persistence",
    "late-session-flow-acceleration",
}
EVALUATION_BUCKETS = {
    "preopen",
    "open_0900_0930",
    "morning_0931_1130",
    "afternoon_1131_1500",
    "closing_1501_1529",
    "postclose",
}
FLOW_HYPOTHESIS_CONTRACTS = {
    "domestic-flow-persistence": {
        "evaluationBuckets": ("morning_0931_1130",),
        "eligibleFromTime": "10:00",
        "predictorVersion": "domestic-flow-persistence-v1",
        "requiredInputAnchors": ("open30", "open60"),
        "requiredInputMetrics": FLOW_METRICS,
        "requiredOutcomeFeatures": (
            "foreignCash.persistence.open30.open60",
            "foreignCash.delta.open60.close",
            "programNonArbitrage.delta.open60.close",
            "programTotal.delta.open60.close",
        ),
    },
    "late-session-flow-acceleration": {
        "evaluationBuckets": ("afternoon_1131_1500", "closing_1501_1529"),
        "eligibleFromTime": "14:00",
        "predictorVersion": "late-session-flow-acceleration-v1",
        "requiredInputAnchors": ("at1400",),
        "requiredInputMetrics": FLOW_METRICS,
        "requiredOutcomeFeatures": (
            "foreignCash.delta.at1400.close",
            "foreignCash.persistence.at1400.close",
            "programNonArbitrage.delta.at1400.close",
            "programTotal.delta.at1400.close",
        ),
    },
}
FORBIDDEN_FORECAST_FIELDS = {
    "actual",
    "outcome",
    "realizedScenario",
    "errorCodes",
    "recordedAt",
    "pushAt",
    "deployVerifiedAt",
    "canonicalForAggregate",
}
ERROR_CODES = {
    "range_too_narrow_up",
    "range_too_narrow_down",
    "direction_wrong",
    "trigger_false_positive",
    "trigger_missed",
    "domestic_flow_underweighted",
    "external_signal_overweighted",
    "late_session_reversal_missed",
    "data_stale",
    "nonindependent_revision",
    "cause_unverifiable",
}


class ValidationError(ValueError):
    """Raised when an evaluation record violates the forecast contract."""


def parse_iso(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise ValidationError(f"{field} must be an ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValidationError(f"{field} is not a valid ISO-8601 timestamp") from error
    if parsed.tzinfo is None:
        raise ValidationError(f"{field} must include a UTC offset")
    return parsed


def require_number(value: Any, field: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result) or (positive and result <= 0):
        raise ValidationError(f"{field} is outside the allowed range")
    return result


def require_nonnegative_integer(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValidationError(f"{field} must be a non-negative integer")
    return value


def validate_raw_hash(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValidationError(f"{field} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as error:
        raise ValidationError(f"{field} is not hexadecimal") from error
    return value


def canonical_forecast_content_hash(payload: dict[str, Any]) -> str:
    """Hash only the sealed forecast contract, excluding its self-hash."""
    canonical_payload = {
        key: value for key, value in payload.items() if key != "contentHash"
    }
    canonical = json.dumps(
        canonical_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def canonical_object_hash(
    payload: dict[str, Any], *, excluded_keys: set[str] | None = None
) -> str:
    """Return a deterministic hash for a small sealed evidence object."""
    excluded = {"canonicalHash"} if excluded_keys is None else excluded_keys
    canonical_payload = {
        key: value for key, value in payload.items() if key not in excluded
    }
    canonical = json.dumps(
        canonical_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def validate_commit_sha(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) != 40:
        raise ValidationError(f"{field} must be a 40-character Git commit SHA")
    try:
        int(value, 16)
    except ValueError as error:
        raise ValidationError(f"{field} is not hexadecimal") from error
    return value.lower()


def validate_forecast_at_commit(
    repo_root: Path | None,
    forecast: dict[str, Any],
    commit_sha: str,
) -> None:
    """Fail closed when a real repository cannot reproduce the pushed contract."""
    if repo_root is None or not (repo_root / ".git").exists():
        return
    relative_path = forecast.get("forecastRelativePath")
    if not isinstance(relative_path, str) or not relative_path:
        raise ValidationError(
            f"{forecast['forecastId']}: forecast path is not anchored in the repository"
        )
    result = subprocess.run(
        ["git", "-C", str(repo_root), "show", f"{commit_sha}:{relative_path}"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        raise ValidationError(
            f"{forecast['forecastId']}: pushed commit does not contain {relative_path}"
        )
    try:
        committed_payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise ValidationError(
            f"{forecast['forecastId']}: pushed forecast contract is not valid JSON"
        ) from error
    if not isinstance(committed_payload, dict):
        raise ValidationError(
            f"{forecast['forecastId']}: pushed forecast contract is not an object"
        )
    committed_hash = canonical_forecast_content_hash(committed_payload)
    if (
        committed_payload.get("contentHash") != forecast["contentHash"]
        or committed_hash != forecast["contentHash"]
    ):
        raise ValidationError(
            f"{forecast['forecastId']}: pushed commit forecast differs from contentHash"
        )
    report_path = forecast.get("reportPath")
    if not isinstance(report_path, str) or not report_path:
        raise ValidationError(
            f"{forecast['forecastId']}: report path is not anchored in the repository"
        )
    report_result = subprocess.run(
        ["git", "-C", str(repo_root), "show", f"{commit_sha}:{report_path}"],
        capture_output=True,
        check=False,
    )
    if report_result.returncode != 0:
        raise ValidationError(
            f"{forecast['forecastId']}: pushed commit does not contain report {report_path}"
        )
    committed_report_hash = hashlib.sha256(report_result.stdout).hexdigest()
    if committed_report_hash != forecast["reportSha256"]:
        raise ValidationError(
            f"{forecast['forecastId']}: pushed commit report differs from reportSha256"
        )


def validate_close_source_metadata(
    payload: dict[str, Any],
    field: str,
    *,
    session_date: str,
    fetched_at: datetime,
) -> dict[str, Any]:
    as_of = parse_iso(payload.get("asOf"), f"{field}.asOf")
    local_as_of = as_of.astimezone(SEOUL)
    if local_as_of.strftime("%Y-%m-%d") != session_date or local_as_of.time() < time(15, 30):
        raise ValidationError(f"{field}.asOf must be a 15:30 KST or later close")
    if fetched_at < as_of:
        raise ValidationError(f"fetchedAt precedes {field}.asOf")
    source = payload.get("source")
    if not isinstance(source, str) or not source.strip():
        raise ValidationError(f"{field}.source is required")
    raw_hash = validate_raw_hash(payload.get("rawHash"), f"{field}.rawHash")
    return {"asOf": as_of, "source": source, "rawHash": raw_hash}


def expected_flow_anchor_at(session_date: str, anchor_name: str) -> datetime:
    session_day = datetime.strptime(session_date, "%Y-%m-%d").date()
    return datetime.combine(session_day, FLOW_ANCHOR_TIMES[anchor_name], tzinfo=SEOUL)


def validate_flow_anchor(
    payload: Any,
    anchor_name: str,
    *,
    session_date: str,
    fetched_at: datetime,
    field: str,
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValidationError(f"{field} must be an object")
    status = payload.get("status")
    expected_at = expected_flow_anchor_at(session_date, anchor_name)
    if status == "available":
        expected_fields = {
            "status",
            "asOf",
            *FLOW_METRICS,
            "source",
            "rawHash",
        }
        if set(payload) != expected_fields:
            raise ValidationError(
                f"{field} available fields must be {sorted(expected_fields)}"
            )
        as_of = parse_iso(payload.get("asOf"), f"{field}.asOf")
        if as_of != expected_at:
            raise ValidationError(
                f"{field}.asOf must equal {expected_at.isoformat()}"
            )
        if as_of > fetched_at:
            raise ValidationError(f"{field}.asOf is later than actual.fetchedAt")
        values = {
            metric: require_number(payload.get(metric), f"{field}.{metric}")
            for metric in FLOW_METRICS
        }
        source = payload.get("source")
        if not isinstance(source, str) or not source.strip():
            raise ValidationError(f"{field}.source is required")
        raw_hash = validate_raw_hash(payload.get("rawHash"), f"{field}.rawHash")
        return {
            "status": "available",
            "asOf": as_of,
            **values,
            "source": source,
            "rawHash": raw_hash,
        }
    if status == "missing":
        expected_fields = {
            "status",
            "expectedAsOf",
            "attemptedAt",
            "sourceStatus",
            "source",
            "missingReason",
            "rawHash",
        }
        if set(payload) != expected_fields:
            raise ValidationError(
                f"{field} missing fields must be {sorted(expected_fields)}"
            )
        expected_as_of = parse_iso(
            payload.get("expectedAsOf"), f"{field}.expectedAsOf"
        )
        attempted_at = parse_iso(payload.get("attemptedAt"), f"{field}.attemptedAt")
        if expected_as_of != expected_at:
            raise ValidationError(
                f"{field}.expectedAsOf must equal {expected_at.isoformat()}"
            )
        if attempted_at < expected_as_of or attempted_at > fetched_at:
            raise ValidationError(
                f"{field}.attemptedAt must be between expectedAsOf and actual.fetchedAt"
            )
        source_status = payload.get("sourceStatus")
        if source_status not in PATH_SOURCE_STATUSES:
            raise ValidationError(f"{field}.sourceStatus is invalid")
        source = payload.get("source")
        missing_reason = payload.get("missingReason")
        if not isinstance(source, str) or not source.strip():
            raise ValidationError(f"{field}.source is required")
        if not isinstance(missing_reason, str) or not missing_reason.strip():
            raise ValidationError(f"{field}.missingReason is required")
        raw_hash = validate_raw_hash(payload.get("rawHash"), f"{field}.rawHash")
        return {
            "status": "missing",
            "expectedAsOf": expected_as_of,
            "attemptedAt": attempted_at,
            "sourceStatus": source_status,
            "source": source,
            "missingReason": missing_reason,
            "rawHash": raw_hash,
        }
    raise ValidationError(f"{field}.status must be available or missing")


def derive_flow_features(anchors: dict[str, dict[str, Any]] | None) -> dict[str, Any]:
    features: dict[str, Any] = {}
    for start_index, start_name in enumerate(FLOW_ANCHORS):
        for end_name in FLOW_ANCHORS[start_index + 1 :]:
            start = None if anchors is None else anchors.get(start_name)
            end = None if anchors is None else anchors.get(end_name)
            for metric in FLOW_METRICS:
                delta_id = f"{metric}.delta.{start_name}.{end_name}"
                persistence_id = f"{metric}.persistence.{start_name}.{end_name}"
                if (
                    start is None
                    or end is None
                    or start.get("status") != "available"
                    or end.get("status") != "available"
                ):
                    features[delta_id] = None
                    features[persistence_id] = "unavailable"
                    continue
                start_value = float(start[metric])
                end_value = float(end[metric])
                features[delta_id] = end_value - start_value
                start_sign = sign(start_value)
                end_sign = sign(end_value)
                if start_sign != 0 and end_sign != 0 and start_sign != end_sign:
                    persistence = "reversal"
                elif abs(end_value) > abs(start_value):
                    persistence = "strengthening"
                elif abs(end_value) < abs(start_value):
                    persistence = "weakening"
                else:
                    persistence = "flat"
                features[persistence_id] = persistence
    return features


FLOW_FEATURE_IDS = frozenset(derive_flow_features(None))


def validate_flow_trajectory(
    payload: dict[str, Any],
    path: Path,
    *,
    session_date: str,
    fetched_at: datetime,
    close_snapshot: dict[str, Any] | None,
) -> tuple[dict[str, Any] | None, dict[str, Any], dict[str, Any] | None]:
    trajectory = payload.get("flowTrajectory")
    missing_evidence = payload.get("flowTrajectoryMissingEvidence")
    if trajectory is None:
        if close_snapshot is not None:
            raise ValidationError(
                f"{path}: flowTrajectory close must be archived when closeSnapshot exists"
            )
        expected_fields = {
            "sourceStatus",
            "source",
            "asOf",
            "fetchedAt",
            "missingReason",
            "rawHash",
        }
        if not isinstance(missing_evidence, dict) or set(missing_evidence) != expected_fields:
            raise ValidationError(
                f"{path}: missing flowTrajectory needs exact flowTrajectoryMissingEvidence"
            )
        source_status = missing_evidence.get("sourceStatus")
        if source_status not in PATH_SOURCE_STATUSES:
            raise ValidationError(f"{path}: flow trajectory sourceStatus is invalid")
        source = missing_evidence.get("source")
        missing_reason = missing_evidence.get("missingReason")
        if not isinstance(source, str) or not source.strip():
            raise ValidationError(f"{path}: flow trajectory missing source is required")
        if not isinstance(missing_reason, str) or not missing_reason.strip():
            raise ValidationError(f"{path}: flow trajectory missingReason is required")
        as_of = parse_iso(missing_evidence.get("asOf"), "flowTrajectoryMissingEvidence.asOf")
        evidence_fetched_at = parse_iso(
            missing_evidence.get("fetchedAt"), "flowTrajectoryMissingEvidence.fetchedAt"
        )
        expected_close = expected_flow_anchor_at(session_date, "close")
        if as_of != expected_close:
            raise ValidationError(
                f"{path}: flow trajectory missing asOf must equal the session close"
            )
        if evidence_fetched_at < as_of or evidence_fetched_at > fetched_at:
            raise ValidationError(
                f"{path}: flow trajectory missing fetchedAt must be between close and actual.fetchedAt"
            )
        raw_hash = validate_raw_hash(
            missing_evidence.get("rawHash"), "flowTrajectoryMissingEvidence.rawHash"
        )
        parsed_evidence = {
            "sourceStatus": source_status,
            "source": source,
            "asOf": as_of,
            "fetchedAt": evidence_fetched_at,
            "missingReason": missing_reason,
            "rawHash": raw_hash,
        }
        return None, derive_flow_features(None), parsed_evidence
    if missing_evidence is not None:
        raise ValidationError(
            f"{path}: available flowTrajectory cannot have flowTrajectoryMissingEvidence"
        )
    if not isinstance(trajectory, dict) or set(trajectory) != {
        "contract",
        "unit",
        "anchors",
    }:
        raise ValidationError(
            f"{path}: flowTrajectory must contain contract, unit, and anchors"
        )
    if trajectory.get("contract") != FLOW_TRAJECTORY_CONTRACT:
        raise ValidationError(f"{path}: unsupported flowTrajectory contract")
    if trajectory.get("unit") != "억원":
        raise ValidationError(f"{path}: flowTrajectory.unit must be 억원")
    anchors = trajectory.get("anchors")
    if not isinstance(anchors, dict) or set(anchors) != set(FLOW_ANCHORS):
        raise ValidationError(
            f"{path}: flowTrajectory.anchors must contain {list(FLOW_ANCHORS)}"
        )
    parsed_anchors = {
        anchor_name: validate_flow_anchor(
            anchors[anchor_name],
            anchor_name,
            session_date=session_date,
            fetched_at=fetched_at,
            field=f"flowTrajectory.anchors.{anchor_name}",
        )
        for anchor_name in FLOW_ANCHORS
    }
    if close_snapshot is not None:
        close_anchor = parsed_anchors["close"]
        if close_anchor["status"] != "available":
            raise ValidationError(
                f"{path}: flowTrajectory close must be available when closeSnapshot exists"
            )
        expected_close_values = {
            "foreignCash": close_snapshot["cashFlow"]["foreign"],
            "programNonArbitrage": close_snapshot["program"]["nonArbitrage"],
            "programTotal": close_snapshot["program"]["total"],
        }
        for metric, expected_value in expected_close_values.items():
            if not math.isclose(
                float(close_anchor[metric]), float(expected_value), abs_tol=1e-9
            ):
                raise ValidationError(
                    f"{path}: flowTrajectory close {metric} does not match closeSnapshot"
                )
    elif parsed_anchors["close"]["status"] != "missing":
        raise ValidationError(
            f"{path}: flowTrajectory close must be missing when closeSnapshot is missing"
        )
    return (
        {
            "contract": FLOW_TRAJECTORY_CONTRACT,
            "unit": "억원",
            "anchors": parsed_anchors,
        },
        derive_flow_features(parsed_anchors),
        None,
    )


def validate_predictor_inputs(
    row: dict[str, Any],
    hypothesis_id: str,
    *,
    data_cutoff_at: datetime,
    issued_at: datetime,
) -> tuple[str | None, dict[str, Any] | None, dict[str, Any] | None]:
    input_status = row.get("inputStatus")
    predictor_inputs = row.get("predictorInputs")
    missing_evidence = row.get("missingInputEvidence")
    if hypothesis_id not in FLOW_HYPOTHESIS_IDS:
        if any(
            key in row for key in ("inputStatus", "predictorInputs", "missingInputEvidence")
        ):
            raise ValidationError(
                f"hypothesis trial {hypothesis_id} cannot use flow predictor inputs"
            )
        return None, None, None
    if input_status == "available":
        if missing_evidence is not None:
            raise ValidationError(
                f"hypothesis trial {hypothesis_id} available input cannot have missing evidence"
            )
        if not isinstance(predictor_inputs, dict) or set(predictor_inputs) != {
            "asOf",
            "anchors",
            "canonicalHash",
        }:
            raise ValidationError(
                f"hypothesis trial {hypothesis_id} predictorInputs fields are invalid"
            )
        canonical_hash = validate_raw_hash(
            predictor_inputs.get("canonicalHash"),
            f"hypothesisTrials.{hypothesis_id}.predictorInputs.canonicalHash",
        )
        if canonical_hash != canonical_object_hash(
            predictor_inputs, excluded_keys={"canonicalHash"}
        ):
            raise ValidationError(
                f"hypothesis trial {hypothesis_id} predictorInputs canonicalHash changed"
            )
        as_of = parse_iso(
            predictor_inputs.get("asOf"),
            f"hypothesisTrials.{hypothesis_id}.predictorInputs.asOf",
        )
        if as_of > data_cutoff_at:
            raise ValidationError(
                f"hypothesis trial {hypothesis_id} predictorInputs.asOf exceeds dataCutoffAt"
            )
        anchors = predictor_inputs.get("anchors")
        if not isinstance(anchors, dict) or not anchors:
            raise ValidationError(
                f"hypothesis trial {hypothesis_id} predictorInputs.anchors is required"
            )
        parsed_anchors: dict[str, dict[str, Any]] = {}
        latest_anchor_at: datetime | None = None
        expected_anchor_fields = {"asOf", *FLOW_METRICS, "source", "rawHash"}
        for anchor_name, anchor in anchors.items():
            if anchor_name not in FLOW_ANCHORS or not isinstance(anchor, dict):
                raise ValidationError(
                    f"hypothesis trial {hypothesis_id} has an invalid predictor anchor"
                )
            if set(anchor) != expected_anchor_fields:
                raise ValidationError(
                    f"hypothesis trial {hypothesis_id} predictor anchor {anchor_name} fields are invalid"
                )
            anchor_as_of = parse_iso(
                anchor.get("asOf"),
                f"hypothesisTrials.{hypothesis_id}.predictorInputs.{anchor_name}.asOf",
            )
            expected_time = expected_flow_anchor_at(
                data_cutoff_at.astimezone(SEOUL).strftime("%Y-%m-%d"), anchor_name
            )
            if anchor_as_of != expected_time or anchor_as_of > data_cutoff_at:
                raise ValidationError(
                    f"hypothesis trial {hypothesis_id} predictor anchor {anchor_name} has an invalid asOf"
                )
            values = {
                metric: require_number(
                    anchor.get(metric),
                    f"hypothesisTrials.{hypothesis_id}.predictorInputs.{anchor_name}.{metric}",
                )
                for metric in FLOW_METRICS
            }
            source = anchor.get("source")
            if not isinstance(source, str) or not source.strip():
                raise ValidationError(
                    f"hypothesis trial {hypothesis_id} predictor anchor source is required"
                )
            raw_hash = validate_raw_hash(
                anchor.get("rawHash"),
                f"hypothesisTrials.{hypothesis_id}.predictorInputs.{anchor_name}.rawHash",
            )
            parsed_anchors[anchor_name] = {
                "asOf": anchor_as_of,
                **values,
                "source": source,
                "rawHash": raw_hash,
            }
            latest_anchor_at = (
                anchor_as_of
                if latest_anchor_at is None or anchor_as_of > latest_anchor_at
                else latest_anchor_at
            )
        if as_of != latest_anchor_at:
            raise ValidationError(
                f"hypothesis trial {hypothesis_id} predictorInputs.asOf must equal its latest anchor"
            )
        return (
            "available",
            {
                "asOf": as_of,
                "anchors": parsed_anchors,
                "canonicalHash": canonical_hash,
            },
            None,
        )
    if input_status == "missing":
        if predictor_inputs is not None:
            raise ValidationError(
                f"hypothesis trial {hypothesis_id} missing input cannot contain predictorInputs"
            )
        expected_fields = {"sourceStatus", "source", "asOf", "fetchedAt", "rawHash"}
        if not isinstance(missing_evidence, dict) or set(missing_evidence) != expected_fields:
            raise ValidationError(
                f"hypothesis trial {hypothesis_id} missing input needs exact missingInputEvidence"
            )
        source_status = missing_evidence.get("sourceStatus")
        if source_status not in PATH_SOURCE_STATUSES:
            raise ValidationError(
                f"hypothesis trial {hypothesis_id} missing sourceStatus is invalid"
            )
        source = missing_evidence.get("source")
        if not isinstance(source, str) or not source.strip():
            raise ValidationError(
                f"hypothesis trial {hypothesis_id} missing source is required"
            )
        as_of = parse_iso(
            missing_evidence.get("asOf"),
            f"hypothesisTrials.{hypothesis_id}.missingInputEvidence.asOf",
        )
        evidence_fetched_at = parse_iso(
            missing_evidence.get("fetchedAt"),
            f"hypothesisTrials.{hypothesis_id}.missingInputEvidence.fetchedAt",
        )
        if as_of > data_cutoff_at or evidence_fetched_at < as_of or evidence_fetched_at > issued_at:
            raise ValidationError(
                f"hypothesis trial {hypothesis_id} missing input timestamps are invalid"
            )
        raw_hash = validate_raw_hash(
            missing_evidence.get("rawHash"),
            f"hypothesisTrials.{hypothesis_id}.missingInputEvidence.rawHash",
        )
        return (
            "missing",
            None,
            {
                "sourceStatus": source_status,
                "source": source,
                "asOf": as_of,
                "fetchedAt": evidence_fetched_at,
                "rawHash": raw_hash,
            },
        )
    raise ValidationError(
        f"hypothesis trial {hypothesis_id} inputStatus must be available or missing"
    )


def compare_predictor_inputs(
    trial: dict[str, Any], actual_flow: dict[str, Any] | None
) -> str:
    if trial.get("predictorInputStatus") == "missing":
        return "missing_input"
    predictor_inputs = trial.get("predictorInputsParsed")
    if predictor_inputs is None:
        return "verified"
    if actual_flow is None:
        return "missing_actual"
    actual_anchors = actual_flow["anchors"]
    for anchor_name, predictor_anchor in predictor_inputs["anchors"].items():
        actual_anchor = actual_anchors.get(anchor_name)
        if actual_anchor is None or actual_anchor.get("status") != "available":
            return "missing_actual"
        if (
            actual_anchor["asOf"] != predictor_anchor["asOf"]
            or actual_anchor["source"] != predictor_anchor["source"]
            or actual_anchor["rawHash"] != predictor_anchor["rawHash"]
        ):
            return "input_mismatch"
        if any(
            not math.isclose(
                float(actual_anchor[metric]),
                float(predictor_anchor[metric]),
                abs_tol=1e-9,
            )
            for metric in FLOW_METRICS
        ):
            return "input_mismatch"
    return "verified"


def validate_trigger_threshold(value: Any, operator: str, field: str) -> float | list[float]:
    if operator in {"between", "outside"}:
        if not isinstance(value, list) or len(value) != 2:
            raise ValidationError(f"{field} must contain [low, high]")
        low = require_number(value[0], f"{field}[0]")
        high = require_number(value[1], f"{field}[1]")
        if low > high:
            raise ValidationError(f"{field} low exceeds high")
        return [low, high]
    return require_number(value, field)


def trigger_condition_observed(
    value: float, operator: str, threshold: float | list[float]
) -> bool:
    if operator == "gt":
        return value > float(threshold)
    if operator == "gte":
        return value >= float(threshold)
    if operator == "lt":
        return value < float(threshold)
    if operator == "lte":
        return value <= float(threshold)
    low, high = threshold
    if operator == "between":
        return low <= value <= high
    return value < low or value > high


def aggregate_trigger_status(logic: str, statuses: list[str]) -> str:
    """Return observed/not_observed/unavailable for one sealed scenario rule."""
    if logic == "AND":
        if "not_observed" in statuses:
            return "not_observed"
        if all(status == "observed" for status in statuses):
            return "observed"
        return "unavailable"
    if "observed" in statuses:
        return "observed"
    if all(status == "not_observed" for status in statuses):
        return "not_observed"
    return "unavailable"


def expected_bucket(issued_at: datetime, session_day: Any) -> tuple[str, str]:
    local = issued_at.astimezone(SEOUL)
    if local.date() > session_day:
        raise ValidationError("issuedAt is later than target.sessionDate")
    if local.date() < session_day:
        if local.time() >= time(15, 30):
            return "postclose", "postclose"
        return "preopen", "preopen"
    local_time = local.time()
    if local_time < time(9, 0):
        return "preopen", "preopen"
    if local_time <= time(9, 30):
        return "open_0900_0930", "intraday"
    if local_time <= time(11, 30):
        return "morning_0931_1130", "intraday"
    if local_time <= time(15, 0):
        return "afternoon_1131_1500", "intraday"
    return "closing_1501_1529", "intraday"


def load_json_files(directory: Path) -> list[tuple[Path, dict[str, Any]]]:
    if not directory.exists():
        return []
    records: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(directory.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValidationError(f"cannot read {path}: {error}") from error
        if not isinstance(payload, dict):
            raise ValidationError(f"{path} must contain one JSON object")
        records.append((path, payload))
    return records


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValidationError(f"cannot read {path}:{line_number}: {error}") from error
        if not isinstance(payload, dict):
            raise ValidationError(f"{path}:{line_number} must contain one JSON object")
        records.append(payload)
    return records


def load_trading_session_sequence(path: Path) -> list[str]:
    if not path.is_file():
        raise ValidationError(f"{path}: trading session sequence is required")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValidationError(f"cannot read {path}: {error}") from error
    if not isinstance(payload, dict) or payload.get("schemaVersion") != 1:
        raise ValidationError(f"{path}: invalid trading session sequence")
    sessions = payload.get("sessions")
    if not isinstance(sessions, list) or len(sessions) < 2:
        raise ValidationError(f"{path}: sessions must contain at least two trading dates")
    parsed_sessions: list[str] = []
    for value in sessions:
        try:
            parsed = datetime.strptime(str(value), "%Y-%m-%d").date()
        except ValueError as error:
            raise ValidationError(f"{path}: invalid trading session date {value}") from error
        parsed_sessions.append(parsed.isoformat())
    if parsed_sessions != sorted(set(parsed_sessions)):
        raise ValidationError(f"{path}: sessions must be unique and strictly increasing")
    if not isinstance(payload.get("source"), str) or not payload["source"].strip():
        raise ValidationError(f"{path}: source is required")
    parse_iso(payload.get("asOf"), f"{path}.asOf")
    validate_raw_hash(payload.get("rawHash"), f"{path}.rawHash")
    return parsed_sessions


def validate_forecast_session_sequence(
    forecasts: Iterable[dict[str, Any]], sessions: list[str]
) -> None:
    session_index = {session_date: index for index, session_date in enumerate(sessions)}
    for forecast in forecasts:
        target_date = forecast["sessionDate"]
        index = session_index.get(target_date)
        if index is None or index == 0:
            raise ValidationError(
                f"{forecast['forecastId']}: target session is missing from the trading sequence"
            )
        expected_previous = sessions[index - 1]
        declared_previous = forecast["target"].get("previousSessionDate")
        if declared_previous != expected_previous:
            raise ValidationError(
                f"{forecast['forecastId']}: target.previousSessionDate is "
                f"{declared_previous}, expected {expected_previous} from the trading sequence"
            )


def validate_scenarios(payload: Any) -> dict[str, dict[str, float]]:
    if not isinstance(payload, dict) or set(payload) != set(SCENARIOS):
        raise ValidationError("scenarios must contain bull, base, and bear")
    result: dict[str, dict[str, float]] = {}
    probability_total = 0.0
    for name in SCENARIOS:
        row = payload[name]
        if not isinstance(row, dict):
            raise ValidationError(f"scenarios.{name} must be an object")
        low = require_number(row.get("low"), f"scenarios.{name}.low", positive=True)
        high = require_number(row.get("high"), f"scenarios.{name}.high", positive=True)
        probability = require_number(row.get("probability"), f"scenarios.{name}.probability")
        if low > high:
            raise ValidationError(f"scenarios.{name} has low greater than high")
        if probability < 0 or probability > 1:
            raise ValidationError(f"scenarios.{name}.probability must be between 0 and 1")
        result[name] = {"low": low, "high": high, "probability": probability}
        probability_total += probability
    if not math.isclose(probability_total, 1.0, abs_tol=1e-9):
        raise ValidationError("scenario probabilities must sum to 1")
    if result["bear"]["high"] > result["base"]["low"]:
        raise ValidationError("bear and base ranges overlap")
    if result["base"]["high"] > result["bull"]["low"]:
        raise ValidationError("base and bull ranges overlap")
    if not math.isclose(result["bear"]["high"], result["base"]["low"], abs_tol=1e-9):
        raise ValidationError("bear and base ranges must share one boundary")
    if not math.isclose(result["base"]["high"], result["bull"]["low"], abs_tol=1e-9):
        raise ValidationError("base and bull ranges must share one boundary")
    return result


def validate_drivers(payload: Any) -> tuple[list[dict[str, Any]], set[str]]:
    if not isinstance(payload, list) or not 2 <= len(payload) <= 4:
        raise ValidationError("drivers must contain 2 to 4 ranked items")
    result: list[dict[str, Any]] = []
    ids: set[str] = set()
    for index, row in enumerate(payload, start=1):
        if not isinstance(row, dict):
            raise ValidationError("each driver must be an object")
        driver_id = row.get("id")
        if not isinstance(driver_id, str) or not driver_id.strip() or driver_id in ids:
            raise ValidationError("driver ids must be unique non-empty strings")
        if row.get("rank") != index:
            raise ValidationError("driver ranks must be consecutive and match list order")
        for field in ("claim", "validationMetric"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                raise ValidationError(f"drivers.{driver_id}.{field} is required")
        ids.add(driver_id)
        result.append(row)
    return result, ids


def validate_scenario_triggers(
    payload: Any,
    *,
    issued_at: datetime,
    session_close: datetime,
) -> tuple[
    dict[str, Any],
    set[str],
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
]:
    if not isinstance(payload, dict) or set(payload) != set(SCENARIOS):
        raise ValidationError("scenarioTriggers must contain bull, base, and bear")
    trigger_ids: set[str] = set()
    parsed_conditions: dict[str, dict[str, Any]] = {}
    parsed_scenarios: dict[str, dict[str, Any]] = {}
    for scenario in SCENARIOS:
        row = payload[scenario]
        if not isinstance(row, dict) or row.get("logic") not in {"AND", "OR"}:
            raise ValidationError(f"scenarioTriggers.{scenario}.logic must be AND or OR")
        observe_by = parse_iso(row.get("observeBy"), f"scenarioTriggers.{scenario}.observeBy")
        if observe_by < issued_at or observe_by > session_close:
            raise ValidationError(
                f"scenarioTriggers.{scenario}.observeBy must be between issue and close"
            )
        conditions = row.get("conditions")
        if not isinstance(conditions, list) or not conditions:
            raise ValidationError(f"scenarioTriggers.{scenario}.conditions cannot be empty")
        scenario_condition_ids: list[str] = []
        for condition in conditions:
            if not isinstance(condition, dict):
                raise ValidationError("scenario trigger condition must be an object")
            condition_id = condition.get("id")
            description = condition.get("description")
            if (
                not isinstance(condition_id, str)
                or not condition_id.strip()
                or condition_id in trigger_ids
            ):
                raise ValidationError("scenario trigger ids must be unique non-empty strings")
            if not isinstance(description, str) or not description.strip():
                raise ValidationError(f"scenario trigger {condition_id} needs a description")
            metric_id = condition.get("metricId")
            if metric_id not in TRIGGER_METRICS:
                raise ValidationError(
                    f"scenario trigger {condition_id} has an unsupported metricId"
                )
            operator = condition.get("operator")
            if operator not in TRIGGER_OPERATORS:
                raise ValidationError(
                    f"scenario trigger {condition_id} has an unsupported operator"
                )
            threshold = validate_trigger_threshold(
                condition.get("threshold"),
                operator,
                f"scenarioTriggers.{scenario}.{condition_id}.threshold",
            )
            source = condition.get("source")
            if not isinstance(source, str) or not source.strip():
                raise ValidationError(f"scenario trigger {condition_id} needs a source")
            trigger_ids.add(condition_id)
            scenario_condition_ids.append(condition_id)
            parsed_conditions[condition_id] = {
                "scenario": scenario,
                "observeBy": observe_by,
                "metricId": metric_id,
                "unit": TRIGGER_METRICS[metric_id],
                "operator": operator,
                "threshold": threshold,
                "source": source,
            }
        parsed_scenarios[scenario] = {
            "logic": row["logic"],
            "observeBy": observe_by,
            "conditionIds": scenario_condition_ids,
        }
    return payload, trigger_ids, parsed_conditions, parsed_scenarios


def validate_hypothesis_trials(
    payload: Any,
    reference_price: float,
    market_regime: str,
    *,
    data_cutoff_at: datetime,
    issued_at: datetime,
) -> tuple[list[dict[str, Any]], set[str]]:
    if payload is None:
        return [], set()
    if not isinstance(payload, list):
        raise ValidationError("hypothesisTrials must be an array")
    result: list[dict[str, Any]] = []
    hypothesis_ids: set[str] = set()
    for row in payload:
        if not isinstance(row, dict):
            raise ValidationError("each hypothesis trial must be an object")
        hypothesis_id = row.get("hypothesisId")
        regime = row.get("regime")
        predictor_version = row.get("predictorVersion")
        if (
            not isinstance(hypothesis_id, str)
            or not hypothesis_id.strip()
            or hypothesis_id in hypothesis_ids
        ):
            raise ValidationError("hypothesis trial ids must be unique non-empty strings")
        if regime not in HYPOTHESIS_REGIMES:
            raise ValidationError(f"hypothesis trial {hypothesis_id} has an invalid regime")
        if regime != market_regime:
            raise ValidationError(
                f"hypothesis trial {hypothesis_id} regime must match forecast.marketRegime"
            )
        if not isinstance(predictor_version, str) or not predictor_version.strip():
            raise ValidationError(
                f"hypothesis trial {hypothesis_id} needs predictorVersion"
            )
        candidate_prediction = require_number(
            row.get("candidatePrediction"),
            f"hypothesisTrials.{hypothesis_id}.candidatePrediction",
            positive=True,
        )
        baseline_id = row.get("baselineId")
        if baseline_id not in BASELINE_IDS:
            raise ValidationError(f"hypothesis trial {hypothesis_id} has an invalid baselineId")
        baseline_prediction = reference_price
        (
            predictor_input_status,
            predictor_inputs,
            missing_input_evidence,
        ) = validate_predictor_inputs(
            row,
            hypothesis_id,
            data_cutoff_at=data_cutoff_at,
            issued_at=issued_at,
        )
        hypothesis_ids.add(hypothesis_id)
        result.append(
            {
                "hypothesisId": hypothesis_id,
                "regime": regime,
                "candidatePrediction": candidate_prediction,
                "baselineId": baseline_id,
                "baselinePrediction": baseline_prediction,
                "predictorVersion": predictor_version,
                "predictorInputStatus": predictor_input_status,
                "predictorInputsParsed": predictor_inputs,
                "missingInputEvidenceParsed": missing_input_evidence,
            }
        )
    return result, hypothesis_ids


def validate_forecast(
    payload: dict[str, Any],
    path: Path,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    if payload.get("schemaVersion") != 1:
        raise ValidationError(f"{path}: unsupported schemaVersion")
    forbidden = FORBIDDEN_FORECAST_FIELDS.intersection(payload)
    if forbidden:
        raise ValidationError(f"{path}: forecast contains post-close fields: {sorted(forbidden)}")
    forecast_id = payload.get("forecastId")
    if not isinstance(forecast_id, str) or not forecast_id.strip():
        raise ValidationError(f"{path}: forecastId is required")
    visibility = payload.get("visibility")
    if visibility not in VISIBILITIES:
        raise ValidationError(f"{path}: visibility must be public or internal")
    issued_at = parse_iso(payload.get("issuedAt"), "issuedAt")
    data_cutoff_at = parse_iso(payload.get("dataCutoffAt"), "dataCutoffAt")
    if issued_at < data_cutoff_at:
        raise ValidationError(f"{path}: issuedAt precedes dataCutoffAt")
    market_state = payload.get("marketState")
    if market_state not in MARKET_STATES:
        raise ValidationError(f"{path}: invalid marketState")
    evaluation_bucket = payload.get("evaluationBucket")
    if evaluation_bucket not in EVALUATION_BUCKETS:
        raise ValidationError(f"{path}: invalid evaluationBucket")
    target = payload.get("target")
    if not isinstance(target, dict):
        raise ValidationError(f"{path}: target is required")
    session_date = target.get("sessionDate")
    try:
        session_day = datetime.strptime(str(session_date), "%Y-%m-%d").date()
    except ValueError as error:
        raise ValidationError(f"{path}: invalid target.sessionDate") from error
    if target.get("horizon") != "session_close" or target.get("instrument") != "KOSPI":
        raise ValidationError(f"{path}: only KOSPI session_close is currently supported")
    lead_sessions = target.get("leadSessions")
    if isinstance(lead_sessions, bool) or lead_sessions not in {0, 1}:
        raise ValidationError(f"{path}: target.leadSessions must be 0 or 1")
    previous_session_date = target.get("previousSessionDate")
    try:
        previous_session_day = datetime.strptime(
            str(previous_session_date), "%Y-%m-%d"
        ).date()
    except ValueError as error:
        raise ValidationError(f"{path}: invalid target.previousSessionDate") from error
    if previous_session_day >= session_day:
        raise ValidationError(
            f"{path}: target.previousSessionDate must precede target.sessionDate"
        )
    issued_local_day = issued_at.astimezone(SEOUL).date()
    expected_lead_sessions = 0 if issued_local_day == session_day else 1
    if lead_sessions != expected_lead_sessions:
        raise ValidationError(
            f"{path}: target.leadSessions is {lead_sessions}, expected "
            f"{expected_lead_sessions} from issuedAt"
        )
    if issued_local_day < previous_session_day:
        raise ValidationError(
            f"{path}: issuedAt precedes target.previousSessionDate; only the current "
            "or next trading session may be targeted"
        )
    session_close = datetime.combine(session_day, time(15, 30), tzinfo=SEOUL)
    if issued_at >= session_close or data_cutoff_at >= session_close:
        raise ValidationError(f"{path}: session-close forecast must be sealed before 15:30 KST")
    inferred_bucket, inferred_state = expected_bucket(issued_at, session_day)
    if evaluation_bucket != inferred_bucket:
        raise ValidationError(
            f"{path}: evaluationBucket is {evaluation_bucket}, expected {inferred_bucket}"
        )
    if market_state != inferred_state:
        raise ValidationError(f"{path}: marketState is {market_state}, expected {inferred_state}")
    data_lag_minutes = (issued_at - data_cutoff_at).total_seconds() / 60
    max_data_lag = (
        MAX_POSTCLOSE_DATA_LAG_MINUTES
        if inferred_bucket == "postclose"
        else MAX_DATA_LAG_MINUTES
    )
    if data_lag_minutes > max_data_lag:
        raise ValidationError(
            f"{path}: dataCutoffAt is {data_lag_minutes:.1f} minutes behind issuedAt; "
            f"maximum is {max_data_lag:.0f}"
        )
    reference = payload.get("reference")
    if not isinstance(reference, dict):
        raise ValidationError(f"{path}: reference is required")
    reference_price = require_number(reference.get("price"), "reference.price", positive=True)
    reference_as_of = parse_iso(reference.get("asOf"), "reference.asOf")
    reference_kind = reference.get("kind")
    if reference_kind not in {"live", "previous_close"}:
        raise ValidationError(f"{path}: reference.kind must be live or previous_close")
    if reference_as_of > data_cutoff_at:
        raise ValidationError(f"{path}: reference.asOf is later than dataCutoffAt")
    reference_local = reference_as_of.astimezone(SEOUL)
    if inferred_state == "intraday":
        reference_lag_minutes = (
            data_cutoff_at - reference_as_of
        ).total_seconds() / 60
        if reference_kind != "live":
            raise ValidationError(f"{path}: intraday reference.kind must be live")
        if reference_local.date() != session_day:
            raise ValidationError(
                f"{path}: intraday reference.asOf must be on target.sessionDate"
            )
        if reference_lag_minutes > MAX_LIVE_REFERENCE_LAG_MINUTES:
            raise ValidationError(
                f"{path}: live reference is {reference_lag_minutes:.1f} minutes behind "
                f"dataCutoffAt; maximum is {MAX_LIVE_REFERENCE_LAG_MINUTES:.0f}"
            )
    else:
        if reference_kind != "previous_close":
            raise ValidationError(
                f"{path}: preopen/postclose reference.kind must be previous_close"
            )
        if (
            reference_local.date() != previous_session_day
            or reference_local.time() < time(15, 30)
        ):
            raise ValidationError(
                f"{path}: previous_close reference must be the sealed "
                "target.previousSessionDate close"
            )
    scenarios = validate_scenarios(payload.get("scenarios"))
    path_envelope = payload.get("pathEnvelope")
    if not isinstance(path_envelope, dict):
        raise ValidationError(f"{path}: pathEnvelope is required")
    path_low = require_number(path_envelope.get("low"), "pathEnvelope.low", positive=True)
    path_high = require_number(path_envelope.get("high"), "pathEnvelope.high", positive=True)
    if path_low > path_high:
        raise ValidationError(f"{path}: pathEnvelope.low exceeds pathEnvelope.high")
    if path_low > scenarios["bear"]["low"] or path_high < scenarios["bull"]["high"]:
        raise ValidationError(f"{path}: pathEnvelope must contain every close scenario")
    close_envelope_coverage = require_number(
        payload.get("closeEnvelopeCoverage"), "closeEnvelopeCoverage"
    )
    path_coverage = require_number(path_envelope.get("coverage"), "pathEnvelope.coverage")
    if not math.isclose(close_envelope_coverage, CLOSE_ENVELOPE_COVERAGE, abs_tol=1e-9):
        raise ValidationError(
            f"{path}: closeEnvelopeCoverage must be fixed at {CLOSE_ENVELOPE_COVERAGE}"
        )
    if not math.isclose(path_coverage, PATH_ENVELOPE_COVERAGE, abs_tol=1e-9):
        raise ValidationError(
            f"{path}: pathEnvelope.coverage must be fixed at {PATH_ENVELOPE_COVERAGE}"
        )
    drivers, driver_ids = validate_drivers(payload.get("drivers"))
    (
        scenario_triggers,
        trigger_ids,
        trigger_conditions,
        trigger_scenarios,
    ) = validate_scenario_triggers(
        payload.get("scenarioTriggers"), issued_at=issued_at, session_close=session_close
    )
    market_regime = payload.get("marketRegime")
    if market_regime not in HYPOTHESIS_REGIMES:
        raise ValidationError(f"{path}: marketRegime must use the fixed taxonomy")
    hypothesis_trials, hypothesis_trial_ids = validate_hypothesis_trials(
        payload.get("hypothesisTrials"),
        reference_price,
        market_regime,
        data_cutoff_at=data_cutoff_at,
        issued_at=issued_at,
    )
    posture = payload.get("posture")
    if not isinstance(posture, dict) or set(posture) != {"attack", "wait", "defense"}:
        raise ValidationError(f"{path}: posture must contain attack, wait, and defense")
    posture_values = {
        key: require_number(posture[key], f"posture.{key}") for key in ("attack", "wait", "defense")
    }
    if any(value < 0 for value in posture_values.values()) or not math.isclose(
        sum(posture_values.values()), 100.0, abs_tol=1e-9
    ):
        raise ValidationError(f"{path}: posture values must be non-negative and sum to 100")
    supersedes = payload.get("supersedes")
    if supersedes is not None and (not isinstance(supersedes, str) or not supersedes.strip()):
        raise ValidationError(f"{path}: supersedes must be null or a forecastId")
    report_path = payload.get("reportPath")
    report_sha256 = payload.get("reportSha256")
    if not isinstance(report_path, str) or not report_path:
        raise ValidationError(f"{path}: reportPath is required")
    if not isinstance(report_sha256, str) or len(report_sha256) != 64:
        raise ValidationError(f"{path}: reportSha256 must be a SHA-256 hex digest")
    try:
        int(report_sha256, 16)
    except ValueError as error:
        raise ValidationError(f"{path}: reportSha256 is not hexadecimal") from error
    forecast_relative_path = None
    if repo_root is not None:
        try:
            forecast_relative_path = path.resolve().relative_to(
                repo_root.resolve()
            ).as_posix()
        except ValueError as error:
            raise ValidationError(
                f"{path}: forecast contract path escapes the repository"
            ) from error
        report_file = (repo_root / report_path).resolve()
        try:
            report_file.relative_to(repo_root.resolve())
        except ValueError as error:
            raise ValidationError(f"{path}: reportPath escapes the repository") from error
        if not report_file.is_file():
            raise ValidationError(f"{path}: reportPath does not exist")
        actual_digest = hashlib.sha256(report_file.read_bytes()).hexdigest()
        if actual_digest != report_sha256:
            raise ValidationError(f"{path}: reportSha256 no longer matches the report")
    content_hash = validate_raw_hash(payload.get("contentHash"), f"{path}: contentHash")
    expected_content_hash = canonical_forecast_content_hash(payload)
    if content_hash != expected_content_hash:
        raise ValidationError(
            f"{path}: contentHash does not match the sealed forecast contract"
        )
    return {
        **payload,
        "forecastId": forecast_id,
        "visibility": visibility,
        "contentHash": content_hash,
        "forecastRelativePath": forecast_relative_path,
        "issuedAtParsed": issued_at,
        "dataCutoffAtParsed": data_cutoff_at,
        "sessionDate": str(session_date),
        "referencePrice": reference_price,
        "referenceAsOfParsed": reference_as_of,
        "referenceKind": reference_kind,
        "scenariosParsed": scenarios,
        "closeEnvelopeCoverageParsed": close_envelope_coverage,
        "pathEnvelopeParsed": {"low": path_low, "high": path_high, "coverage": path_coverage},
        "driversParsed": drivers,
        "driverIds": driver_ids,
        "scenarioTriggersParsed": scenario_triggers,
        "triggerIds": trigger_ids,
        "triggerConditionsParsed": trigger_conditions,
        "triggerScenariosParsed": trigger_scenarios,
        "hypothesisTrialsParsed": hypothesis_trials,
        "hypothesisTrialIds": hypothesis_trial_ids,
    }


def validate_actual(payload: dict[str, Any], path: Path) -> dict[str, Any]:
    if payload.get("schemaVersion") != 1:
        raise ValidationError(f"{path}: unsupported schemaVersion")
    session_date = payload.get("sessionDate")
    try:
        datetime.strptime(str(session_date), "%Y-%m-%d")
    except ValueError as error:
        raise ValidationError(f"{path}: invalid sessionDate") from error
    expected_bizdate = str(session_date).replace("-", "")
    if payload.get("bizdate") != expected_bizdate:
        raise ValidationError(f"{path}: bizdate does not match sessionDate")
    if payload.get("marketStatus") != "CLOSE":
        raise ValidationError(f"{path}: marketStatus must be CLOSE")
    fetched_at = parse_iso(payload.get("fetchedAt"), "fetchedAt")
    actual = payload.get("kospi")
    if not isinstance(actual, dict):
        raise ValidationError(f"{path}: kospi is required")
    prices = {
        key: require_number(actual.get(key), f"kospi.{key}", positive=True)
        for key in ("open", "high", "low", "close")
    }
    if prices["high"] < max(prices["open"], prices["close"]) or prices["low"] > min(
        prices["open"], prices["close"]
    ):
        raise ValidationError(f"{path}: KOSPI OHLC is inconsistent")
    if prices["high"] < prices["low"]:
        raise ValidationError(f"{path}: KOSPI high is lower than low")
    actual_as_of = parse_iso(actual.get("asOf"), "kospi.asOf")
    local_as_of = actual_as_of.astimezone(SEOUL)
    if local_as_of.strftime("%Y-%m-%d") != str(session_date) or local_as_of.time() < time(15, 30):
        raise ValidationError(f"{path}: KOSPI actual must be a 15:30 KST or later close")
    if fetched_at < actual_as_of:
        raise ValidationError(f"{path}: fetchedAt precedes kospi.asOf")
    source = actual.get("source")
    if not isinstance(source, str) or not source.strip():
        raise ValidationError(f"{path}: kospi.source is required")
    validate_raw_hash(actual.get("rawHash"), f"{path}: kospi.rawHash")
    close_snapshot = payload.get("closeSnapshot")
    parsed_close_snapshot = None
    if close_snapshot is None:
        if not isinstance(payload.get("closeSnapshotMissingReason"), str) or not payload[
            "closeSnapshotMissingReason"
        ].strip():
            raise ValidationError(
                f"{path}: closeSnapshot or closeSnapshotMissingReason is required"
            )
    elif not isinstance(close_snapshot, dict):
        raise ValidationError(f"{path}: closeSnapshot must be an object or null")
    else:
        required_sections = {"kodex", "cashFlow", "program", "breadth"}
        if set(close_snapshot) != required_sections:
            raise ValidationError(
                f"{path}: closeSnapshot must contain {sorted(required_sections)}"
            )
        kodex = close_snapshot["kodex"]
        cash_flow = close_snapshot["cashFlow"]
        program = close_snapshot["program"]
        breadth = close_snapshot["breadth"]
        if not all(isinstance(row, dict) for row in (kodex, cash_flow, program, breadth)):
            raise ValidationError(f"{path}: closeSnapshot sections must be objects")

        kodex_prices = {
            key: require_number(kodex.get(key), f"closeSnapshot.kodex.{key}", positive=True)
            for key in ("open", "high", "low", "close")
        }
        if kodex_prices["high"] < max(kodex_prices["open"], kodex_prices["close"]):
            raise ValidationError(f"{path}: closeSnapshot KODEX high is inconsistent")
        if kodex_prices["low"] > min(kodex_prices["open"], kodex_prices["close"]):
            raise ValidationError(f"{path}: closeSnapshot KODEX low is inconsistent")
        if kodex_prices["high"] < kodex_prices["low"]:
            raise ValidationError(f"{path}: closeSnapshot KODEX high is lower than low")
        kodex_volume = require_number(
            kodex.get("volume"), "closeSnapshot.kodex.volume", positive=True
        )
        kodex_meta = validate_close_source_metadata(
            kodex,
            "closeSnapshot.kodex",
            session_date=str(session_date),
            fetched_at=fetched_at,
        )

        if cash_flow.get("unit") != "억원":
            raise ValidationError(f"{path}: closeSnapshot.cashFlow.unit must be 억원")
        cash_flow_values = {
            key: require_number(cash_flow.get(key), f"closeSnapshot.cashFlow.{key}")
            for key in ("foreign", "institution", "personal")
        }
        cash_flow_meta = validate_close_source_metadata(
            cash_flow,
            "closeSnapshot.cashFlow",
            session_date=str(session_date),
            fetched_at=fetched_at,
        )

        if program.get("unit") != "억원":
            raise ValidationError(f"{path}: closeSnapshot.program.unit must be 억원")
        program_values = {
            key: require_number(program.get(key), f"closeSnapshot.program.{key}")
            for key in ("arbitrage", "nonArbitrage", "total")
        }
        if not math.isclose(
            program_values["arbitrage"] + program_values["nonArbitrage"],
            program_values["total"],
            abs_tol=1.0,
        ):
            raise ValidationError(
                f"{path}: closeSnapshot.program.total does not match its components"
            )
        program_meta = validate_close_source_metadata(
            program,
            "closeSnapshot.program",
            session_date=str(session_date),
            fetched_at=fetched_at,
        )

        if breadth.get("unit") != "종목":
            raise ValidationError(f"{path}: closeSnapshot.breadth.unit must be 종목")
        breadth_values = {
            key: require_nonnegative_integer(
                breadth.get(key), f"closeSnapshot.breadth.{key}"
            )
            for key in ("up", "flat", "down")
        }
        breadth_meta = validate_close_source_metadata(
            breadth,
            "closeSnapshot.breadth",
            session_date=str(session_date),
            fetched_at=fetched_at,
        )
        parsed_close_snapshot = {
            "kodex": {**kodex_prices, "volume": kodex_volume, **kodex_meta},
            "cashFlow": {**cash_flow_values, **cash_flow_meta},
            "program": {**program_values, **program_meta},
            "breadth": {**breadth_values, **breadth_meta},
        }
    (
        parsed_flow_trajectory,
        parsed_flow_features,
        parsed_flow_missing_evidence,
    ) = validate_flow_trajectory(
        payload,
        path,
        session_date=str(session_date),
        fetched_at=fetched_at,
        close_snapshot=parsed_close_snapshot,
    )
    return {
        **payload,
        "sessionDate": str(session_date),
        "fetchedAtParsed": fetched_at,
        "actualAsOfParsed": actual_as_of,
        "actualParsed": prices,
        "closeSnapshotParsed": parsed_close_snapshot,
        "flowTrajectoryParsed": parsed_flow_trajectory,
        "flowFeaturesParsed": parsed_flow_features,
        "flowTrajectoryMissingEvidenceParsed": parsed_flow_missing_evidence,
    }


def validate_outcome(
    payload: dict[str, Any],
    path: Path,
    forecast: dict[str, Any],
    actual: dict[str, Any],
) -> dict[str, Any]:
    if payload.get("schemaVersion") != 1:
        raise ValidationError(f"{path}: unsupported schemaVersion")
    if payload.get("forecastId") != forecast["forecastId"]:
        raise ValidationError(f"{path}: forecastId does not match")
    recorded_at = parse_iso(payload.get("recordedAt"), "recordedAt")
    actual_ref = payload.get("actualRef")
    if actual_ref != actual["sessionDate"] or actual_ref != forecast["sessionDate"]:
        raise ValidationError(f"{path}: actualRef does not match forecast session")
    if recorded_at < actual["actualAsOfParsed"]:
        raise ValidationError(f"{path}: recordedAt precedes the archived close")
    realized = payload.get("realizedScenario")
    if realized not in SCENARIOS:
        raise ValidationError(f"{path}: invalid realizedScenario")
    expected_realized = classify_close(actual["actualParsed"]["close"], forecast["scenariosParsed"])
    if realized != expected_realized:
        raise ValidationError(
            f"{path}: realizedScenario is {realized}, expected {expected_realized} from the close"
        )
    error_codes = payload.get("errorCodes", [])
    if (
        not isinstance(error_codes, list)
        or len(set(error_codes)) != len(error_codes)
        or any(code not in ERROR_CODES for code in error_codes)
    ):
        raise ValidationError(f"{path}: errorCodes contains an unknown code")
    trigger_results = payload.get("triggerResults")
    if not isinstance(trigger_results, list):
        raise ValidationError(f"{path}: triggerResults must be an array")
    trigger_result_ids: set[str] = set()
    for row in trigger_results:
        if not isinstance(row, dict):
            raise ValidationError(f"{path}: invalid trigger result")
        trigger_id = row.get("id")
        if not isinstance(trigger_id, str) or trigger_id in trigger_result_ids:
            raise ValidationError(f"{path}: trigger result ids must be unique")
        condition = forecast["triggerConditionsParsed"].get(trigger_id)
        if condition is None:
            raise ValidationError(f"{path}: trigger result {trigger_id} was not sealed")
        status = row.get("status")
        if status == "unavailable":
            if set(row) != {"id", "status", "reason"}:
                raise ValidationError(
                    f"{path}: unavailable trigger {trigger_id} needs only a reason"
                )
            if not isinstance(row.get("reason"), str) or not row["reason"].strip():
                raise ValidationError(f"{path}: unavailable trigger {trigger_id} needs a reason")
        elif status in {"observed", "not_observed"}:
            if set(row) != {"id", "status", "observedAt", "observedValue", "source"}:
                raise ValidationError(
                    f"{path}: observed trigger {trigger_id} needs value, time, and source"
                )
            observed_at = parse_iso(row.get("observedAt"), f"triggerResults.{trigger_id}.observedAt")
            if observed_at < forecast["issuedAtParsed"] or observed_at > condition["observeBy"]:
                raise ValidationError(
                    f"{path}: trigger {trigger_id} observedAt is outside its sealed window"
                )
            observed_value = require_number(
                row.get("observedValue"), f"triggerResults.{trigger_id}.observedValue"
            )
            if row.get("source") != condition["source"]:
                raise ValidationError(f"{path}: trigger {trigger_id} source changed after issue")
            expected_status = (
                "observed"
                if trigger_condition_observed(
                    observed_value, condition["operator"], condition["threshold"]
                )
                else "not_observed"
            )
            if status != expected_status:
                raise ValidationError(
                    f"{path}: trigger {trigger_id} status is {status}, expected {expected_status}"
                )
        else:
            raise ValidationError(f"{path}: invalid trigger result")
        trigger_result_ids.add(trigger_id)
    if trigger_result_ids != forecast["triggerIds"]:
        raise ValidationError(f"{path}: triggerResults do not match the sealed trigger ids")
    trigger_results_by_id = {row["id"]: row["status"] for row in trigger_results}
    scenario_trigger_statuses: dict[str, str] = {}
    for scenario, scenario_rule in forecast["triggerScenariosParsed"].items():
        statuses = [
            trigger_results_by_id[condition_id]
            for condition_id in scenario_rule["conditionIds"]
        ]
        scenario_trigger_statuses[scenario] = aggregate_trigger_status(
            scenario_rule["logic"], statuses
        )
    derived_trigger_codes: set[str] = set()
    if any(
        status == "observed" and scenario != realized
        for scenario, status in scenario_trigger_statuses.items()
    ):
        derived_trigger_codes.add("trigger_false_positive")
    if scenario_trigger_statuses[realized] == "not_observed":
        derived_trigger_codes.add("trigger_missed")
    trigger_error_codes = {"trigger_false_positive", "trigger_missed"}
    manually_declared_trigger_codes = set(error_codes).intersection(trigger_error_codes)
    if not manually_declared_trigger_codes.issubset(derived_trigger_codes):
        raise ValidationError(
            f"{path}: trigger errorCodes conflict with derived scenario logic"
        )
    parsed_error_codes = sorted(
        (set(error_codes) - trigger_error_codes).union(derived_trigger_codes)
    )
    driver_assessment = payload.get("driverAssessment")
    if not isinstance(driver_assessment, list):
        raise ValidationError(f"{path}: driverAssessment must be an array")
    assessed_ids: set[str] = set()
    for row in driver_assessment:
        if not isinstance(row, dict) or row.get("status") not in {
            "confirmed",
            "partial",
            "rejected",
            "unverifiable",
        }:
            raise ValidationError(f"{path}: invalid driver assessment")
        driver_id = row.get("id")
        if not isinstance(driver_id, str) or driver_id in assessed_ids:
            raise ValidationError(f"{path}: driver assessment ids must be unique")
        assessed_ids.add(driver_id)
    if assessed_ids != forecast["driverIds"]:
        raise ValidationError(f"{path}: driverAssessment does not match sealed drivers")
    hypothesis_tests = payload.get("hypothesisTests", [])
    if not isinstance(hypothesis_tests, list):
        raise ValidationError(f"{path}: hypothesisTests must be an array")
    sealed_trials = {
        row["hypothesisId"]: row for row in forecast["hypothesisTrialsParsed"]
    }
    hypothesis_ids: set[str] = set()
    parsed_hypothesis_tests: list[dict[str, Any]] = []
    for row in hypothesis_tests:
        if not isinstance(row, dict) or row.get("result") not in {
            "supported",
            "refuted",
            "inconclusive",
        }:
            raise ValidationError(f"{path}: invalid hypothesis test")
        hypothesis_id = row.get("hypothesisId")
        if not isinstance(hypothesis_id, str) or not hypothesis_id or hypothesis_id in hypothesis_ids:
            raise ValidationError(f"{path}: hypothesis test ids must be unique")
        if set(row) != {"hypothesisId", "result"}:
            raise ValidationError(
                f"{path}: hypothesisTests may only record hypothesisId and result"
            )
        sealed = sealed_trials.get(hypothesis_id)
        if sealed is None:
            raise ValidationError(
                f"{path}: hypothesis {hypothesis_id} was not sealed in the forecast"
            )
        close = actual["actualParsed"]["close"]
        reference = forecast["referencePrice"]
        baseline_lift_bps = (
            abs(close - sealed["baselinePrediction"])
            - abs(close - sealed["candidatePrediction"])
        ) / reference * 10000
        expected_result = (
            "supported"
            if baseline_lift_bps > 1e-9
            else "refuted"
            if baseline_lift_bps < -1e-9
            else "inconclusive"
        )
        if row["result"] != expected_result:
            raise ValidationError(
                f"{path}: hypothesis {hypothesis_id} result is {row['result']}, "
                f"expected {expected_result} from the sealed predictions"
            )
        hypothesis_ids.add(hypothesis_id)
        input_evidence_status = compare_predictor_inputs(
            sealed, actual["flowTrajectoryParsed"]
        )
        parsed_hypothesis_tests.append(
            {
                **row,
                "regime": sealed["regime"],
                "candidatePrediction": sealed["candidatePrediction"],
                "baselinePrediction": sealed["baselinePrediction"],
                "predictorVersion": sealed["predictorVersion"],
                "inputEvidenceStatus": input_evidence_status,
                "baselineLiftBpsParsed": baseline_lift_bps,
            }
        )
    if hypothesis_ids != forecast["hypothesisTrialIds"]:
        raise ValidationError(
            f"{path}: hypothesisTests do not match the sealed hypothesisTrials"
        )
    post_forecast_path = None
    post_forecast_path_status = payload.get("postForecastPathStatus")
    post_forecast_path_missing_reason = payload.get("postForecastPathMissingReason")
    post_forecast_path_missing_evidence = payload.get(
        "postForecastPathMissingEvidence"
    )
    parsed_missing_evidence = None
    if forecast["marketState"] == "intraday":
        if post_forecast_path_status not in {"available", "missing"}:
            raise ValidationError(
                f"{path}: intraday outcome needs postForecastPathStatus"
            )
        if post_forecast_path_status == "missing":
            if payload.get("postForecastPath") is not None:
                raise ValidationError(
                    f"{path}: missing postForecastPathStatus cannot contain a path"
                )
            if (
                not isinstance(post_forecast_path_missing_reason, str)
                or not post_forecast_path_missing_reason.strip()
            ):
                raise ValidationError(
                    f"{path}: missing intraday path needs postForecastPathMissingReason"
                )
            if not isinstance(post_forecast_path_missing_evidence, dict) or set(
                post_forecast_path_missing_evidence
            ) != {"sourceStatus", "source", "asOf", "fetchedAt", "rawHash"}:
                raise ValidationError(
                    f"{path}: missing intraday path needs exact "
                    "postForecastPathMissingEvidence metadata"
                )
            source_status = post_forecast_path_missing_evidence.get("sourceStatus")
            if source_status not in PATH_SOURCE_STATUSES:
                raise ValidationError(
                    f"{path}: missing path sourceStatus must be unavailable, "
                    "incomplete, or invalid"
                )
            missing_source = post_forecast_path_missing_evidence.get("source")
            if not isinstance(missing_source, str) or not missing_source.strip():
                raise ValidationError(f"{path}: missing path evidence source is required")
            missing_as_of = parse_iso(
                post_forecast_path_missing_evidence.get("asOf"),
                "postForecastPathMissingEvidence.asOf",
            )
            missing_fetched_at = parse_iso(
                post_forecast_path_missing_evidence.get("fetchedAt"),
                "postForecastPathMissingEvidence.fetchedAt",
            )
            if missing_as_of != actual["actualAsOfParsed"]:
                raise ValidationError(
                    f"{path}: missing path evidence asOf must equal the archived close"
                )
            if missing_fetched_at < missing_as_of or missing_fetched_at > recorded_at:
                raise ValidationError(
                    f"{path}: missing path evidence fetchedAt must be between "
                    "asOf and recordedAt"
                )
            missing_raw_hash = validate_raw_hash(
                post_forecast_path_missing_evidence.get("rawHash"),
                "postForecastPathMissingEvidence.rawHash",
            )
            parsed_missing_evidence = {
                "sourceStatus": source_status,
                "source": missing_source,
                "asOf": missing_as_of,
                "fetchedAt": missing_fetched_at,
                "rawHash": missing_raw_hash,
            }
        elif payload.get("postForecastPath") is None:
            raise ValidationError(
                f"{path}: available postForecastPathStatus needs postForecastPath"
            )
        elif post_forecast_path_missing_reason is not None:
            raise ValidationError(
                f"{path}: available path cannot have postForecastPathMissingReason"
            )
        elif post_forecast_path_missing_evidence is not None:
            raise ValidationError(
                f"{path}: available path cannot have postForecastPathMissingEvidence"
            )
    elif any(
        key in payload
        for key in (
            "postForecastPath",
            "postForecastPathStatus",
            "postForecastPathMissingReason",
            "postForecastPathMissingEvidence",
        )
    ):
        raise ValidationError(
            f"{path}: postForecastPath fields are only used for intraday forecasts"
        )
    if post_forecast_path_status == "available":
        row = payload["postForecastPath"]
        if not isinstance(row, dict):
            raise ValidationError(f"{path}: postForecastPath must be an object")
        path_from = parse_iso(row.get("from"), "postForecastPath.from")
        path_as_of = parse_iso(row.get("asOf"), "postForecastPath.asOf")
        path_fetched_at = parse_iso(row.get("fetchedAt"), "postForecastPath.fetchedAt")
        path_high = require_number(row.get("high"), "postForecastPath.high", positive=True)
        path_low = require_number(row.get("low"), "postForecastPath.low", positive=True)
        interval_minutes = require_nonnegative_integer(
            row.get("intervalMinutes"), "postForecastPath.intervalMinutes"
        )
        if interval_minutes not in {1, 5, 15, 30, 60}:
            raise ValidationError(
                f"{path}: postForecastPath.intervalMinutes must be 1, 5, 15, 30, or 60"
            )
        if path_high < path_low:
            raise ValidationError(f"{path}: postForecastPath high is lower than low")
        if path_from < forecast["issuedAtParsed"]:
            raise ValidationError(f"{path}: postForecastPath starts before the forecast was issued")
        if path_from > forecast["issuedAtParsed"] + timedelta(minutes=interval_minutes):
            raise ValidationError(
                f"{path}: postForecastPath does not start with the first post-issue bar"
            )
        if path_from > path_as_of:
            raise ValidationError(f"{path}: postForecastPath.from is later than asOf")
        if path_as_of != actual["actualAsOfParsed"]:
            raise ValidationError(f"{path}: postForecastPath.asOf must equal the archived close")
        if path_fetched_at < path_as_of or path_fetched_at > recorded_at:
            raise ValidationError(
                f"{path}: postForecastPath.fetchedAt must be between asOf and recordedAt"
            )
        close = actual["actualParsed"]["close"]
        if not path_low <= close <= path_high:
            raise ValidationError(f"{path}: postForecastPath does not contain the close")
        if not isinstance(row.get("source"), str) or not row["source"].strip():
            raise ValidationError(f"{path}: postForecastPath.source is required")
        path_raw_hash = validate_raw_hash(
            row.get("rawHash"), "postForecastPath.rawHash"
        )
        post_forecast_path = {
            "from": path_from,
            "asOf": path_as_of,
            "fetchedAt": path_fetched_at,
            "intervalMinutes": interval_minutes,
            "high": path_high,
            "low": path_low,
            "source": row["source"],
            "rawHash": path_raw_hash,
        }
    return {
        **payload,
        "recordedAtParsed": recorded_at,
        "actualParsed": actual["actualParsed"],
        "errorCodesParsed": parsed_error_codes,
        "triggerScenarioStatusParsed": scenario_trigger_statuses,
        "postForecastPathStatusParsed": post_forecast_path_status,
        "postForecastPathMissingReasonParsed": post_forecast_path_missing_reason,
        "postForecastPathMissingEvidenceParsed": parsed_missing_evidence,
        "postForecastPathParsed": post_forecast_path,
        "hypothesisTestsParsed": parsed_hypothesis_tests,
        "flowTrajectoryParsed": actual["flowTrajectoryParsed"],
        "flowFeaturesParsed": actual["flowFeaturesParsed"],
    }


def validate_publication_event(
    payload: dict[str, Any], path: Path, forecast: dict[str, Any]
) -> dict[str, Any]:
    if payload.get("schemaVersion") != 1 or payload.get("forecastId") != forecast["forecastId"]:
        raise ValidationError(f"{path}: publication event does not match forecast")
    if forecast["visibility"] != "public":
        raise ValidationError(f"{path}: internal forecast cannot have publication events")
    event_type = payload.get("eventType")
    if event_type not in {"pushed", "deploy_verified"}:
        raise ValidationError(f"{path}: invalid publication eventType")
    common_fields = {
        "schemaVersion",
        "forecastId",
        "eventType",
        "occurredAt",
        "contentHash",
        "commitSha",
    }
    expected_fields = (
        common_fields
        if event_type == "pushed"
        else common_fields.union({"availabilityStatus", "publicUrl"})
    )
    if set(payload) != expected_fields:
        raise ValidationError(
            f"{path}: {event_type} publication fields must be {sorted(expected_fields)}"
        )
    event_content_hash = validate_raw_hash(
        payload.get("contentHash"), f"{path}: contentHash"
    )
    if event_content_hash != forecast["contentHash"]:
        raise ValidationError(
            f"{path}: publication contentHash does not match the forecast contract"
        )
    commit_sha = validate_commit_sha(payload.get("commitSha"), f"{path}: commitSha")
    occurred_at = parse_iso(payload.get("occurredAt"), "occurredAt")
    if occurred_at < forecast["issuedAtParsed"]:
        raise ValidationError(f"{path}: publication event precedes issuedAt")
    session_close = datetime.combine(
        datetime.strptime(forecast["sessionDate"], "%Y-%m-%d").date(),
        time(15, 30),
        tzinfo=SEOUL,
    )
    if occurred_at >= session_close:
        raise ValidationError(
            f"{path}: {event_type} occurred after the target close"
        )
    event_lag = (occurred_at - forecast["issuedAtParsed"]).total_seconds() / 60
    max_lag = (
        MAX_PUBLICATION_LAG_MINUTES
        if event_type == "pushed"
        else MAX_DEPLOY_VERIFY_LAG_MINUTES
    )
    if event_lag > max_lag:
        raise ValidationError(
            f"{path}: {event_type} is {event_lag:.1f} minutes behind issuedAt; "
            f"maximum is {max_lag:.0f}"
        )
    event_bucket, _ = expected_bucket(
        occurred_at, datetime.strptime(forecast["sessionDate"], "%Y-%m-%d").date()
    )
    if event_bucket != forecast["evaluationBucket"]:
        raise ValidationError(
            f"{path}: {event_type} crossed from {forecast['evaluationBucket']} "
            f"into {event_bucket}"
        )
    availability_status = None
    public_url = None
    if event_type == "deploy_verified":
        availability_status = payload.get("availabilityStatus")
        public_url = payload.get("publicUrl")
        if availability_status != "available":
            raise ValidationError(
                f"{path}: deploy_verified availabilityStatus must be available"
            )
        if not isinstance(public_url, str) or not public_url.startswith("https://"):
            raise ValidationError(
                f"{path}: deploy_verified publicUrl must be an https URL"
            )
    return {
        **payload,
        "eventType": event_type,
        "occurredAtParsed": occurred_at,
        "contentHashParsed": event_content_hash,
        "commitShaParsed": commit_sha,
        "availabilityStatusParsed": availability_status,
        "publicUrlParsed": public_url,
    }


def distance_to_range(value: float, low: float, high: float) -> float:
    if value < low:
        return low - value
    if value > high:
        return value - high
    return 0.0


def classify_close(value: float, scenarios: dict[str, dict[str, float]]) -> str:
    """Classify one close with base taking precedence at shared boundaries."""
    base = scenarios["base"]
    bear = scenarios["bear"]
    bull = scenarios["bull"]
    if base["low"] <= value <= base["high"]:
        return "base"
    if bear["low"] <= value < base["low"]:
        return "bear"
    if base["high"] < value <= bull["high"]:
        return "bull"
    return "bear" if value < base["low"] else "bull"


def sign(value: float, tolerance: float = 1e-12) -> int:
    if value > tolerance:
        return 1
    if value < -tolerance:
        return -1
    return 0


def interval_score_bps(
    value: float,
    low: float,
    high: float,
    coverage: float,
    reference: float,
) -> float:
    alpha = 1.0 - coverage
    miss = 0.0
    if value < low:
        miss = low - value
    elif value > high:
        miss = value - high
    score = (high - low) + (2.0 / alpha) * miss
    return score / reference * 10000


def score_pair(
    forecast: dict[str, Any],
    outcome: dict[str, Any],
    publication: dict[str, Any] | None = None,
) -> dict[str, Any]:
    scenarios = forecast["scenariosParsed"]
    close = outcome["actualParsed"]["close"]
    reference = forecast["referencePrice"]
    base = scenarios["base"]
    envelope_low = min(row["low"] for row in scenarios.values())
    envelope_high = max(row["high"] for row in scenarios.values())
    base_distance = distance_to_range(close, base["low"], base["high"])
    envelope_distance = distance_to_range(close, envelope_low, envelope_high)
    base_width_bps = (base["high"] - base["low"]) / reference * 10000
    base_miss_bps = base_distance / reference * 10000
    envelope_miss_bps = envelope_distance / reference * 10000
    base_interval_score_bps = interval_score_bps(
        close,
        base["low"],
        base["high"],
        base["probability"],
        reference,
    )
    close_envelope_score_bps = interval_score_bps(
        close,
        envelope_low,
        envelope_high,
        forecast["closeEnvelopeCoverageParsed"],
        reference,
    )
    realized = outcome["realizedScenario"]
    brier = sum(
        (scenarios[name]["probability"] - (1.0 if name == realized else 0.0)) ** 2
        for name in SCENARIOS
    )
    expected_center = sum(
        ((row["low"] + row["high"]) / 2) * row["probability"] for row in scenarios.values()
    )
    forecast_direction = sign(expected_center - reference)
    actual_direction = sign(close - reference)
    path_actual = outcome["postForecastPathParsed"]
    intraday_path_expected = forecast["marketState"] == "intraday"
    if path_actual is None and forecast["marketState"] in {"preopen", "postclose"}:
        path_actual = {
            "high": outcome["actualParsed"]["high"],
            "low": outcome["actualParsed"]["low"],
        }
    path_expected = True
    path_available = path_actual is not None
    path_envelope = forecast["pathEnvelopeParsed"]
    if path_actual is not None:
        actual_high = path_actual["high"]
        actual_low = path_actual["low"]
        path_low_miss_bps = max(0.0, path_envelope["low"] - actual_low) / reference * 10000
        path_high_miss_bps = max(0.0, actual_high - path_envelope["high"]) / reference * 10000
        high_move_bps = max(0.0, actual_high - reference) / reference * 10000
        low_move_bps = max(0.0, reference - actual_low) / reference * 10000
        path_interval_score_bps = (
            interval_score_bps(
                actual_low,
                path_envelope["low"],
                path_envelope["high"],
                path_envelope["coverage"],
                reference,
            )
            + interval_score_bps(
                actual_high,
                path_envelope["low"],
                path_envelope["high"],
                path_envelope["coverage"],
                reference,
            )
        ) / 2.0
        if forecast_direction > 0:
            favorable_move_bps, adverse_move_bps = high_move_bps, low_move_bps
        elif forecast_direction < 0:
            favorable_move_bps, adverse_move_bps = low_move_bps, high_move_bps
        else:
            favorable_move_bps = adverse_move_bps = None
    else:
        path_low_miss_bps = path_high_miss_bps = path_interval_score_bps = None
        favorable_move_bps = adverse_move_bps = None
    path_hit = (
        None
        if path_low_miss_bps is None
        else path_low_miss_bps == 0 and path_high_miss_bps == 0
    )
    if path_hit is None:
        path_hit_lower_bound = False
        path_hit_best_case = path_envelope["low"] <= close <= path_envelope["high"]
    else:
        path_hit_lower_bound = path_hit
        path_hit_best_case = path_hit
    center_error_bps = abs(close - expected_center) / reference * 10000
    carry_error_bps = abs(close - reference) / reference * 10000
    data_lag = (
        forecast["issuedAtParsed"] - forecast["dataCutoffAtParsed"]
    ).total_seconds() / 60
    publication_lag = None
    deploy_lag = None
    public_availability_status = None
    public_url = None
    if publication is not None:
        publication_lag = (
            publication["pushedAtParsed"] - forecast["issuedAtParsed"]
        ).total_seconds() / 60
        if publication["deployVerifiedAtParsed"] is not None:
            deploy_lag = (
                publication["deployVerifiedAtParsed"] - publication["pushedAtParsed"]
            ).total_seconds() / 60
        public_availability_status = publication["availabilityStatus"]
        public_url = publication["publicUrl"]
    return {
        "forecastId": forecast["forecastId"],
        "sessionDate": forecast["sessionDate"],
        "marketState": forecast["marketState"],
        "evaluationBucket": forecast["evaluationBucket"],
        "baseHit": base_distance == 0,
        "envelopeHit": envelope_distance == 0,
        "baseWidthBps": round(base_width_bps, 4),
        "baseMissBps": round(base_miss_bps, 4),
        "envelopeMissBps": round(envelope_miss_bps, 4),
        "baseIntervalScoreBps": round(base_interval_score_bps, 4),
        "closeEnvelopeIntervalScoreBps": round(close_envelope_score_bps, 4),
        "directionHit": forecast_direction == actual_direction,
        "forecastDirection": forecast_direction,
        "actualDirection": actual_direction,
        "pathExpected": path_expected,
        "pathAvailable": path_available,
        "intradayPathExpected": intraday_path_expected,
        "intradayPathAvailable": path_available if intraday_path_expected else True,
        "pathHit": path_hit,
        "pathHitLowerBound": path_hit_lower_bound,
        "pathHitBestCase": path_hit_best_case,
        "pathLowMissBps": None if path_low_miss_bps is None else round(path_low_miss_bps, 4),
        "pathHighMissBps": None if path_high_miss_bps is None else round(path_high_miss_bps, 4),
        "pathIntervalScoreBps": None
        if path_interval_score_bps is None
        else round(path_interval_score_bps, 4),
        "maxFavorableMoveBps": None if favorable_move_bps is None else round(favorable_move_bps, 4),
        "maxAdverseMoveBps": None if adverse_move_bps is None else round(adverse_move_bps, 4),
        "forecastCenterErrorBps": round(center_error_bps, 4),
        "referenceCarryErrorBps": round(carry_error_bps, 4),
        "centerLiftVsCarryBps": round(carry_error_bps - center_error_bps, 4),
        "brier": None if brier is None else round(brier, 6),
        "dataLagMinutes": round(data_lag, 3),
        "publicationLagMinutes": None if publication_lag is None else round(publication_lag, 3),
        "deployLagMinutes": None if deploy_lag is None else round(deploy_lag, 3),
        "publicAvailabilityStatus": public_availability_status,
        "publicUrl": public_url,
        "triggerScenarioStatuses": outcome["triggerScenarioStatusParsed"],
        "errorCodes": outcome["errorCodesParsed"],
    }


def select_aggregate_forecasts(
    forecasts_by_id: dict[str, dict[str, Any]],
    publications_by_id: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Keep the first public edition; otherwise use the immutable internal leaf."""
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    parent_to_child: dict[str, str] = {}
    superseded_ids: set[str] = set()
    for forecast in forecasts_by_id.values():
        key = (
            forecast["sessionDate"],
            forecast["target"]["horizon"],
            forecast["evaluationBucket"],
        )
        groups[key].append(forecast)
        parent_id = forecast.get("supersedes")
        if parent_id is None:
            continue
        parent = forecasts_by_id.get(parent_id)
        if parent is None:
            raise ValidationError(f"{forecast['forecastId']} supersedes an unknown forecast")
        parent_key = (
            parent["sessionDate"],
            parent["target"]["horizon"],
            parent["evaluationBucket"],
        )
        if parent_key != key:
            raise ValidationError(f"{forecast['forecastId']} supersedes a different evaluation group")
        if forecast["issuedAtParsed"] <= parent["issuedAtParsed"]:
            raise ValidationError(
                f"{forecast['forecastId']} must be issued after its superseded forecast"
            )
        if forecast["dataCutoffAtParsed"] < parent["dataCutoffAtParsed"]:
            raise ValidationError(
                f"{forecast['forecastId']} cannot use an older data cutoff than its parent"
            )
        if parent_id in parent_to_child:
            raise ValidationError(f"forecast revision chain branches at {parent_id}")
        parent_to_child[parent_id] = forecast["forecastId"]
        superseded_ids.add(parent_id)
    leaves: list[dict[str, Any]] = []
    for key, rows in groups.items():
        group_leaves = [row for row in rows if row["forecastId"] not in superseded_ids]
        if len(group_leaves) != 1:
            raise ValidationError(
                "one immutable revision leaf is required for each session/horizon/bucket: "
                f"{key} has {len(group_leaves)}"
            )
        leaf = group_leaves[0]
        seen: set[str] = set()
        current = leaf
        while current.get("supersedes") is not None:
            if current["forecastId"] in seen:
                raise ValidationError(f"forecast revision cycle at {current['forecastId']}")
            seen.add(current["forecastId"])
            current = forecasts_by_id[current["supersedes"]]
        public_rows = [row for row in rows if row["visibility"] == "public"]
        if public_rows:
            if publications_by_id is None or any(
                row["forecastId"] not in publications_by_id for row in public_rows
            ):
                raise ValidationError(
                    f"public aggregate selection for {key} needs complete publication evidence"
                )
            public_rows = sorted(
                public_rows,
                key=lambda row: publications_by_id[row["forecastId"]]["pushedAtParsed"],
            )
            if (
                len(public_rows) > 1
                and publications_by_id[public_rows[0]["forecastId"]]["pushedAtParsed"]
                == publications_by_id[public_rows[1]["forecastId"]]["pushedAtParsed"]
            ):
                raise ValidationError(
                    f"public aggregate selection for {key} has tied first push times"
                )
            representative = public_rows[0]
        else:
            representative = leaf
        leaves.append(representative)
    return sorted(leaves, key=lambda row: (row["sessionDate"], row["evaluationBucket"]))


def mean(values: Iterable[float]) -> float | None:
    collected = list(values)
    return sum(collected) / len(collected) if collected else None


def build_summary(
    scores: list[dict[str, Any]],
    unsettled_ids: list[str],
    *,
    generated_at: str | None,
    hypothesis_summary: list[dict[str, Any]],
) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for score in scores:
        grouped[score["evaluationBucket"]].append(score)

    def session_deduped_error_codes(
        rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        counts = Counter(
            code
            for session_date in {row["sessionDate"] for row in rows}
            for code in {
                code
                for row in rows
                if row["sessionDate"] == session_date
                for code in row["errorCodes"]
            }
        )
        return [
            {"code": code, "count": count}
            for code, count in sorted(
                counts.items(), key=lambda item: (-item[1], item[0])
            )
        ]

    def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
        rows_by_session: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            rows_by_session[row["sessionDate"]].append(row)

        def session_weighted_mean(getter: Any) -> float | None:
            session_values: list[float] = []
            for session_rows in rows_by_session.values():
                values = [getter(row) for row in session_rows]
                numeric = [float(value) for value in values if value is not None]
                session_value = mean(numeric)
                if session_value is not None:
                    session_values.append(session_value)
            return mean(session_values)

        path_hits = [row for row in rows if row["pathHit"] is not None]
        path_expected_count = sum(1 for row in rows if row["pathExpected"])
        path_coverage_by_session: list[float] = []
        intraday_path_expected_count = sum(
            1 for row in rows if row["intradayPathExpected"]
        )
        intraday_path_coverage_by_session: list[float] = []
        for session_rows in rows_by_session.values():
            expected = sum(1 for row in session_rows if row["pathExpected"])
            if expected:
                available = sum(
                    1
                    for row in session_rows
                    if row["pathExpected"] and row["pathAvailable"]
                )
                path_coverage_by_session.append(available / expected)
            intraday_expected = sum(
                1 for row in session_rows if row["intradayPathExpected"]
            )
            if intraday_expected:
                intraday_available = sum(
                    1
                    for row in session_rows
                    if row["intradayPathExpected"]
                    and row["intradayPathAvailable"]
                )
                intraday_path_coverage_by_session.append(
                    intraday_available / intraday_expected
                )
        path_coverage_rate = mean(path_coverage_by_session)
        intraday_path_coverage_rate = mean(intraday_path_coverage_by_session)
        path_coverage_ready = (
            intraday_path_expected_count == 0
            or (
                intraday_path_coverage_rate is not None
                and intraday_path_coverage_rate
                >= MIN_INTRADAY_PATH_COVERAGE_RATE
            )
        )
        return {
            "sampleCount": len(rows),
            "independentSessionCount": len(rows_by_session),
            "baseHitRate": session_weighted_mean(
                lambda row: 1.0 if row["baseHit"] else 0.0
            ),
            "envelopeHitRate": session_weighted_mean(
                lambda row: 1.0 if row["envelopeHit"] else 0.0
            ),
            "directionHitRate": session_weighted_mean(
                lambda row: 1.0 if row["directionHit"] else 0.0
            ),
            "pathExpectedCount": path_expected_count,
            "pathScoredCount": len(path_hits),
            "pathCoverageRate": path_coverage_rate,
            "intradayPathExpectedCount": intraday_path_expected_count,
            "intradayPathScoredCount": sum(
                1
                for row in rows
                if row["intradayPathExpected"]
                and row["intradayPathAvailable"]
            ),
            "intradayPathCoverageRate": intraday_path_coverage_rate,
            "pathSampleGate": "not_applicable"
            if path_expected_count == 0
            else "coverage_ready"
            if path_coverage_ready
            else "insufficient_coverage",
            "pathObservedHitRate": session_weighted_mean(
                lambda row: None
                if row["pathHit"] is None
                else 1.0
                if row["pathHit"]
                else 0.0
            ),
            "pathHitBestCaseRate": session_weighted_mean(
                lambda row: 1.0 if row["pathHitBestCase"] else 0.0
            )
            if path_expected_count
            else None,
            "pathHitLowerBoundRate": session_weighted_mean(
                lambda row: 1.0 if row["pathHitLowerBound"] else 0.0
            )
            if path_expected_count
            else None,
            "pathHitRate": session_weighted_mean(
                lambda row: 1.0 if row["pathHitLowerBound"] else 0.0
            )
            if path_expected_count and path_coverage_ready
            else None,
            "pathInsightEligible": path_expected_count > 0 and path_coverage_ready,
            "meanBaseIntervalScoreBps": session_weighted_mean(
                lambda row: row["baseIntervalScoreBps"]
            ),
            "meanCloseEnvelopeIntervalScoreBps": session_weighted_mean(
                lambda row: row["closeEnvelopeIntervalScoreBps"]
            ),
            "meanPathIntervalScoreBps": session_weighted_mean(
                lambda row: row["pathIntervalScoreBps"]
            )
            if path_coverage_ready
            else None,
            "meanMaxFavorableMoveBps": session_weighted_mean(
                lambda row: row["maxFavorableMoveBps"]
            )
            if path_coverage_ready
            else None,
            "meanMaxAdverseMoveBps": session_weighted_mean(
                lambda row: row["maxAdverseMoveBps"]
            )
            if path_coverage_ready
            else None,
            "meanCenterLiftVsCarryBps": session_weighted_mean(
                lambda row: row["centerLiftVsCarryBps"]
            ),
            "meanBrier": session_weighted_mean(lambda row: row["brier"]),
            "meanDataLagMinutes": session_weighted_mean(
                lambda row: row["dataLagMinutes"]
            ),
            "meanPublicationLagMinutes": session_weighted_mean(
                lambda row: row["publicationLagMinutes"]
            ),
            "meanDeployLagMinutes": session_weighted_mean(
                lambda row: row["deployLagMinutes"]
            ),
        }

    independent_sessions = len({score["sessionDate"] for score in scores})
    bucket_session_counts = {
        key: len({row["sessionDate"] for row in rows}) for key, rows in grouped.items()
    }
    return {
        "schemaVersion": 1,
        "generatedAt": generated_at,
        "selectedSettledForecastCount": len(scores),
        "independentSessionCount": independent_sessions,
        "unsettledForecastIds": sorted(unsettled_ids),
        "overall": aggregate(scores),
        "byEvaluationBucket": {
            key: {
                **aggregate(grouped[key]),
                "independentSessionCount": bucket_session_counts[key],
                "topErrorCodes": session_deduped_error_codes(grouped[key]),
                "sampleGate": "insufficient"
                if bucket_session_counts[key] < 10
                else "calibration_ready",
            }
            for key in sorted(grouped)
        },
        "topErrorCodes": session_deduped_error_codes(scores),
        "sampleGate": "insufficient" if independent_sessions < 10 else "calibration_ready",
        "hypotheses": hypothesis_summary,
        "activeHypothesisIds": [
            row["hypothesisId"] for row in hypothesis_summary if row["computedStatus"] == "active"
        ],
        "promotionBlockedHypotheses": [
            {
                "hypothesisId": row["hypothesisId"],
                "blockedUntil": row["promotionBlockedUntil"],
                "reason": row.get("promotionBlockReason"),
                "eligibleSessionCount": row.get("eligibleSessionCount"),
                "evaluableSessionCount": row.get("evaluableSessionCount"),
                "evidenceCoverageRate": row.get("evidenceCoverageRate"),
            }
            for row in hypothesis_summary
            if row.get("promotionBlocked")
        ],
        "scores": scores,
    }


def format_percent(value: float | None) -> str:
    return "—" if value is None else f"{value * 100:.1f}%"


def format_number(value: float | None, suffix: str = "") -> str:
    return "—" if value is None else f"{value:.2f}{suffix}"


def render_markdown(summary: dict[str, Any]) -> str:
    overall = summary["overall"]
    lines = [
        "# KOSPI 전망 누적 평가",
        "",
        f"- 평가 기준 시각: {summary['generatedAt'] or '—'}",
        f"- 선택된 정산 전망: {summary['selectedSettledForecastCount']}개",
        f"- 독립 정산 거래일: {summary['independentSessionCount']}개",
        f"- 표본 판정: {summary['sampleGate']}",
        f"- 미정산 전망: {len(summary['unsettledForecastIds'])}개",
        "",
        "## 전체 점수",
        "",
        "| 기본 범위 적중 | 전체 범위 적중 | 방향 적중 | 기본구간 점수 | 전체포락 점수 | 평균 Brier | 데이터 시차 | 발행 시차 | 배포 확인 시차 |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        "| "
        + " | ".join(
            [
                format_percent(overall["baseHitRate"]),
                format_percent(overall["envelopeHitRate"]),
                format_percent(overall["directionHitRate"]),
                format_number(overall["meanBaseIntervalScoreBps"], "bp"),
                format_number(overall["meanCloseEnvelopeIntervalScoreBps"], "bp"),
                format_number(overall["meanBrier"]),
                format_number(overall["meanDataLagMinutes"], "분"),
                format_number(overall["meanPublicationLagMinutes"], "분"),
                format_number(overall["meanDeployLagMinutes"], "분"),
            ]
        )
        + " |",
        "",
        "| 전체 경로 예상 표본 | 전체 확인 표본 | 장중 경로 예상 표본 | 장중 확인 표본 | 장중 자료 충족률 | 경로 표본 판정 | 확인 표본 적중 | 최선 적중률 | 누락 실패 하한 | 활성 판정 적중 | 경로구간 점수 | 평균 최대 유리 움직임 | 평균 최대 불리 움직임 | 현재가 유지 대비 중심값 개선 |",
        "|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        "| "
        + " | ".join(
            [
                str(overall["pathExpectedCount"]),
                str(overall["pathScoredCount"]),
                str(overall["intradayPathExpectedCount"]),
                str(overall["intradayPathScoredCount"]),
                format_percent(overall["intradayPathCoverageRate"]),
                overall["pathSampleGate"],
                format_percent(overall["pathObservedHitRate"]),
                format_percent(overall["pathHitBestCaseRate"]),
                format_percent(overall["pathHitLowerBoundRate"]),
                format_percent(overall["pathHitRate"]),
                format_number(overall["meanPathIntervalScoreBps"], "bp"),
                format_number(overall["meanMaxFavorableMoveBps"], "bp"),
                format_number(overall["meanMaxAdverseMoveBps"], "bp"),
                format_number(overall["meanCenterLiftVsCarryBps"], "bp"),
            ]
        )
        + " |",
        "",
        "## 시간대별",
        "",
        "| 평가 구간 | 독립 거래일 | 선택 전망 | 기본 적중 | 방향 적중 | 기본구간 점수 | 반복 오류 |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for bucket, row in summary["byEvaluationBucket"].items():
        bucket_errors = ", ".join(
            f"`{error['code']}` {error['count']}회"
            for error in row["topErrorCodes"]
        ) or "—"
        lines.append(
            f"| {bucket} | {row['independentSessionCount']} | {row['sampleCount']} | "
            f"{format_percent(row['baseHitRate'])} | {format_percent(row['directionHitRate'])} | "
            f"{format_number(row['meanBaseIntervalScoreBps'], 'bp')} | {bucket_errors} |"
        )
    lines.extend(["", "## 반복 오류", ""])
    if summary["topErrorCodes"]:
        lines.extend(f"- `{row['code']}`: {row['count']}회" for row in summary["topErrorCodes"])
    else:
        lines.append("- 정산된 오류 코드가 없습니다.")
    lines.extend(
        [
            "",
            "## 가설 증거 커버리지",
            "",
            "| 가설 | 적격 거래일 | 입력 검증 | 결과 feature | 평가 가능 | 커버리지 | 승격 게이트 |",
            "|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in summary["hypotheses"]:
        lines.append(
            f"| `{row['hypothesisId']}` | {row['eligibleSessionCount']} | "
            f"{row['verifiedInputSessionCount']} | {row['outcomeFeatureSessionCount']} | "
            f"{row['evaluableSessionCount']} | {format_percent(row['evidenceCoverageRate'])} | "
            f"{'충족' if row['promotionGateSatisfied'] else '미충족'} |"
        )
    lines.extend(["", "## 활성 가설", ""])
    if summary["activeHypothesisIds"]:
        lines.extend(f"- `{hypothesis_id}`" for hypothesis_id in summary["activeHypothesisIds"])
    else:
        lines.append("- 활성 가설이 없습니다.")
    lines.extend(["", "## 승격 차단", ""])
    if summary["promotionBlockedHypotheses"]:
        lines.extend(
            f"- `{row['hypothesisId']}`: `{row['blockedUntil']}` · "
            f"증거 {row['evaluableSessionCount']}/{row['eligibleSessionCount']} · "
            f"{row['reason'] or '게이트 미충족'}"
            for row in summary["promotionBlockedHypotheses"]
        )
    else:
        lines.append("- 승격이 차단된 가설이 없습니다.")
    if summary["independentSessionCount"] < 10:
        lines.extend(
            [
                "",
                "> 독립 표본이 10개 미만이므로 적중률을 성과나 우위로 해석하지 않는다. 현재 결과는 오류 분류용이다.",
            ]
        )
    return "\n".join(lines) + "\n"


def hypothesis_stage(
    independent_samples: int,
    *,
    baseline_lift: float | None = None,
    support_rate: float | None = None,
    regime_count: int = 0,
    recent_degraded: bool = False,
) -> str:
    if independent_samples < 10:
        return "candidate"
    if baseline_lift is not None and baseline_lift <= 0:
        return "retired"
    if recent_degraded:
        return "watch"
    if independent_samples < 20 or baseline_lift is None or support_rate is None:
        return "monitoring"
    if (
        baseline_lift >= MIN_ACTIVE_LIFT_BPS
        and support_rate >= MIN_ACTIVE_SUPPORT_RATE
        and regime_count >= 2
    ):
        return "active"
    return "checklist_candidate"


def apply_promotion_block(
    stage: str,
    promotion_blocked_until: str | None,
    promotion_gate_satisfied: bool = False,
) -> str:
    if promotion_blocked_until and not promotion_gate_satisfied and stage == "active":
        return "checklist_candidate"
    return stage


def hypothesis_required_for_forecast(
    definition: dict[str, Any], forecast: dict[str, Any]
) -> bool:
    if definition["status"] == "retired":
        retired_at = parse_iso(
            definition["lastReviewedAt"],
            f"hypothesis {definition['hypothesisId']} lastReviewedAt",
        )
        if forecast["issuedAtParsed"] >= retired_at:
            return False
    eligible_from_time = definition["eligibleFromTimeParsed"]
    return (
        forecast["evaluationBucket"] in definition["evaluationBuckets"]
        and forecast["marketRegime"] in definition["allowedRegimes"]
        and (
            eligible_from_time is None
            or forecast["dataCutoffAtParsed"].astimezone(SEOUL).time()
            >= eligible_from_time
        )
    )


def summarize_hypotheses(
    definitions: list[dict[str, Any]],
    forecasts_by_id: dict[str, dict[str, Any]],
    outcomes_by_id: dict[str, dict[str, Any]],
    eligible_forecast_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    definitions_by_id: dict[str, dict[str, Any]] = {}
    for row in definitions:
        if row.get("schemaVersion") != 1:
            raise ValidationError("hypothesis has unsupported schemaVersion")
        hypothesis_id = row.get("hypothesisId")
        if not isinstance(hypothesis_id, str) or not hypothesis_id or hypothesis_id in definitions_by_id:
            raise ValidationError("hypothesis ids must be unique non-empty strings")
        for field in ("statement", "requiredNext", "predictorVersion"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                raise ValidationError(f"hypothesis {hypothesis_id} needs {field}")
        parse_iso(row.get("lastReviewedAt"), f"hypothesis.{hypothesis_id}.lastReviewedAt")
        buckets = row.get("evaluationBuckets")
        if (
            not isinstance(buckets, list)
            or not buckets
            or any(bucket not in EVALUATION_BUCKETS for bucket in buckets)
        ):
            raise ValidationError(
                f"hypothesis {hypothesis_id} needs valid evaluationBuckets"
            )
        allowed_regimes = row.get("allowedRegimes")
        if (
            not isinstance(allowed_regimes, list)
            or not allowed_regimes
            or len(set(allowed_regimes)) != len(allowed_regimes)
            or any(regime not in HYPOTHESIS_REGIMES for regime in allowed_regimes)
        ):
            raise ValidationError(
                f"hypothesis {hypothesis_id} needs unique allowedRegimes from the fixed taxonomy"
            )
        eligible_from_time = row.get("eligibleFromTime")
        eligible_from_time_parsed = None
        if eligible_from_time is not None:
            try:
                eligible_from_time_parsed = datetime.strptime(
                    eligible_from_time, "%H:%M"
                ).time()
            except (TypeError, ValueError) as error:
                raise ValidationError(
                    f"hypothesis {hypothesis_id} eligibleFromTime must be HH:MM"
                ) from error
        promotion_blocked_until = row.get("promotionBlockedUntil")
        if promotion_blocked_until is not None and (
            not isinstance(promotion_blocked_until, str)
            or not promotion_blocked_until.strip()
        ):
            raise ValidationError(
                f"hypothesis {hypothesis_id} promotionBlockedUntil must be a non-empty contract id"
            )
        if promotion_blocked_until not in {None, FLOW_TRAJECTORY_CONTRACT}:
            raise ValidationError(
                f"hypothesis {hypothesis_id} uses an unsupported promotion contract"
            )
        required_input_anchors = row.get("requiredInputAnchors", [])
        required_input_metrics = row.get("requiredInputMetrics", [])
        required_outcome_features = row.get("requiredOutcomeFeatures", [])
        if (
            not isinstance(required_input_anchors, list)
            or len(set(required_input_anchors)) != len(required_input_anchors)
            or any(anchor not in FLOW_ANCHORS for anchor in required_input_anchors)
        ):
            raise ValidationError(
                f"hypothesis {hypothesis_id} has invalid requiredInputAnchors"
            )
        if (
            not isinstance(required_input_metrics, list)
            or len(set(required_input_metrics)) != len(required_input_metrics)
            or any(metric not in FLOW_METRICS for metric in required_input_metrics)
        ):
            raise ValidationError(
                f"hypothesis {hypothesis_id} has invalid requiredInputMetrics"
            )
        if (
            not isinstance(required_outcome_features, list)
            or len(set(required_outcome_features)) != len(required_outcome_features)
            or any(feature not in FLOW_FEATURE_IDS for feature in required_outcome_features)
        ):
            raise ValidationError(
                f"hypothesis {hypothesis_id} has invalid requiredOutcomeFeatures"
            )
        flow_required = hypothesis_id in FLOW_HYPOTHESIS_IDS
        if flow_required:
            canonical_contract = FLOW_HYPOTHESIS_CONTRACTS[hypothesis_id]
            contract_fields = {
                "evaluationBuckets": buckets,
                "eligibleFromTime": eligible_from_time,
                "predictorVersion": row["predictorVersion"],
                "requiredInputAnchors": required_input_anchors,
                "requiredInputMetrics": required_input_metrics,
                "requiredOutcomeFeatures": required_outcome_features,
            }
            for field, actual_value in contract_fields.items():
                expected_value = canonical_contract[field]
                if isinstance(expected_value, tuple):
                    expected_value = list(expected_value)
                if actual_value != expected_value:
                    raise ValidationError(
                        f"hypothesis {hypothesis_id} cannot weaken canonical "
                        f"{FLOW_TRAJECTORY_CONTRACT} field {field}"
                    )
        for feature in required_outcome_features:
            metric, _, start_anchor, _ = feature.split(".")
            if (
                metric not in required_input_metrics
                or start_anchor not in required_input_anchors
            ):
                raise ValidationError(
                    f"hypothesis {hypothesis_id} outcome feature is not anchored in its sealed inputs"
                )
        if flow_required and (
            promotion_blocked_until != FLOW_TRAJECTORY_CONTRACT
            or not required_input_anchors
            or not required_input_metrics
            or not required_outcome_features
        ):
            raise ValidationError(
                f"hypothesis {hypothesis_id} needs the complete flow_trajectory_v1 contract"
            )
        if not flow_required and any(
            (required_input_anchors, required_input_metrics, required_outcome_features)
        ):
            raise ValidationError(
                f"hypothesis {hypothesis_id} cannot declare flow trajectory requirements"
            )
        definitions_by_id[hypothesis_id] = {
            **row,
            "eligibleFromTimeParsed": eligible_from_time_parsed,
            "requiredInputAnchorsParsed": required_input_anchors,
            "requiredInputMetricsParsed": required_input_metrics,
            "requiredOutcomeFeaturesParsed": required_outcome_features,
            "flowTrajectoryRequired": flow_required,
        }

    for forecast in forecasts_by_id.values():
        for trial in forecast["hypothesisTrialsParsed"]:
            hypothesis_id = trial["hypothesisId"]
            if hypothesis_id not in definitions_by_id:
                raise ValidationError(f"forecast references unknown hypothesis {hypothesis_id}")
            if forecast["evaluationBucket"] not in definitions_by_id[hypothesis_id][
                "evaluationBuckets"
            ]:
                raise ValidationError(
                    f"hypothesis {hypothesis_id} cannot be tested in "
                    f"{forecast['evaluationBucket']}"
                )
            if trial["regime"] not in definitions_by_id[hypothesis_id]["allowedRegimes"]:
                raise ValidationError(
                    f"hypothesis {hypothesis_id} cannot use regime {trial['regime']}"
                )
            if trial["predictorVersion"] != definitions_by_id[hypothesis_id][
                "predictorVersion"
            ]:
                raise ValidationError(
                    f"hypothesis {hypothesis_id} predictorVersion does not match its definition"
                )
            definition = definitions_by_id[hypothesis_id]
            if definition["flowTrajectoryRequired"]:
                if trial["predictorInputStatus"] not in {"available", "missing"}:
                    raise ValidationError(
                        f"hypothesis {hypothesis_id} needs a sealed predictor input status"
                    )
                if trial["predictorInputStatus"] == "available":
                    predictor_anchor_names = set(
                        trial["predictorInputsParsed"]["anchors"]
                    )
                    if predictor_anchor_names != set(
                        definition["requiredInputAnchorsParsed"]
                    ):
                        raise ValidationError(
                            f"hypothesis {hypothesis_id} predictor anchors do not match its definition"
                        )

    if eligible_forecast_ids is not None:
        for forecast_id in sorted(eligible_forecast_ids):
            forecast = forecasts_by_id[forecast_id]
            expected_hypothesis_ids = {
                hypothesis_id
                for hypothesis_id, definition in definitions_by_id.items()
                if hypothesis_required_for_forecast(definition, forecast)
            }
            actual_hypothesis_ids = {
                trial["hypothesisId"] for trial in forecast["hypothesisTrialsParsed"]
            }
            if actual_hypothesis_ids != expected_hypothesis_ids:
                missing = sorted(expected_hypothesis_ids - actual_hypothesis_ids)
                unexpected = sorted(actual_hypothesis_ids - expected_hypothesis_ids)
                raise ValidationError(
                    f"selected forecast {forecast_id} hypothesis eligibility mismatch; "
                    f"missing={missing}, unexpected={unexpected}"
                )

    tests_by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for forecast_id, outcome in outcomes_by_id.items():
        if eligible_forecast_ids is not None and forecast_id not in eligible_forecast_ids:
            continue
        session_date = forecasts_by_id[forecast_id]["sessionDate"]
        for row in outcome["hypothesisTestsParsed"]:
            hypothesis_id = row["hypothesisId"]
            if hypothesis_id not in definitions_by_id:
                raise ValidationError(f"outcome references unknown hypothesis {hypothesis_id}")
            forecast_bucket = forecasts_by_id[forecast_id]["evaluationBucket"]
            if forecast_bucket not in definitions_by_id[hypothesis_id]["evaluationBuckets"]:
                raise ValidationError(
                    f"hypothesis {hypothesis_id} cannot be tested in {forecast_bucket}"
                )
            evidence_status = row.get("inputEvidenceStatus", "verified")
            if evidence_status == "verified" and any(
                outcome["flowFeaturesParsed"].get(feature) in {None, "unavailable"}
                for feature in definitions_by_id[hypothesis_id][
                    "requiredOutcomeFeaturesParsed"
                ]
            ):
                evidence_status = "missing_outcome_feature"
            tests_by_id[hypothesis_id].append({
                **row,
                "forecastId": forecast_id,
                "sessionDate": session_date,
                "evaluationBucket": forecast_bucket,
                "flowFeaturesParsed": outcome["flowFeaturesParsed"],
                "evidenceStatus": evidence_status,
            })

    summary: list[dict[str, Any]] = []
    for hypothesis_id, definition in sorted(definitions_by_id.items()):
        eligible_ids_for_hypothesis = {
            forecast_id
            for forecast_id in (eligible_forecast_ids or set(forecasts_by_id))
            if (
                forecasts_by_id[forecast_id]["evaluationBucket"]
                in definition["evaluationBuckets"]
                and forecasts_by_id[forecast_id]["marketRegime"]
                in definition["allowedRegimes"]
                and (
                    definition["eligibleFromTimeParsed"] is None
                    or forecasts_by_id[forecast_id]["dataCutoffAtParsed"]
                    .astimezone(SEOUL)
                    .time()
                    >= definition["eligibleFromTimeParsed"]
                )
            )
        }
        eligible_ids_by_session: dict[str, list[str]] = defaultdict(list)
        for forecast_id in eligible_ids_for_hypothesis:
            eligible_ids_by_session[forecasts_by_id[forecast_id]["sessionDate"]].append(
                forecast_id
            )
        eligible_sessions = set(eligible_ids_by_session)
        rows = sorted(
            tests_by_id[hypothesis_id],
            key=lambda row: (row["sessionDate"], row["forecastId"]),
        )
        rows_by_forecast = {row["forecastId"]: row for row in rows}
        verified_input_sessions: set[str] = set()
        outcome_feature_sessions: set[str] = set()
        evaluable_sessions: set[str] = set()
        evidence_status_counts: Counter[str] = Counter()
        for session_date, forecast_ids in eligible_ids_by_session.items():
            input_verified = True
            outcome_features_available = True
            for forecast_id in forecast_ids:
                test = rows_by_forecast.get(forecast_id)
                if test is None:
                    input_verified = False
                    outcome_features_available = False
                    evidence_status_counts["missing_outcome"] += 1
                    continue
                input_status = test.get("inputEvidenceStatus", "verified")
                if input_status != "verified":
                    input_verified = False
                    evidence_status_counts[input_status] += 1
                missing_feature = any(
                    test["flowFeaturesParsed"].get(feature) in {None, "unavailable"}
                    for feature in definition["requiredOutcomeFeaturesParsed"]
                )
                if missing_feature:
                    outcome_features_available = False
                    evidence_status_counts["missing_outcome_feature"] += 1
                elif input_status == "verified":
                    evidence_status_counts["verified"] += 1
            if input_verified:
                verified_input_sessions.add(session_date)
            if outcome_features_available:
                outcome_feature_sessions.add(session_date)
            if input_verified and outcome_features_available:
                evaluable_sessions.add(session_date)
        if not definition["flowTrajectoryRequired"]:
            verified_input_sessions = set(eligible_sessions)
            outcome_feature_sessions = set(eligible_sessions)
            evaluable_sessions = {
                row["sessionDate"] for row in rows
            }
        eligible_session_count = len(eligible_sessions)
        evaluable_session_count = len(evaluable_sessions)
        evidence_coverage_rate = (
            evaluable_session_count / eligible_session_count
            if eligible_session_count
            else None
        )
        rows = [
            row
            for row in rows
            if (
                not definition["flowTrajectoryRequired"]
                or row["sessionDate"] in evaluable_sessions
            )
        ]
        rows_by_session: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            rows_by_session[row["sessionDate"]].append(row)
        independent_sessions = len(rows_by_session)
        session_lifts = [
            mean(
                float(row["baselineLiftBpsParsed"])
                for row in session_rows
                if row.get("baselineLiftBpsParsed") is not None
            )
            for _, session_rows in sorted(rows_by_session.items())
        ]
        session_lifts = [value for value in session_lifts if value is not None]
        baseline_lift = mean(session_lifts)
        support_rate = mean(1.0 if value > 0 else 0.0 for value in session_lifts)
        rows_by_regime: dict[str, dict[str, list[float]]] = defaultdict(
            lambda: defaultdict(list)
        )
        for row in rows:
            if row.get("baselineLiftBpsParsed") is not None:
                rows_by_regime[row["regime"]][row["sessionDate"]].append(
                    float(row["baselineLiftBpsParsed"])
                )
        positive_regimes = set()
        for regime, regime_sessions in rows_by_regime.items():
            regime_lifts = [mean(values) for values in regime_sessions.values()]
            regime_lifts = [value for value in regime_lifts if value is not None]
            if (
                len(regime_lifts) >= MIN_ACTIVE_REGIME_SESSIONS
                and (mean(regime_lifts) or 0) > 0
            ):
                positive_regimes.add(regime)
        recent_lifts = session_lifts[-10:]
        recent_degraded = len(recent_lifts) >= 5 and (mean(recent_lifts) or 0) <= 0
        statistical_status = hypothesis_stage(
            independent_sessions,
            baseline_lift=baseline_lift,
            support_rate=support_rate,
            regime_count=len(positive_regimes),
            recent_degraded=recent_degraded,
        )
        promotion_blocked_until = definition.get("promotionBlockedUntil")
        promotion_gate_satisfied = True
        promotion_block_reason = None
        if promotion_blocked_until == FLOW_TRAJECTORY_CONTRACT:
            recent_eligible_sessions = sorted(eligible_sessions)[
                -FLOW_PROMOTION_RECENT_SESSIONS:
            ]
            promotion_gate_satisfied = (
                len(recent_eligible_sessions) == FLOW_PROMOTION_RECENT_SESSIONS
                and all(
                    session_date in evaluable_sessions
                    for session_date in recent_eligible_sessions
                )
            )
            if len(recent_eligible_sessions) < FLOW_PROMOTION_RECENT_SESSIONS:
                promotion_block_reason = (
                    f"최근 적격 거래일 {len(recent_eligible_sessions)}/"
                    f"{FLOW_PROMOTION_RECENT_SESSIONS}"
                )
            elif not promotion_gate_satisfied:
                complete_count = sum(
                    session_date in evaluable_sessions
                    for session_date in recent_eligible_sessions
                )
                promotion_block_reason = (
                    f"최근 {FLOW_PROMOTION_RECENT_SESSIONS}거래일 완전 증거 "
                    f"{complete_count}/{FLOW_PROMOTION_RECENT_SESSIONS}"
                )
        computed_status = apply_promotion_block(
            statistical_status,
            promotion_blocked_until,
            promotion_gate_satisfied,
        )
        declared_status = definition.get("status")
        if declared_status != computed_status:
            raise ValidationError(
                f"hypothesis {hypothesis_id} declares {declared_status}, expected {computed_status}"
            )
        summary.append(
            {
                "hypothesisId": hypothesis_id,
                "computedStatus": computed_status,
                "statisticalStatus": statistical_status,
                "promotionBlockedUntil": promotion_blocked_until,
                "promotionBlocked": bool(
                    promotion_blocked_until and not promotion_gate_satisfied
                ),
                "promotionGateSatisfied": promotion_gate_satisfied,
                "promotionBlockReason": promotion_block_reason,
                "eligibleSessionCount": eligible_session_count,
                "verifiedInputSessionCount": len(verified_input_sessions),
                "outcomeFeatureSessionCount": len(outcome_feature_sessions),
                "evaluableSessionCount": evaluable_session_count,
                "evidenceCoverageRate": evidence_coverage_rate,
                "evidenceStatusCounts": dict(sorted(evidence_status_counts.items())),
                "independentSessionCount": independent_sessions,
                "meanBaselineLiftBps": baseline_lift,
                "supportRate": support_rate,
                "positiveRegimeCount": len(positive_regimes),
                "recentDegraded": recent_degraded,
            }
        )
    return summary


def evaluate(evaluation_root: Path, repo_root: Path | None) -> dict[str, Any]:
    forecasts_by_id: dict[str, dict[str, Any]] = {}
    for path, payload in load_json_files(evaluation_root / "forecasts"):
        forecast = validate_forecast(payload, path, repo_root)
        forecast_id = forecast["forecastId"]
        if forecast_id in forecasts_by_id:
            raise ValidationError(f"duplicate forecastId: {forecast_id}")
        forecasts_by_id[forecast_id] = forecast
    if forecasts_by_id:
        trading_sessions = load_trading_session_sequence(
            evaluation_root / "trading-sessions.json"
        )
        validate_forecast_session_sequence(forecasts_by_id.values(), trading_sessions)
    actuals_by_date: dict[str, dict[str, Any]] = {}
    for path, payload in load_json_files(evaluation_root / "actuals"):
        actual = validate_actual(payload, path)
        session_date = actual["sessionDate"]
        if session_date in actuals_by_date:
            raise ValidationError(f"duplicate actual for {session_date}")
        actuals_by_date[session_date] = actual

    outcomes_by_id: dict[str, dict[str, Any]] = {}
    for path, payload in load_json_files(evaluation_root / "outcomes"):
        forecast_id = payload.get("forecastId")
        if forecast_id not in forecasts_by_id:
            raise ValidationError(f"{path}: outcome has no matching forecast")
        if forecast_id in outcomes_by_id:
            raise ValidationError(f"duplicate outcome for {forecast_id}")
        actual_ref = payload.get("actualRef")
        if actual_ref not in actuals_by_date:
            raise ValidationError(f"{path}: outcome has no matching actual archive")
        outcomes_by_id[forecast_id] = validate_outcome(
            payload,
            path,
            forecasts_by_id[forecast_id],
            actuals_by_date[actual_ref],
        )

    publication_events: dict[tuple[str, str], dict[str, Any]] = {}
    for path, payload in load_json_files(evaluation_root / "publications"):
        forecast_id = payload.get("forecastId")
        if forecast_id not in forecasts_by_id:
            raise ValidationError(f"{path}: publication event has no matching forecast")
        event = validate_publication_event(
            payload, path, forecasts_by_id[forecast_id]
        )
        event_key = (forecast_id, event["eventType"])
        if event_key in publication_events:
            raise ValidationError(
                f"duplicate publication event {event['eventType']} for {forecast_id}"
            )
        publication_events[event_key] = event

    publications_by_id: dict[str, dict[str, Any]] = {}
    for forecast_id in forecasts_by_id:
        forecast = forecasts_by_id[forecast_id]
        pushed = publication_events.get((forecast_id, "pushed"))
        deployed = publication_events.get((forecast_id, "deploy_verified"))
        if forecast["visibility"] == "public" and (pushed is None or deployed is None):
            raise ValidationError(
                f"public forecast {forecast_id} needs pushed and deploy_verified events"
            )
        if forecast["visibility"] == "internal" and (pushed is not None or deployed is not None):
            raise ValidationError(
                f"internal forecast {forecast_id} cannot have publication events"
            )
        if deployed is not None and pushed is None:
            raise ValidationError(f"deploy event has no push event for {forecast_id}")
        if pushed is None:
            continue
        if deployed is not None and deployed["occurredAtParsed"] < pushed["occurredAtParsed"]:
            raise ValidationError(f"deploy event precedes push event for {forecast_id}")
        if (
            deployed is not None
            and deployed["commitShaParsed"] != pushed["commitShaParsed"]
        ):
            raise ValidationError(
                f"deploy event commitSha differs from the pushed revision for {forecast_id}"
            )
        validate_forecast_at_commit(
            repo_root, forecast, pushed["commitShaParsed"]
        )
        publications_by_id[forecast_id] = {
            "pushedAtParsed": pushed["occurredAtParsed"],
            "deployVerifiedAtParsed": None
            if deployed is None
            else deployed["occurredAtParsed"],
            "commitSha": pushed["commitShaParsed"],
            "contentHash": pushed["contentHashParsed"],
            "availabilityStatus": None
            if deployed is None
            else deployed["availabilityStatusParsed"],
            "publicUrl": None if deployed is None else deployed["publicUrlParsed"],
        }

    selected_forecasts = select_aggregate_forecasts(
        forecasts_by_id, publications_by_id
    )

    hypothesis_definitions = load_jsonl(evaluation_root / "hypotheses.jsonl")
    hypothesis_summary = summarize_hypotheses(
        hypothesis_definitions,
        forecasts_by_id,
        outcomes_by_id,
        {forecast["forecastId"] for forecast in selected_forecasts},
    )

    scores = [
        score_pair(
            forecast,
            outcomes_by_id[forecast["forecastId"]],
            publications_by_id.get(forecast["forecastId"]),
        )
        for forecast in selected_forecasts
        if forecast["forecastId"] in outcomes_by_id
    ]
    unsettled = [
        forecast["forecastId"]
        for forecast in selected_forecasts
        if forecast["forecastId"] not in outcomes_by_id
    ]
    event_times: list[datetime] = []
    event_times.extend(forecast["issuedAtParsed"] for forecast in forecasts_by_id.values())
    event_times.extend(actual["fetchedAtParsed"] for actual in actuals_by_date.values())
    event_times.extend(outcome["recordedAtParsed"] for outcome in outcomes_by_id.values())
    event_times.extend(event["occurredAtParsed"] for event in publication_events.values())
    event_times.extend(
        parse_iso(row["lastReviewedAt"], "hypothesis.lastReviewedAt")
        for row in hypothesis_definitions
    )
    generated_at = max(event_times).astimezone(SEOUL).isoformat(timespec="seconds") if event_times else None
    return build_summary(
        scores,
        unsettled,
        generated_at=generated_at,
        hypothesis_summary=hypothesis_summary,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluation-root", type=Path, default=DEFAULT_EVALUATION_ROOT)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    return parser.parse_args()


def main() -> int:
    reconfigure_stdout = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure_stdout):
        reconfigure_stdout(encoding="utf-8", errors="replace")
    args = parse_args()
    try:
        summary = evaluate(args.evaluation_root, args.repo_root)
    except ValidationError as error:
        print(f"evaluation error: {error}")
        return 1
    rendered_json = json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    rendered_md = render_markdown(summary)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(rendered_json, encoding="utf-8")
    if args.output_md:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(rendered_md, encoding="utf-8")
    if not args.output_json and not args.output_md:
        print(rendered_md, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
