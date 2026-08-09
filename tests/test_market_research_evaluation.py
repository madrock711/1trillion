import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "evaluate_market_research.py"
SPEC = importlib.util.spec_from_file_location("market_research_evaluation", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class MarketResearchEvaluationTests(unittest.TestCase):
    def make_report(self, root: Path, name: str = "sample.md") -> tuple[str, str]:
        path = root / "reports" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# sealed report\n", encoding="utf-8")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        return path.relative_to(root).as_posix(), digest

    def make_forecast(self, root: Path, forecast_id: str = "2026-08-07-0911-same-close"):
        report_path, report_hash = self.make_report(root)
        forecast = {
            "schemaVersion": 1,
            "forecastId": forecast_id,
            "visibility": "public",
            "reportPath": report_path,
            "reportSha256": report_hash,
            "issuedAt": "2026-08-07T09:12:00+09:00",
            "dataCutoffAt": "2026-08-07T09:11:00+09:00",
            "marketState": "intraday",
            "marketRegime": "risk_off",
            "evaluationBucket": "open_0900_0930",
            "target": {
                "sessionDate": "2026-08-07",
                "horizon": "session_close",
                "instrument": "KOSPI",
                "leadSessions": 0,
                "previousSessionDate": "2026-08-06",
            },
            "reference": {
                "price": 6385.43,
                "asOf": "2026-08-07T09:11:00+09:00",
                "kind": "live",
            },
            "scenarios": {
                "bull": {"low": 6400, "high": 6500, "probability": 0.25},
                "base": {"low": 6300, "high": 6400, "probability": 0.55},
                "bear": {"low": 6220, "high": 6300, "probability": 0.20},
            },
            "closeEnvelopeCoverage": 0.90,
            "pathEnvelope": {"low": 6180, "high": 6550, "coverage": 0.90},
            "drivers": [
                {
                    "id": "domestic-flow",
                    "rank": 1,
                    "claim": "외국인 현물 수급이 유지된다.",
                    "validationMetric": "외국인 현물 30분·60분·종가 누적값",
                },
                {
                    "id": "semiconductor-price",
                    "rank": 2,
                    "claim": "반도체 대형주가 지수 하단을 지지한다.",
                    "validationMetric": "삼성전자·SK하이닉스 종가 위치",
                },
            ],
            "scenarioTriggers": {
                "bull": {
                    "logic": "AND",
                    "observeBy": "2026-08-07T15:20:00+09:00",
                    "conditions": [
                        {
                            "id": "bull-flow",
                            "description": "외국인 현물 매수 유지",
                            "metricId": "foreign_cash",
                            "operator": "gt",
                            "threshold": 0,
                            "source": "fixture-flow",
                        }
                    ],
                },
                "base": {
                    "logic": "AND",
                    "observeBy": "2026-08-07T15:20:00+09:00",
                    "conditions": [
                        {
                            "id": "base-support",
                            "description": "기준선 종가 방어",
                            "metricId": "kospi_price",
                            "operator": "gte",
                            "threshold": 6300,
                            "source": "fixture-price",
                        }
                    ],
                },
                "bear": {
                    "logic": "OR",
                    "observeBy": "2026-08-07T15:20:00+09:00",
                    "conditions": [
                        {
                            "id": "bear-reversal",
                            "description": "외국인 현물 매도 반전",
                            "metricId": "foreign_cash",
                            "operator": "lt",
                            "threshold": 0,
                            "source": "fixture-flow",
                        }
                    ],
                },
            },
            "posture": {"attack": 30, "wait": 50, "defense": 20},
            "supersedes": None,
        }
        return self.seal_forecast(forecast)

    def seal_forecast(self, forecast: dict):
        forecast["contentHash"] = MODULE.canonical_forecast_content_hash(forecast)
        return forecast

    def make_actual(self):
        return {
            "schemaVersion": 1,
            "sessionDate": "2026-08-07",
            "bizdate": "20260807",
            "fetchedAt": "2026-08-07T18:10:00+09:00",
            "marketStatus": "CLOSE",
            "kospi": {
                "open": 6365.07,
                "high": 6415.60,
                "low": 6238.32,
                "close": 6258.71,
                "asOf": "2026-08-07T15:30:00+09:00",
                "source": "fixture",
                "rawHash": "a" * 64,
            },
            "closeSnapshot": None,
            "closeSnapshotMissingReason": "fixture keeps only OHLC",
            "flowTrajectory": None,
            "flowTrajectoryMissingEvidence": {
                "sourceStatus": "unavailable",
                "source": "fixture-flow",
                "asOf": "2026-08-07T15:30:00+09:00",
                "fetchedAt": "2026-08-07T18:09:00+09:00",
                "missingReason": "base fixture omits the flow trajectory",
                "rawHash": "6" * 64,
            },
        }

    def make_close_snapshot(self):
        metadata = {
            "asOf": "2026-08-07T15:30:00+09:00",
            "source": "fixture-close",
            "rawHash": "b" * 64,
        }
        return {
            "kodex": {
                "open": 92000,
                "high": 95830,
                "low": 87660,
                "close": 90690,
                "volume": 17937175,
                **metadata,
            },
            "cashFlow": {
                "foreign": -8651,
                "institution": 5854,
                "personal": 2675,
                "unit": "억원",
                **metadata,
            },
            "program": {
                "arbitrage": 120,
                "nonArbitrage": 2251,
                "total": 2371,
                "unit": "억원",
                **metadata,
            },
            "breadth": {
                "up": 557,
                "flat": 36,
                "down": 322,
                "unit": "종목",
                **metadata,
            },
        }

    def make_flow_anchor(
        self,
        anchor: str,
        *,
        foreign_cash: float,
        program_non_arbitrage: float,
        program_total: float,
    ):
        anchor_times = {
            "open30": "09:30:00",
            "open60": "10:00:00",
            "at1400": "14:00:00",
            "close": "15:30:00",
        }
        hash_chars = {
            "open30": "1",
            "open60": "2",
            "at1400": "3",
            "close": "4",
        }
        return {
            "status": "available",
            "asOf": f"2026-08-07T{anchor_times[anchor]}+09:00",
            "foreignCash": foreign_cash,
            "programNonArbitrage": program_non_arbitrage,
            "programTotal": program_total,
            "source": f"fixture-flow-{anchor}",
            "rawHash": hash_chars[anchor] * 64,
        }

    def make_missing_flow_anchor(self, anchor: str = "at1400"):
        anchor_times = {
            "open30": "09:30:00",
            "open60": "10:00:00",
            "at1400": "14:00:00",
            "close": "15:30:00",
        }
        return {
            "status": "missing",
            "expectedAsOf": f"2026-08-07T{anchor_times[anchor]}+09:00",
            "attemptedAt": f"2026-08-07T{anchor_times[anchor]}+09:00",
            "sourceStatus": "unavailable",
            "source": f"fixture-flow-{anchor}",
            "missingReason": "fixture source did not expose the anchor",
            "rawHash": "8" * 64,
        }

    def make_flow_trajectory(self):
        return {
            "contract": "flow_trajectory_v1",
            "unit": "억원",
            "anchors": {
                "open30": self.make_flow_anchor(
                    "open30",
                    foreign_cash=-100,
                    program_non_arbitrage=-20,
                    program_total=-30,
                ),
                "open60": self.make_flow_anchor(
                    "open60",
                    foreign_cash=-150,
                    program_non_arbitrage=-30,
                    program_total=-50,
                ),
                "at1400": self.make_flow_anchor(
                    "at1400",
                    foreign_cash=50,
                    program_non_arbitrage=40,
                    program_total=70,
                ),
                "close": self.make_flow_anchor(
                    "close",
                    foreign_cash=-8651,
                    program_non_arbitrage=2251,
                    program_total=2371,
                ),
            },
        }

    def make_actual_with_flow(self):
        actual = self.make_actual()
        actual["closeSnapshot"] = self.make_close_snapshot()
        actual.pop("closeSnapshotMissingReason")
        actual["flowTrajectory"] = self.make_flow_trajectory()
        actual.pop("flowTrajectoryMissingEvidence")
        return actual

    def make_predictor_inputs(self, anchor_names):
        trajectory = self.make_flow_trajectory()
        anchors = {}
        for anchor_name in anchor_names:
            anchors[anchor_name] = {
                key: value
                for key, value in trajectory["anchors"][anchor_name].items()
                if key != "status"
            }
        payload = {
            "asOf": max(anchor["asOf"] for anchor in anchors.values()),
            "anchors": anchors,
        }
        payload["canonicalHash"] = MODULE.canonical_object_hash(payload)
        return payload

    def make_flow_trial(
        self,
        hypothesis_id: str,
        predictor_version: str,
        anchor_names,
    ):
        return {
            "hypothesisId": hypothesis_id,
            "regime": "risk_off",
            "candidatePrediction": 6260,
            "baselineId": "reference_carry",
            "predictorVersion": predictor_version,
            "inputStatus": "available",
            "predictorInputs": self.make_predictor_inputs(anchor_names),
        }

    def make_flow_hypothesis_definition(
        self,
        hypothesis_id: str = "domestic-flow-persistence",
        *,
        status: str = "candidate",
    ):
        if hypothesis_id == "domestic-flow-persistence":
            buckets = ["morning_0931_1130"]
            eligible_from = "10:00"
            required_anchors = ["open30", "open60"]
            predictor_version = "domestic-flow-persistence-v1"
            required_features = [
                "foreignCash.persistence.open30.open60",
                "foreignCash.delta.open60.close",
                "programNonArbitrage.delta.open60.close",
                "programTotal.delta.open60.close",
            ]
        else:
            buckets = ["afternoon_1131_1500", "closing_1501_1529"]
            eligible_from = "14:00"
            required_anchors = ["at1400"]
            predictor_version = "late-session-flow-acceleration-v1"
            required_features = [
                "foreignCash.delta.at1400.close",
                "foreignCash.persistence.at1400.close",
                "programNonArbitrage.delta.at1400.close",
                "programTotal.delta.at1400.close",
            ]
        return {
            "schemaVersion": 1,
            "hypothesisId": hypothesis_id,
            "status": status,
            "evaluationBuckets": buckets,
            "eligibleFromTime": eligible_from,
            "allowedRegimes": ["risk_on", "risk_off", "mixed", "event_shock"],
            "statement": "flow_trajectory_v1 evidence contract fixture",
            "requiredNext": "20 independent eligible sessions",
            "predictorVersion": predictor_version,
            "promotionBlockedUntil": "flow_trajectory_v1",
            "requiredInputAnchors": required_anchors,
            "requiredInputMetrics": [
                "foreignCash",
                "programNonArbitrage",
                "programTotal",
            ],
            "requiredOutcomeFeatures": required_features,
            "lastReviewedAt": "2026-08-10T00:00:00+09:00",
        }

    def set_intraday_forecast_time(
        self,
        forecast: dict,
        *,
        issued_at: str,
        data_cutoff_at: str,
        evaluation_bucket: str,
    ):
        forecast.update(
            {
                "issuedAt": issued_at,
                "dataCutoffAt": data_cutoff_at,
                "evaluationBucket": evaluation_bucket,
            }
        )
        forecast["reference"]["asOf"] = data_cutoff_at
        return forecast

    def make_missing_path_evidence(self):
        return {
            "sourceStatus": "unavailable",
            "source": "fixture-minute-bars",
            "asOf": "2026-08-07T15:30:00+09:00",
            "fetchedAt": "2026-08-07T18:10:30+09:00",
            "rawHash": "9" * 64,
        }

    def make_outcome(self, forecast_id: str = "2026-08-07-0911-same-close"):
        return {
            "schemaVersion": 1,
            "forecastId": forecast_id,
            "recordedAt": "2026-08-07T18:11:00+09:00",
            "actualRef": "2026-08-07",
            "realizedScenario": "bear",
            "errorCodes": ["late_session_reversal_missed"],
            "triggerResults": [
                {
                    "id": "bull-flow",
                    "status": "not_observed",
                    "observedAt": "2026-08-07T15:20:00+09:00",
                    "observedValue": -8651,
                    "source": "fixture-flow",
                },
                {
                    "id": "base-support",
                    "status": "not_observed",
                    "observedAt": "2026-08-07T15:20:00+09:00",
                    "observedValue": 6258.71,
                    "source": "fixture-price",
                },
                {
                    "id": "bear-reversal",
                    "status": "observed",
                    "observedAt": "2026-08-07T15:20:00+09:00",
                    "observedValue": -8651,
                    "source": "fixture-flow",
                },
            ],
            "driverAssessment": [
                {"id": "domestic-flow", "status": "confirmed"},
                {"id": "semiconductor-price", "status": "partial"},
            ],
            "postForecastPathStatus": "available",
            "postForecastPath": {
                "from": "2026-08-07T09:12:00+09:00",
                "asOf": "2026-08-07T15:30:00+09:00",
                "fetchedAt": "2026-08-07T18:10:30+09:00",
                "intervalMinutes": 1,
                "high": 6410.0,
                "low": 6238.32,
                "source": "fixture-minute-bars",
                "rawHash": "c" * 64,
            },
        }

    def make_publication_events(
        self,
        forecast_id: str = "2026-08-07-0911-same-close",
        content_hash: str | None = None,
        commit_sha: str = "e" * 40,
    ):
        content_hash = content_hash or "f" * 64
        return [
            {
                "schemaVersion": 1,
                "forecastId": forecast_id,
                "eventType": "pushed",
                "occurredAt": "2026-08-07T09:14:00+09:00",
                "contentHash": content_hash,
                "commitSha": commit_sha,
            },
            {
                "schemaVersion": 1,
                "forecastId": forecast_id,
                "eventType": "deploy_verified",
                "occurredAt": "2026-08-07T09:16:00+09:00",
                "contentHash": content_hash,
                "commitSha": commit_sha,
                "availabilityStatus": "available",
                "publicUrl": "https://www.hpmplab.com/articles/market-test.html",
            },
        ]

    def write_record(self, directory: Path, payload: dict):
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{payload['forecastId']}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def write_trading_sessions(self, evaluation: Path, sessions=None):
        payload = {
            "schemaVersion": 1,
            "asOf": "2026-08-10T00:00:00+09:00",
            "source": "fixture-calendar",
            "rawHash": "d" * 64,
            "sessions": sessions or ["2026-08-06", "2026-08-07"],
        }
        evaluation.mkdir(parents=True, exist_ok=True)
        (evaluation / "trading-sessions.json").write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8"
        )

    def test_scores_sealed_forecast_and_outcome(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            evaluation = root / "research" / "evaluation"
            forecast = self.make_forecast(root)
            actual = self.make_actual()
            outcome = self.make_outcome()
            self.write_record(evaluation / "forecasts", forecast)
            self.write_trading_sessions(evaluation)
            (evaluation / "actuals").mkdir(parents=True, exist_ok=True)
            (evaluation / "actuals" / "2026-08-07.json").write_text(
                json.dumps(actual, ensure_ascii=False), encoding="utf-8"
            )
            self.write_record(evaluation / "outcomes", outcome)
            (evaluation / "publications").mkdir(parents=True, exist_ok=True)
            for event in self.make_publication_events(
                content_hash=forecast["contentHash"]
            ):
                event_path = (
                    evaluation
                    / "publications"
                    / f"{event['forecastId']}-{event['eventType']}.json"
                )
                event_path.write_text(
                    json.dumps(event, ensure_ascii=False), encoding="utf-8"
                )
            summary = MODULE.evaluate(evaluation, root)
            self.assertEqual(summary["selectedSettledForecastCount"], 1)
            self.assertEqual(summary["independentSessionCount"], 1)
            self.assertFalse(summary["scores"][0]["baseHit"])
            self.assertTrue(summary["scores"][0]["envelopeHit"])
            self.assertEqual(summary["scores"][0]["dataLagMinutes"], 1.0)
            self.assertEqual(summary["scores"][0]["publicationLagMinutes"], 2.0)
            self.assertEqual(summary["scores"][0]["deployLagMinutes"], 2.0)
            self.assertTrue(summary["scores"][0]["pathHit"])
            self.assertIn("centerLiftVsCarryBps", summary["scores"][0])
            self.assertEqual(summary["sampleGate"], "insufficient")

    def test_rejects_probability_and_posture_conflation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            forecast = self.make_forecast(root)
            forecast["scenarios"]["base"]["probability"] = 0.45
            with self.assertRaisesRegex(MODULE.ValidationError, "probabilities must sum to 1"):
                MODULE.validate_forecast(forecast, root / "forecast.json", root)
            forecast = self.make_forecast(root, "second")
            forecast["posture"]["attack"] = 40
            with self.assertRaisesRegex(MODULE.ValidationError, "posture values"):
                MODULE.validate_forecast(forecast, root / "forecast.json", root)

    def test_forecast_cannot_contain_post_close_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            forecast = self.make_forecast(root)
            forecast["actual"] = {"close": 6258.71}
            with self.assertRaisesRegex(MODULE.ValidationError, "post-close fields"):
                MODULE.validate_forecast(forecast, root / "forecast.json", root)

    def test_revision_leaf_is_selected_without_mutating_the_original(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first_payload = self.make_forecast(root, "first")
            first_payload["visibility"] = "internal"
            self.seal_forecast(first_payload)
            first = MODULE.validate_forecast(first_payload, root / "first.json", root)
            second_payload = self.make_forecast(root, "second")
            second_payload["visibility"] = "internal"
            second_payload["supersedes"] = "first"
            second_payload["dataCutoffAt"] = "2026-08-07T09:13:00+09:00"
            second_payload["issuedAt"] = "2026-08-07T09:14:00+09:00"
            second_payload["reference"]["asOf"] = "2026-08-07T09:13:00+09:00"
            self.seal_forecast(second_payload)
            second = MODULE.validate_forecast(second_payload, root / "second.json", root)
            selected = MODULE.select_aggregate_forecasts({"first": first, "second": second})
            self.assertEqual([row["forecastId"] for row in selected], ["second"])
            third_payload = self.make_forecast(root, "third")
            third_payload["visibility"] = "internal"
            third_payload["supersedes"] = "first"
            third_payload["dataCutoffAt"] = "2026-08-07T09:15:00+09:00"
            third_payload["issuedAt"] = "2026-08-07T09:16:00+09:00"
            third_payload["reference"]["asOf"] = "2026-08-07T09:15:00+09:00"
            self.seal_forecast(third_payload)
            third = MODULE.validate_forecast(third_payload, root / "third.json", root)
            with self.assertRaisesRegex(MODULE.ValidationError, "branches"):
                MODULE.select_aggregate_forecasts(
                    {"first": first, "second": second, "third": third}
                )

    def test_actual_archive_requires_post_close_timestamp(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            actual = self.make_actual()
            actual["kospi"]["asOf"] = "2026-08-07T14:00:00+09:00"
            with self.assertRaisesRegex(MODULE.ValidationError, "15:30 KST"):
                MODULE.validate_actual(actual, root / "actual.json")

    def test_close_snapshot_requires_final_values_and_source_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            actual = self.make_actual_with_flow()
            validated = MODULE.validate_actual(actual, root / "actual.json")
            self.assertEqual(validated["closeSnapshotParsed"]["cashFlow"]["foreign"], -8651)
            actual["closeSnapshot"]["program"]["total"] = 1000
            with self.assertRaisesRegex(MODULE.ValidationError, "does not match"):
                MODULE.validate_actual(actual, root / "actual.json")

    def test_same_session_forecast_cannot_be_sealed_after_close(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            forecast = self.make_forecast(root)
            forecast["issuedAt"] = "2026-08-07T15:31:00+09:00"
            with self.assertRaisesRegex(MODULE.ValidationError, "before 15:30 KST"):
                MODULE.validate_forecast(forecast, root / "forecast.json", root)

    def test_publication_is_recorded_as_append_only_events(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            forecast = MODULE.validate_forecast(
                self.make_forecast(root), root / "forecast.json", root
            )
            pushed, deployed = self.make_publication_events(
                content_hash=forecast["contentHash"]
            )
            pushed_event = MODULE.validate_publication_event(
                pushed, root / "pushed.json", forecast
            )
            deployed_event = MODULE.validate_publication_event(
                deployed, root / "deployed.json", forecast
            )
            self.assertEqual(pushed_event["eventType"], "pushed")
            self.assertGreater(
                deployed_event["occurredAtParsed"], pushed_event["occurredAtParsed"]
            )

    def test_first_deployed_public_edition_remains_the_aggregate_representative(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = MODULE.validate_forecast(
                self.make_forecast(root, "first-public"), root / "first.json", root
            )
            second_payload = self.make_forecast(root, "second-public")
            second_payload["supersedes"] = "first-public"
            second_payload["issuedAt"] = "2026-08-07T09:14:00+09:00"
            second_payload["dataCutoffAt"] = "2026-08-07T09:13:00+09:00"
            second_payload["reference"]["asOf"] = "2026-08-07T09:13:00+09:00"
            self.seal_forecast(second_payload)
            second = MODULE.validate_forecast(
                second_payload, root / "second.json", root
            )
            publications = {
                "first-public": {
                    "pushedAtParsed": MODULE.parse_iso(
                        "2026-08-07T09:16:00+09:00", "first-push"
                    )
                },
                "second-public": {
                    "pushedAtParsed": MODULE.parse_iso(
                        "2026-08-07T09:15:00+09:00", "second-push"
                    )
                },
            }
            selected = MODULE.select_aggregate_forecasts(
                {"first-public": first, "second-public": second}, publications
            )
            self.assertEqual(
                [row["forecastId"] for row in selected], ["second-public"]
            )

    def test_deploy_verification_is_time_bucket_and_availability_gated(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            forecast = MODULE.validate_forecast(
                self.make_forecast(root), root / "forecast.json", root
            )
            _, deployed = self.make_publication_events(
                content_hash=forecast["contentHash"]
            )
            deployed["occurredAt"] = "2026-08-07T09:23:00+09:00"
            with self.assertRaisesRegex(MODULE.ValidationError, "maximum is 10"):
                MODULE.validate_publication_event(
                    deployed, root / "late-deploy.json", forecast
                )
            deployed["occurredAt"] = "2026-08-07T09:16:00+09:00"
            deployed["availabilityStatus"] = "unavailable"
            with self.assertRaisesRegex(MODULE.ValidationError, "must be available"):
                MODULE.validate_publication_event(
                    deployed, root / "unavailable-deploy.json", forecast
                )

    def test_forecast_content_hash_detects_post_issue_edit(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            forecast = self.make_forecast(root)
            forecast["drivers"][0]["claim"] = "사후에 바뀐 설명"
            with self.assertRaisesRegex(MODULE.ValidationError, "contentHash"):
                MODULE.validate_forecast(forecast, root / "forecast.json", root)

    def test_push_and_deploy_must_reference_the_same_commit(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            evaluation = root / "research" / "evaluation"
            forecast = self.make_forecast(root)
            self.write_record(evaluation / "forecasts", forecast)
            self.write_trading_sessions(evaluation)
            pushed, deployed = self.make_publication_events(
                content_hash=forecast["contentHash"]
            )
            deployed["commitSha"] = "1" * 40
            (evaluation / "publications").mkdir(parents=True, exist_ok=True)
            for event in (pushed, deployed):
                (evaluation / "publications" / f"{event['eventType']}.json").write_text(
                    json.dumps(event, ensure_ascii=False), encoding="utf-8"
                )
            with self.assertRaisesRegex(MODULE.ValidationError, "commitSha differs"):
                MODULE.evaluate(evaluation, root)

    def test_pushed_commit_must_contain_the_sealed_report(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".git").mkdir()
            payload = self.make_forecast(root)
            forecast_path = (
                root
                / "research"
                / "evaluation"
                / "forecasts"
                / f"{payload['forecastId']}.json"
            )
            forecast = MODULE.validate_forecast(payload, forecast_path, root)
            committed_forecast = MODULE.subprocess.CompletedProcess(
                [], 0, stdout=json.dumps(payload, ensure_ascii=False), stderr=""
            )
            missing_report = MODULE.subprocess.CompletedProcess(
                [], 128, stdout=b"", stderr=b"missing"
            )
            with patch.object(
                MODULE.subprocess,
                "run",
                side_effect=[committed_forecast, missing_report],
            ):
                with self.assertRaisesRegex(
                    MODULE.ValidationError, "does not contain report"
                ):
                    MODULE.validate_forecast_at_commit(root, forecast, "e" * 40)

    def test_pushed_commit_report_must_match_the_sealed_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".git").mkdir()
            payload = self.make_forecast(root)
            forecast_path = (
                root
                / "research"
                / "evaluation"
                / "forecasts"
                / f"{payload['forecastId']}.json"
            )
            forecast = MODULE.validate_forecast(payload, forecast_path, root)
            committed_forecast = MODULE.subprocess.CompletedProcess(
                [], 0, stdout=json.dumps(payload, ensure_ascii=False), stderr=""
            )
            changed_report = MODULE.subprocess.CompletedProcess(
                [], 0, stdout=b"# changed after sealing\n", stderr=b""
            )
            with patch.object(
                MODULE.subprocess,
                "run",
                side_effect=[committed_forecast, changed_report],
            ):
                with self.assertRaisesRegex(
                    MODULE.ValidationError, "report differs from reportSha256"
                ):
                    MODULE.validate_forecast_at_commit(root, forecast, "e" * 40)

    def test_outcome_scenario_is_derived_from_close(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            forecast = MODULE.validate_forecast(
                self.make_forecast(root), root / "forecast.json", root
            )
            actual = MODULE.validate_actual(self.make_actual(), root / "actual.json")
            outcome = self.make_outcome()
            outcome["realizedScenario"] = "base"
            with self.assertRaisesRegex(MODULE.ValidationError, "expected bear"):
                MODULE.validate_outcome(outcome, root / "outcome.json", forecast, actual)

    def test_intraday_path_is_not_scored_without_post_forecast_bars(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            forecast = MODULE.validate_forecast(
                self.make_forecast(root), root / "forecast.json", root
            )
            actual = MODULE.validate_actual(self.make_actual(), root / "actual.json")
            outcome_payload = self.make_outcome()
            outcome_payload.pop("postForecastPath")
            outcome_payload["postForecastPathStatus"] = "missing"
            outcome_payload["postForecastPathMissingReason"] = "fixture has no bars"
            outcome_payload["postForecastPathMissingEvidence"] = (
                self.make_missing_path_evidence()
            )
            outcome = MODULE.validate_outcome(
                outcome_payload, root / "outcome.json", forecast, actual
            )
            score = MODULE.score_pair(forecast, outcome)
            self.assertIsNone(score["pathHit"])
            self.assertIsNone(score["maxAdverseMoveBps"])

    def test_intraday_path_cannot_include_pre_issue_bars(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            forecast = MODULE.validate_forecast(
                self.make_forecast(root), root / "forecast.json", root
            )
            actual = MODULE.validate_actual(self.make_actual(), root / "actual.json")
            outcome_payload = self.make_outcome()
            outcome_payload["postForecastPath"]["from"] = "2026-08-07T09:11:00+09:00"
            with self.assertRaisesRegex(MODULE.ValidationError, "before the forecast was issued"):
                MODULE.validate_outcome(
                    outcome_payload, root / "outcome.json", forecast, actual
                )

    def test_intraday_path_must_reach_and_contain_the_close(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            forecast = MODULE.validate_forecast(
                self.make_forecast(root), root / "forecast.json", root
            )
            actual = MODULE.validate_actual(self.make_actual(), root / "actual.json")
            outcome_payload = self.make_outcome()
            outcome_payload["postForecastPath"]["low"] = 6300
            with self.assertRaisesRegex(MODULE.ValidationError, "does not contain the close"):
                MODULE.validate_outcome(
                    outcome_payload, root / "outcome.json", forecast, actual
                )

    def test_tail_close_is_scored_as_bear_or_bull_for_brier(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            forecast = MODULE.validate_forecast(
                self.make_forecast(root), root / "forecast.json", root
            )
            self.assertEqual(MODULE.classify_close(6100, forecast["scenariosParsed"]), "bear")
            self.assertEqual(MODULE.classify_close(6700, forecast["scenariosParsed"]), "bull")

            actual_payload = self.make_actual()
            actual_payload["kospi"].update({"high": 6710.0, "close": 6700.0})
            actual = MODULE.validate_actual(actual_payload, root / "actual.json")
            outcome_payload = self.make_outcome()
            outcome_payload["realizedScenario"] = "bull"
            outcome_payload["postForecastPath"].update({"high": 6710.0})
            outcome = MODULE.validate_outcome(
                outcome_payload, root / "outcome.json", forecast, actual
            )
            score = MODULE.score_pair(forecast, outcome)
            self.assertIsNotNone(score["brier"])
            self.assertGreater(score["closeEnvelopeIntervalScoreBps"], 0)

    def test_bucket_must_match_issue_time(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            forecast = self.make_forecast(root)
            forecast["evaluationBucket"] = "preopen"
            with self.assertRaisesRegex(MODULE.ValidationError, "expected open_0900_0930"):
                MODULE.validate_forecast(forecast, root / "forecast.json", root)

    def test_evaluation_bucket_uses_issue_time_and_rejects_stale_data(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            forecast = self.make_forecast(root)
            forecast["issuedAt"] = "2026-08-07T09:40:00+09:00"
            forecast["evaluationBucket"] = "morning_0931_1130"
            with self.assertRaisesRegex(MODULE.ValidationError, "maximum is 20"):
                MODULE.validate_forecast(forecast, root / "forecast.json", root)

    def test_interval_coverage_is_fixed_for_comparable_scores(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            forecast = self.make_forecast(root)
            forecast["closeEnvelopeCoverage"] = 0.75
            with self.assertRaisesRegex(MODULE.ValidationError, "fixed at 0.9"):
                MODULE.validate_forecast(forecast, root / "forecast.json", root)

    def test_trigger_status_is_derived_from_sealed_threshold(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            forecast = MODULE.validate_forecast(
                self.make_forecast(root), root / "forecast.json", root
            )
            actual = MODULE.validate_actual(self.make_actual(), root / "actual.json")
            outcome = self.make_outcome()
            outcome["triggerResults"][0]["status"] = "observed"
            with self.assertRaisesRegex(MODULE.ValidationError, "expected not_observed"):
                MODULE.validate_outcome(
                    outcome, root / "outcome.json", forecast, actual
                )

    def test_scenario_logic_derives_trigger_false_positive_and_missed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            forecast = MODULE.validate_forecast(
                self.make_forecast(root), root / "forecast.json", root
            )
            actual = MODULE.validate_actual(self.make_actual(), root / "actual.json")
            outcome_payload = self.make_outcome()
            outcome_payload["triggerResults"][0].update(
                {"status": "observed", "observedValue": 100}
            )
            outcome_payload["triggerResults"][2].update(
                {"status": "not_observed", "observedValue": 100}
            )
            outcome = MODULE.validate_outcome(
                outcome_payload, root / "outcome.json", forecast, actual
            )
            self.assertEqual(outcome["triggerScenarioStatusParsed"]["bull"], "observed")
            self.assertEqual(outcome["triggerScenarioStatusParsed"]["bear"], "not_observed")
            self.assertIn("trigger_false_positive", outcome["errorCodesParsed"])
            self.assertIn("trigger_missed", outcome["errorCodesParsed"])

    def test_publication_completeness_is_required_only_for_public_forecasts(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            evaluation = root / "research" / "evaluation"
            public_forecast = self.make_forecast(root)
            self.write_record(evaluation / "forecasts", public_forecast)
            self.write_trading_sessions(evaluation)
            with self.assertRaisesRegex(MODULE.ValidationError, "needs pushed"):
                MODULE.evaluate(evaluation, root)

            public_forecast["visibility"] = "internal"
            self.seal_forecast(public_forecast)
            self.write_record(evaluation / "forecasts", public_forecast)
            summary = MODULE.evaluate(evaluation, root)
            self.assertEqual(summary["unsettledForecastIds"], [public_forecast["forecastId"]])
            validated = MODULE.validate_forecast(
                public_forecast, root / "forecast.json", root
            )
            pushed = self.make_publication_events(
                content_hash=public_forecast["contentHash"]
            )[0]
            with self.assertRaisesRegex(MODULE.ValidationError, "internal forecast"):
                MODULE.validate_publication_event(
                    pushed, root / "pushed.json", validated
                )

    def test_intraday_path_missing_is_explicit_and_blocks_path_aggregate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            forecast = MODULE.validate_forecast(
                self.make_forecast(root), root / "forecast.json", root
            )
            actual = MODULE.validate_actual(self.make_actual(), root / "actual.json")
            missing_payload = self.make_outcome()
            missing_payload.pop("postForecastPath")
            missing_payload.pop("postForecastPathStatus")
            with self.assertRaisesRegex(MODULE.ValidationError, "postForecastPathStatus"):
                MODULE.validate_outcome(
                    missing_payload, root / "outcome.json", forecast, actual
                )
            missing_payload["postForecastPathStatus"] = "missing"
            missing_payload["postForecastPathMissingReason"] = "source bars unavailable"
            with self.assertRaisesRegex(
                MODULE.ValidationError, "postForecastPathMissingEvidence"
            ):
                MODULE.validate_outcome(
                    missing_payload, root / "outcome.json", forecast, actual
                )
            missing_payload["postForecastPathMissingEvidence"] = (
                self.make_missing_path_evidence()
            )
            outcome = MODULE.validate_outcome(
                missing_payload, root / "outcome.json", forecast, actual
            )
            score = MODULE.score_pair(forecast, outcome)
            summary = MODULE.build_summary(
                [score],
                [],
                generated_at="2026-08-07T18:11:00+09:00",
                hypothesis_summary=[],
            )
            self.assertEqual(summary["overall"]["pathCoverageRate"], 0.0)
            self.assertEqual(summary["overall"]["intradayPathExpectedCount"], 1)
            self.assertEqual(summary["overall"]["intradayPathScoredCount"], 0)
            self.assertEqual(summary["overall"]["intradayPathCoverageRate"], 0.0)
            self.assertEqual(
                summary["overall"]["pathSampleGate"], "insufficient_coverage"
            )
            self.assertEqual(summary["overall"]["pathHitBestCaseRate"], 1.0)
            self.assertEqual(summary["overall"]["pathHitLowerBoundRate"], 0.0)
            self.assertIsNone(summary["overall"]["pathHitRate"])

    def test_live_reference_must_be_fresh(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            forecast = self.make_forecast(root)
            forecast["reference"]["asOf"] = "2026-08-07T09:00:00+09:00"
            with self.assertRaisesRegex(MODULE.ValidationError, "live reference"):
                MODULE.validate_forecast(forecast, root / "forecast.json", root)

    def test_overall_metrics_weight_each_session_equally(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            forecast = MODULE.validate_forecast(
                self.make_forecast(root), root / "forecast.json", root
            )
            actual = MODULE.validate_actual(self.make_actual(), root / "actual.json")
            outcome = MODULE.validate_outcome(
                self.make_outcome(), root / "outcome.json", forecast, actual
            )
            first = MODULE.score_pair(forecast, outcome)
            same_session = {
                **first,
                "forecastId": "same-session-second-bucket",
                "evaluationBucket": "morning_0931_1130",
                "baseHit": not first["baseHit"],
            }
            next_session = {
                **first,
                "forecastId": "next-session",
                "sessionDate": "2026-08-08",
                "baseHit": True,
            }
            summary = MODULE.build_summary(
                [first, same_session, next_session],
                [],
                generated_at="2026-08-08T18:11:00+09:00",
                hypothesis_summary=[],
            )
            self.assertAlmostEqual(summary["overall"]["baseHitRate"], 0.75)

    def test_bucket_error_codes_are_session_deduped_and_rendered(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            forecast = MODULE.validate_forecast(
                self.make_forecast(root), root / "forecast.json", root
            )
            actual = MODULE.validate_actual(self.make_actual(), root / "actual.json")
            outcome = MODULE.validate_outcome(
                self.make_outcome(), root / "outcome.json", forecast, actual
            )
            first = {
                **MODULE.score_pair(forecast, outcome),
                "errorCodes": ["direction_wrong", "data_stale"],
            }
            same_session = {
                **first,
                "forecastId": "same-session-revision",
                "errorCodes": ["direction_wrong"],
            }
            next_session = {
                **first,
                "forecastId": "next-session",
                "sessionDate": "2026-08-08",
                "errorCodes": ["direction_wrong"],
            }
            summary = MODULE.build_summary(
                [first, same_session, next_session],
                [],
                generated_at="2026-08-08T18:11:00+09:00",
                hypothesis_summary=[],
            )
            bucket = summary["byEvaluationBucket"]["open_0900_0930"]
            self.assertEqual(
                bucket["topErrorCodes"],
                [
                    {"code": "direction_wrong", "count": 2},
                    {"code": "data_stale", "count": 1},
                ],
            )
            rendered = MODULE.render_markdown(summary)
            self.assertIn("`direction_wrong` 2회", rendered)
            self.assertIn("`data_stale` 1회", rendered)

    def test_only_current_or_next_trading_session_may_be_targeted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            forecast = self.make_forecast(root)
            forecast.update(
                {
                    "visibility": "internal",
                    "issuedAt": "2026-08-07T16:00:00+09:00",
                    "dataCutoffAt": "2026-08-07T15:55:00+09:00",
                    "marketState": "postclose",
                    "evaluationBucket": "postclose",
                }
            )
            forecast["target"].update(
                {
                    "sessionDate": "2026-08-14",
                    "previousSessionDate": "2026-08-07",
                    "leadSessions": 1,
                }
            )
            forecast["reference"].update(
                {
                    "asOf": "2026-08-07T15:30:00+09:00",
                    "kind": "previous_close",
                }
            )
            for scenario in ("bull", "base", "bear"):
                forecast["scenarioTriggers"][scenario][
                    "observeBy"
                ] = "2026-08-14T15:20:00+09:00"
            self.seal_forecast(forecast)
            MODULE.validate_forecast(forecast, root / "forecast.json", root)
            evaluation = root / "research" / "evaluation"
            self.write_record(evaluation / "forecasts", forecast)
            self.write_trading_sessions(
                evaluation,
                [
                    "2026-08-07",
                    "2026-08-10",
                    "2026-08-11",
                    "2026-08-12",
                    "2026-08-13",
                    "2026-08-14",
                ],
            )
            with self.assertRaisesRegex(MODULE.ValidationError, "expected 2026-08-13"):
                MODULE.evaluate(evaluation, root)

            postclose = self.make_forecast(root, "2026-08-06-postclose-next")
            postclose.update(
                {
                    "issuedAt": "2026-08-06T16:00:00+09:00",
                    "dataCutoffAt": "2026-08-06T15:55:00+09:00",
                    "marketState": "postclose",
                    "evaluationBucket": "postclose",
                }
            )
            postclose["target"]["leadSessions"] = 1
            postclose["reference"].update(
                {
                    "asOf": "2026-08-06T15:30:00+09:00",
                    "kind": "previous_close",
                }
            )
            self.seal_forecast(postclose)
            validated = MODULE.validate_forecast(
                postclose, root / "postclose.json", root
            )
            self.assertEqual(validated["evaluationBucket"], "postclose")

    def test_sample_gate_counts_unique_sessions_not_forecast_editions(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            forecast = MODULE.validate_forecast(
                self.make_forecast(root), root / "forecast.json", root
            )
            actual = MODULE.validate_actual(self.make_actual(), root / "actual.json")
            outcome = MODULE.validate_outcome(
                self.make_outcome(), root / "outcome.json", forecast, actual
            )
            score = MODULE.score_pair(forecast, outcome)
            second_score = {**score, "forecastId": "second", "evaluationBucket": "morning_0931_1130"}
            summary = MODULE.build_summary(
                [score, second_score],
                [],
                generated_at="2026-08-07T18:11:00+09:00",
                hypothesis_summary=[],
            )
            self.assertEqual(summary["selectedSettledForecastCount"], 2)
            self.assertEqual(summary["independentSessionCount"], 1)
            self.assertEqual(summary["sampleGate"], "insufficient")

    def test_hypothesis_status_cannot_be_promoted_without_evidence(self):
        definition = {
            "schemaVersion": 1,
            "hypothesisId": "manual-active",
            "status": "active",
            "evaluationBuckets": ["open_0900_0930"],
            "allowedRegimes": ["risk_on", "risk_off"],
            "statement": "수급 유지가 방향을 설명한다.",
            "requiredNext": "독립 표본을 누적한다.",
            "lastReviewedAt": "2026-08-10T00:00:00+09:00",
            "predictorVersion": "v1",
        }
        with self.assertRaisesRegex(MODULE.ValidationError, "expected candidate"):
            MODULE.summarize_hypotheses([definition], {}, {})

    def test_flow_hypotheses_remain_promotion_blocked_until_v1_evidence_exists(self):
        self.assertEqual(
            MODULE.apply_promotion_block("active", "flow_trajectory_v1"),
            "checklist_candidate",
        )
        self.assertEqual(
            MODULE.apply_promotion_block("monitoring", "flow_trajectory_v1"),
            "monitoring",
        )

    def test_hypothesis_eligibility_respects_the_sealed_input_cutoff_time(self):
        definition = self.make_flow_hypothesis_definition()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            before_payload = self.make_forecast(root, "before-1000")
            before_payload.update(
                {
                    "issuedAt": "2026-08-07T09:59:00+09:00",
                    "dataCutoffAt": "2026-08-07T09:59:00+09:00",
                    "evaluationBucket": "morning_0931_1130",
                }
            )
            before_payload["reference"]["asOf"] = "2026-08-07T09:59:00+09:00"
            self.seal_forecast(before_payload)
            before = MODULE.validate_forecast(
                before_payload, root / "before.json", root
            )
            MODULE.summarize_hypotheses(
                [definition], {before["forecastId"]: before}, {}, {before["forecastId"]}
            )

            eligible_payload = self.make_forecast(root, "at-1000")
            eligible_payload.update(
                {
                    "issuedAt": "2026-08-07T10:01:00+09:00",
                    "dataCutoffAt": "2026-08-07T10:00:00+09:00",
                    "evaluationBucket": "morning_0931_1130",
                }
            )
            eligible_payload["reference"]["asOf"] = "2026-08-07T10:00:00+09:00"
            self.seal_forecast(eligible_payload)
            eligible = MODULE.validate_forecast(
                eligible_payload, root / "eligible.json", root
            )
            with self.assertRaisesRegex(MODULE.ValidationError, "eligibility mismatch"):
                MODULE.summarize_hypotheses(
                    [definition],
                    {eligible["forecastId"]: eligible},
                    {},
                    {eligible["forecastId"]},
                )

    def test_every_eligible_selected_forecast_must_seal_the_predictor_version(self):
        definition = self.make_flow_hypothesis_definition()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            forecast_payload = self.make_forecast(root)
            self.set_intraday_forecast_time(
                forecast_payload,
                issued_at="2026-08-07T10:01:00+09:00",
                data_cutoff_at="2026-08-07T10:00:00+09:00",
                evaluation_bucket="morning_0931_1130",
            )
            self.seal_forecast(forecast_payload)
            forecast = MODULE.validate_forecast(
                forecast_payload, root / "forecast.json", root
            )
            with self.assertRaisesRegex(MODULE.ValidationError, "eligibility mismatch"):
                MODULE.summarize_hypotheses(
                    [definition],
                    {forecast["forecastId"]: forecast},
                    {},
                    {forecast["forecastId"]},
                )

            versioned_payload = self.make_forecast(root, "versioned")
            self.set_intraday_forecast_time(
                versioned_payload,
                issued_at="2026-08-07T10:01:00+09:00",
                data_cutoff_at="2026-08-07T10:00:00+09:00",
                evaluation_bucket="morning_0931_1130",
            )
            versioned_payload["hypothesisTrials"] = [
                self.make_flow_trial(
                    "domestic-flow-persistence",
                    "domestic-flow-persistence-v2",
                    ("open30", "open60"),
                )
            ]
            self.seal_forecast(versioned_payload)
            versioned = MODULE.validate_forecast(
                versioned_payload, root / "versioned.json", root
            )
            with self.assertRaisesRegex(MODULE.ValidationError, "predictorVersion"):
                MODULE.summarize_hypotheses(
                    [definition],
                    {versioned["forecastId"]: versioned},
                    {},
                    {versioned["forecastId"]},
                )

    def test_flow_hypothesis_definition_cannot_weaken_canonical_contract(self):
        mutations = {
            "evaluationBuckets": ["open_0900_0930"],
            "eligibleFromTime": "09:30",
            "predictorVersion": "domestic-flow-persistence-v0",
            "requiredInputAnchors": ["open30"],
            "requiredInputMetrics": ["foreignCash"],
            "requiredOutcomeFeatures": [
                "foreignCash.persistence.open30.open60"
            ],
        }
        for field, weakened_value in mutations.items():
            with self.subTest(field=field):
                definition = self.make_flow_hypothesis_definition()
                definition[field] = weakened_value
                with self.assertRaisesRegex(
                    MODULE.ValidationError,
                    f"canonical flow_trajectory_v1 field {field}",
                ):
                    MODULE.summarize_hypotheses([definition], {}, {})

    def test_hypothesis_predictions_must_be_sealed_before_the_outcome(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            forecast_payload = self.make_forecast(root)
            forecast_payload["hypothesisTrials"] = [
                {
                    "hypothesisId": "us-chip-signal-overweight",
                    "regime": "risk_off",
                    "candidatePrediction": 6260,
                    "baselineId": "reference_carry",
                    "predictorVersion": "v1",
                }
            ]
            self.seal_forecast(forecast_payload)
            forecast = MODULE.validate_forecast(
                forecast_payload, root / "forecast.json", root
            )
            actual = MODULE.validate_actual(self.make_actual(), root / "actual.json")
            outcome_payload = self.make_outcome()
            outcome_payload["hypothesisTests"] = [
                {"hypothesisId": "us-chip-signal-overweight", "result": "supported"}
            ]
            outcome = MODULE.validate_outcome(
                outcome_payload, root / "outcome.json", forecast, actual
            )
            self.assertGreater(
                outcome["hypothesisTestsParsed"][0]["baselineLiftBpsParsed"], 0
            )
            outcome_payload["hypothesisTests"][0]["candidatePrediction"] = 6258.71
            with self.assertRaisesRegex(MODULE.ValidationError, "may only record"):
                MODULE.validate_outcome(
                    outcome_payload, root / "outcome.json", forecast, actual
                )

    def test_hypothesis_cannot_choose_a_strawman_baseline_or_freeform_regime(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            forecast = self.make_forecast(root)
            forecast["hypothesisTrials"] = [
                {
                    "hypothesisId": "domestic-flow-persistence",
                    "regime": "made-up-regime",
                    "candidatePrediction": 6260,
                    "baselineId": "arbitrary_bad_prediction",
                    "predictorVersion": "v1",
                }
            ]
            with self.assertRaisesRegex(MODULE.ValidationError, "invalid regime"):
                MODULE.validate_forecast(forecast, root / "forecast.json", root)
            forecast["hypothesisTrials"][0]["regime"] = "risk_off"
            with self.assertRaisesRegex(MODULE.ValidationError, "invalid baselineId"):
                MODULE.validate_forecast(forecast, root / "forecast.json", root)

    def test_hypothesis_promotion_requires_samples_baseline_and_regimes(self):
        self.assertEqual(MODULE.hypothesis_stage(9), "candidate")
        self.assertEqual(MODULE.hypothesis_stage(12, baseline_lift=0.1), "monitoring")
        self.assertEqual(MODULE.hypothesis_stage(12, baseline_lift=-0.1), "retired")
        self.assertEqual(
            MODULE.hypothesis_stage(
                20, baseline_lift=9.9, support_rate=0.8, regime_count=2
            ),
            "checklist_candidate",
        )
        self.assertEqual(
            MODULE.hypothesis_stage(
                20, baseline_lift=10.0, support_rate=0.6, regime_count=2
            ),
            "active",
        )
        self.assertEqual(
            MODULE.hypothesis_stage(
                20,
                baseline_lift=10.0,
                support_rate=0.6,
                regime_count=2,
                recent_degraded=True,
            ),
            "watch",
        )

    def test_flow_trajectory_v1_derives_every_forward_pair_feature(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            actual = MODULE.validate_actual(
                self.make_actual_with_flow(), root / "actual.json"
            )
            features = actual["flowFeaturesParsed"]
            expected_feature_names = {
                f"{metric}.{feature_kind}.{start}.{end}"
                for start_index, start in enumerate(MODULE.FLOW_ANCHORS)
                for end in MODULE.FLOW_ANCHORS[start_index + 1 :]
                for metric in MODULE.FLOW_METRICS
                for feature_kind in ("delta", "persistence")
            }
            self.assertEqual(set(features), expected_feature_names)
            self.assertEqual(features["foreignCash.delta.open30.open60"], -50)
            self.assertEqual(
                features["foreignCash.persistence.open30.open60"],
                "strengthening",
            )
            self.assertEqual(
                features["foreignCash.persistence.open60.at1400"],
                "reversal",
            )
            self.assertEqual(
                features["programTotal.persistence.at1400.close"],
                "strengthening",
            )

    def test_flow_trajectory_anchor_available_and_missing_schemas_are_strict(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            payload = self.make_actual_with_flow()
            payload["flowTrajectory"]["anchors"][
                "at1400"
            ] = self.make_missing_flow_anchor("at1400")
            validated = MODULE.validate_actual(payload, root / "actual.json")
            self.assertEqual(
                validated["flowTrajectoryParsed"]["anchors"]["at1400"]["status"],
                "missing",
            )
            self.assertEqual(
                validated["flowFeaturesParsed"][
                    "foreignCash.persistence.open60.at1400"
                ],
                "unavailable",
            )

            malformed_available = self.make_actual_with_flow()
            malformed_available["flowTrajectory"]["anchors"]["open30"][
                "missingReason"
            ] = "not allowed on an available anchor"
            with self.assertRaises(MODULE.ValidationError):
                MODULE.validate_actual(
                    malformed_available, root / "malformed-available.json"
                )

            malformed_missing = self.make_actual_with_flow()
            malformed_missing["flowTrajectory"]["anchors"][
                "at1400"
            ] = self.make_missing_flow_anchor("at1400")
            malformed_missing["flowTrajectory"]["anchors"]["at1400"].pop(
                "rawHash"
            )
            with self.assertRaises(MODULE.ValidationError):
                MODULE.validate_actual(
                    malformed_missing, root / "malformed-missing.json"
                )

    def test_flow_trajectory_close_anchor_must_match_close_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            payload = self.make_actual_with_flow()
            payload["flowTrajectory"]["anchors"]["close"]["foreignCash"] = -8000
            with self.assertRaises(MODULE.ValidationError):
                MODULE.validate_actual(payload, root / "actual.json")

    def test_available_flow_close_is_rejected_when_close_snapshot_is_missing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            payload = self.make_actual_with_flow()
            payload["closeSnapshot"] = None
            payload["closeSnapshotMissingReason"] = "fixture omits the final snapshot"
            with self.assertRaisesRegex(
                MODULE.ValidationError,
                "flowTrajectory close must be missing when closeSnapshot is missing",
            ):
                MODULE.validate_actual(payload, root / "actual.json")

    def test_predictor_inputs_require_canonical_hash_and_respect_data_cutoff(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            payload = self.make_forecast(root, "domestic-at-1000")
            self.set_intraday_forecast_time(
                payload,
                issued_at="2026-08-07T10:01:00+09:00",
                data_cutoff_at="2026-08-07T10:00:00+09:00",
                evaluation_bucket="morning_0931_1130",
            )
            payload["hypothesisTrials"] = [
                self.make_flow_trial(
                    "domestic-flow-persistence",
                    "domestic-flow-persistence-v1",
                    ("open30", "open60"),
                )
            ]
            self.seal_forecast(payload)
            validated = MODULE.validate_forecast(
                payload, root / "forecast.json", root
            )
            trial = validated["hypothesisTrialsParsed"][0]
            self.assertEqual(trial["predictorInputStatus"], "available")
            self.assertEqual(
                trial["predictorInputsParsed"]["canonicalHash"],
                payload["hypothesisTrials"][0]["predictorInputs"]["canonicalHash"],
            )

            stale_hash = json.loads(json.dumps(payload))
            stale_hash["hypothesisTrials"][0]["predictorInputs"]["anchors"][
                "open60"
            ]["foreignCash"] = -151
            self.seal_forecast(stale_hash)
            with self.assertRaises(MODULE.ValidationError):
                MODULE.validate_forecast(
                    stale_hash, root / "stale-hash.json", root
                )

            after_cutoff = json.loads(json.dumps(payload))
            after_cutoff["hypothesisTrials"][0]["predictorInputs"][
                "asOf"
            ] = "2026-08-07T10:01:00+09:00"
            predictor_inputs = after_cutoff["hypothesisTrials"][0][
                "predictorInputs"
            ]
            predictor_inputs["canonicalHash"] = MODULE.canonical_object_hash(
                predictor_inputs
            )
            self.seal_forecast(after_cutoff)
            with self.assertRaises(MODULE.ValidationError):
                MODULE.validate_forecast(
                    after_cutoff, root / "after-cutoff.json", root
                )

    def test_predictor_input_comparison_reports_all_evidence_statuses(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            payload = self.make_forecast(root, "domestic-compare")
            self.set_intraday_forecast_time(
                payload,
                issued_at="2026-08-07T10:01:00+09:00",
                data_cutoff_at="2026-08-07T10:00:00+09:00",
                evaluation_bucket="morning_0931_1130",
            )
            payload["hypothesisTrials"] = [
                self.make_flow_trial(
                    "domestic-flow-persistence",
                    "domestic-flow-persistence-v1",
                    ("open30", "open60"),
                )
            ]
            self.seal_forecast(payload)
            forecast = MODULE.validate_forecast(
                payload, root / "forecast.json", root
            )
            actual = MODULE.validate_actual(
                self.make_actual_with_flow(), root / "actual.json"
            )
            trial = forecast["hypothesisTrialsParsed"][0]
            self.assertEqual(
                MODULE.compare_predictor_inputs(
                    trial, actual["flowTrajectoryParsed"]
                ),
                "verified",
            )

            mismatched = json.loads(json.dumps(trial, default=str))
            mismatched["predictorInputsParsed"]["anchors"]["open60"][
                "foreignCash"
            ] = -151
            self.assertEqual(
                MODULE.compare_predictor_inputs(
                    mismatched, actual["flowTrajectoryParsed"]
                ),
                "input_mismatch",
            )
            self.assertEqual(
                MODULE.compare_predictor_inputs(trial, None),
                "missing_actual",
            )

            missing_payload = self.make_forecast(root, "domestic-missing-input")
            self.set_intraday_forecast_time(
                missing_payload,
                issued_at="2026-08-07T10:01:00+09:00",
                data_cutoff_at="2026-08-07T10:00:00+09:00",
                evaluation_bucket="morning_0931_1130",
            )
            missing_payload["hypothesisTrials"] = [
                {
                    "hypothesisId": "domestic-flow-persistence",
                    "regime": "risk_off",
                    "candidatePrediction": 6260,
                    "baselineId": "reference_carry",
                    "predictorVersion": "domestic-flow-persistence-v1",
                    "inputStatus": "missing",
                    "missingInputEvidence": {
                        "sourceStatus": "unavailable",
                        "source": "fixture-flow",
                        "asOf": "2026-08-07T10:00:00+09:00",
                        "fetchedAt": "2026-08-07T10:00:00+09:00",
                        "rawHash": "7" * 64,
                    },
                }
            ]
            self.seal_forecast(missing_payload)
            missing_forecast = MODULE.validate_forecast(
                missing_payload, root / "missing-forecast.json", root
            )
            self.assertEqual(
                MODULE.compare_predictor_inputs(
                    missing_forecast["hypothesisTrialsParsed"][0],
                    actual["flowTrajectoryParsed"],
                ),
                "missing_input",
            )

    def test_domestic_flow_trial_becomes_eligible_at_1000_with_required_anchors(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            before = self.make_forecast(root, "domestic-before-1000")
            self.set_intraday_forecast_time(
                before,
                issued_at="2026-08-07T09:59:00+09:00",
                data_cutoff_at="2026-08-07T09:59:00+09:00",
                evaluation_bucket="morning_0931_1130",
            )
            before["hypothesisTrials"] = [
                self.make_flow_trial(
                    "domestic-flow-persistence",
                    "domestic-flow-persistence-v1",
                    ("open30", "open60"),
                )
            ]
            self.seal_forecast(before)
            with self.assertRaises(MODULE.ValidationError):
                MODULE.validate_forecast(before, root / "before.json", root)

            eligible = self.make_forecast(root, "domestic-at-1000")
            self.set_intraday_forecast_time(
                eligible,
                issued_at="2026-08-07T10:01:00+09:00",
                data_cutoff_at="2026-08-07T10:00:00+09:00",
                evaluation_bucket="morning_0931_1130",
            )
            eligible["hypothesisTrials"] = [
                self.make_flow_trial(
                    "domestic-flow-persistence",
                    "domestic-flow-persistence-v1",
                    ("open30", "open60"),
                )
            ]
            self.seal_forecast(eligible)
            validated = MODULE.validate_forecast(
                eligible, root / "eligible.json", root
            )
            self.assertEqual(
                validated["hypothesisTrialsParsed"][0]["predictorInputStatus"],
                "available",
            )

    def test_late_session_flow_trial_becomes_eligible_at_1400(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            before = self.make_forecast(root, "late-before-1400")
            self.set_intraday_forecast_time(
                before,
                issued_at="2026-08-07T13:59:00+09:00",
                data_cutoff_at="2026-08-07T13:59:00+09:00",
                evaluation_bucket="afternoon_1131_1500",
            )
            before["hypothesisTrials"] = [
                self.make_flow_trial(
                    "late-session-flow-acceleration",
                    "late-session-flow-acceleration-v1",
                    ("at1400",),
                )
            ]
            self.seal_forecast(before)
            with self.assertRaises(MODULE.ValidationError):
                MODULE.validate_forecast(before, root / "before.json", root)

            eligible = self.make_forecast(root, "late-at-1400")
            self.set_intraday_forecast_time(
                eligible,
                issued_at="2026-08-07T14:01:00+09:00",
                data_cutoff_at="2026-08-07T14:00:00+09:00",
                evaluation_bucket="afternoon_1131_1500",
            )
            eligible["hypothesisTrials"] = [
                self.make_flow_trial(
                    "late-session-flow-acceleration",
                    "late-session-flow-acceleration-v1",
                    ("at1400",),
                )
            ]
            self.seal_forecast(eligible)
            validated = MODULE.validate_forecast(
                eligible, root / "eligible.json", root
            )
            self.assertEqual(
                validated["hypothesisTrialsParsed"][0]["predictorInputStatus"],
                "available",
            )

    def test_twenty_complete_flow_sessions_auto_unblock_promotion(self):
        flow_features = MODULE.derive_flow_features(
            self.make_flow_trajectory()["anchors"]
        )
        predictor_inputs = self.make_predictor_inputs(("open30", "open60"))

        def make_summary_fixture(session_count: int):
            forecasts = {}
            outcomes = {}
            eligible_ids = set()
            for index in range(session_count):
                session_date = f"2026-07-{index + 1:02d}"
                forecast_id = f"flow-{session_date}"
                regime = "risk_on" if index < session_count // 2 else "risk_off"
                forecasts[forecast_id] = {
                    "forecastId": forecast_id,
                    "sessionDate": session_date,
                    "evaluationBucket": "morning_0931_1130",
                    "marketRegime": regime,
                    "dataCutoffAtParsed": MODULE.parse_iso(
                        f"{session_date}T10:00:00+09:00",
                        "fixture.dataCutoffAt",
                    ),
                    "hypothesisTrialsParsed": [
                        {
                            "hypothesisId": "domestic-flow-persistence",
                            "regime": regime,
                            "predictorVersion": "domestic-flow-persistence-v1",
                            "predictorInputStatus": "available",
                            "predictorInputsParsed": predictor_inputs,
                        }
                    ],
                }
                outcomes[forecast_id] = {
                    "hypothesisTestsParsed": [
                        {
                            "hypothesisId": "domestic-flow-persistence",
                            "regime": regime,
                            "baselineLiftBpsParsed": 12.0,
                            "inputEvidenceStatus": "verified",
                        }
                    ],
                    "flowFeaturesParsed": flow_features,
                }
                eligible_ids.add(forecast_id)
            return forecasts, outcomes, eligible_ids

        forecasts_19, outcomes_19, eligible_19 = make_summary_fixture(19)
        blocked = MODULE.summarize_hypotheses(
            [self.make_flow_hypothesis_definition(status="monitoring")],
            forecasts_19,
            outcomes_19,
            eligible_19,
        )[0]
        self.assertEqual(blocked["eligibleSessionCount"], 19)
        self.assertEqual(blocked["evaluableSessionCount"], 19)
        self.assertEqual(blocked["evidenceCoverageRate"], 1.0)
        self.assertFalse(blocked["promotionGateSatisfied"])
        self.assertTrue(blocked["promotionBlocked"])

        forecasts_20, outcomes_20, eligible_20 = make_summary_fixture(20)
        missing_forecast_id = sorted(eligible_20)[-1]
        outcomes_20[missing_forecast_id]["hypothesisTestsParsed"][0][
            "inputEvidenceStatus"
        ] = "missing_actual"
        incomplete = MODULE.summarize_hypotheses(
            [self.make_flow_hypothesis_definition(status="monitoring")],
            forecasts_20,
            outcomes_20,
            eligible_20,
        )[0]
        self.assertEqual(incomplete["eligibleSessionCount"], 20)
        self.assertEqual(incomplete["evaluableSessionCount"], 19)
        self.assertEqual(incomplete["evidenceCoverageRate"], 0.95)
        self.assertFalse(incomplete["promotionGateSatisfied"])
        self.assertTrue(incomplete["promotionBlocked"])

        outcomes_20[missing_forecast_id]["hypothesisTestsParsed"][0][
            "inputEvidenceStatus"
        ] = "verified"
        unblocked = MODULE.summarize_hypotheses(
            [self.make_flow_hypothesis_definition(status="active")],
            forecasts_20,
            outcomes_20,
            eligible_20,
        )[0]
        self.assertEqual(unblocked["eligibleSessionCount"], 20)
        self.assertEqual(unblocked["evaluableSessionCount"], 20)
        self.assertEqual(unblocked["evidenceCoverageRate"], 1.0)
        self.assertTrue(unblocked["promotionGateSatisfied"])
        self.assertFalse(unblocked["promotionBlocked"])
        self.assertEqual(unblocked["computedStatus"], "active")


if __name__ == "__main__":
    unittest.main()
