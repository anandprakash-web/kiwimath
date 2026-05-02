"""Tests for the Assessment Engine — IRT, CAT, Path, Spaced Rep."""

import math
import time

from app.assessment.irt_model import (
    AbilityEstimate,
    ItemParameters,
    estimate_ability_eap,
    compute_standard_error,
)
from app.assessment.item_bank import ItemBank
from app.assessment.cat_engine import CATEngine, Domain, StopReason
from app.assessment.path_engine import PathEngine, Track
from app.assessment.scoring import (
    theta_to_kiwiscore,
    kiwiscore_to_percentile,
    FullAssessmentReport,
)
from app.assessment.spaced_rep import SpacedRepEngine
from app.assessment.calibration import ItemCalibrator, ResponseRecord


# ============================================================
# IRT Model Tests
# ============================================================

class TestIRTModel:
    def test_probability_at_difficulty(self):
        """P(correct) should be ~0.5+c/2 when θ=b."""
        item = ItemParameters("test1", a=1.0, b=0.0, c=0.25)
        p = item.probability(0.0)
        # At θ=b: P = c + (1-c)/2 = 0.25 + 0.375 = 0.625
        assert abs(p - 0.625) < 0.01

    def test_probability_high_ability(self):
        """High ability should give P close to 1."""
        item = ItemParameters("test2", a=1.5, b=0.0, c=0.2)
        p = item.probability(3.0)
        assert p > 0.95

    def test_probability_low_ability(self):
        """Low ability should give P close to guessing (c)."""
        item = ItemParameters("test3", a=1.5, b=0.0, c=0.25)
        p = item.probability(-3.0)
        assert abs(p - 0.25) < 0.05

    def test_information_peaks_near_difficulty(self):
        """Information should be highest near θ=b."""
        item = ItemParameters("test4", a=1.5, b=1.0, c=0.2)
        info_at_b = item.information(1.0)
        info_far = item.information(-2.0)
        assert info_at_b > info_far

    def test_discrimination_affects_information(self):
        """Higher discrimination = higher information."""
        item_low = ItemParameters("low_a", a=0.5, b=0.0, c=0.2)
        item_high = ItemParameters("high_a", a=2.0, b=0.0, c=0.2)
        assert item_high.information(0.0) > item_low.information(0.0)

    def test_eap_estimation_correct_responses(self):
        """Consistently correct responses should push θ up."""
        items = [ItemParameters(f"i{i}", a=1.0, b=0.0, c=0.2) for i in range(10)]
        responses = [True] * 10
        theta, se = estimate_ability_eap(items, responses)
        assert theta > 1.0
        assert se < 1.0

    def test_eap_estimation_incorrect_responses(self):
        """Consistently incorrect responses should push θ down."""
        items = [ItemParameters(f"i{i}", a=1.0, b=0.0, c=0.2) for i in range(10)]
        responses = [False] * 10
        theta, se = estimate_ability_eap(items, responses)
        assert theta < -1.0

    def test_eap_mixed_responses(self):
        """Mixed responses should give θ near item difficulty."""
        items = [ItemParameters(f"i{i}", a=1.0, b=0.5, c=0.2) for i in range(20)]
        responses = [True, False] * 10  # 50% correct
        theta, se = estimate_ability_eap(items, responses)
        assert -1.0 < theta < 1.0

    def test_kiwiscore_conversion(self):
        """θ=0 → KiwiScore 200, θ=1 → 230."""
        est = AbilityEstimate(theta=0.0)
        assert est.kiwiscore == 200
        est2 = AbilityEstimate(theta=1.0)
        assert est2.kiwiscore == 230


# ============================================================
# Item Bank Tests
# ============================================================

class TestItemBank:
    def _make_bank(self) -> ItemBank:
        bank = ItemBank()
        for i in range(50):
            bank.add_item(ItemParameters(
                item_id=f"item_{i}",
                a=1.0, b=-2.0 + i * 0.1, c=0.25,
                domain="arithmetic" if i < 25 else "geometry",
                subdomain=f"sub_{i % 5}",
                grade_range=(1, 6),
                state="active",
            ))
        return bank

    def test_filter_by_domain(self):
        bank = self._make_bank()
        arith = bank.get_eligible_items(domain="arithmetic")
        assert len(arith) == 25
        assert all(item.domain == "arithmetic" for item in arith)

    def test_exclude_seen(self):
        bank = self._make_bank()
        bank.record_exposure("item_0", "student_1")
        bank.record_exposure("item_1", "student_1")
        eligible = bank.get_eligible_items(student_id="student_1")
        ids = {item.item_id for item in eligible}
        assert "item_0" not in ids
        assert "item_1" not in ids

    def test_record_response_updates_health(self):
        bank = self._make_bank()
        bank.record_response("item_0", True, 12.5)
        bank.record_response("item_0", False, 8.0)
        health = bank.get_health("item_0")
        assert health.total_responses == 2
        assert health.correct_count == 1


# ============================================================
# CAT Engine Tests
# ============================================================

class TestCATEngine:
    def _make_engine(self) -> CATEngine:
        bank = ItemBank()
        for i in range(100):
            bank.add_item(ItemParameters(
                item_id=f"cat_item_{i}",
                a=1.0 + (i % 5) * 0.2,
                b=-3.0 + i * 0.06,
                c=0.25,
                domain="arithmetic",
                subdomain=f"sub_{i % 4}",
                grade_range=(1, 6),
                state="active",
            ))
        return CATEngine(bank)

    def test_start_session(self):
        engine = self._make_engine()
        session = engine.start_session("student_1", Domain.ARITHMETIC, grade=3)
        assert session.is_active
        assert session.ability.theta == 0.0

    def test_select_item(self):
        engine = self._make_engine()
        session = engine.start_session("student_1", Domain.ARITHMETIC, grade=3)
        item = engine.select_next_item(session)
        assert item is not None
        assert item.domain == "arithmetic"

    def test_record_correct_increases_theta(self):
        engine = self._make_engine()
        session = engine.start_session("student_1", Domain.ARITHMETIC, grade=3)
        item = engine.select_next_item(session)
        result = engine.record_response(session, item, correct=True, response_time_sec=15.0)
        # After 1 correct on medium item, θ should increase
        assert result["theta"] >= 0.0

    def test_session_converges(self):
        engine = self._make_engine()
        session = engine.start_session("student_1", Domain.ARITHMETIC, grade=3)

        # Simulate: always correct (high ability student)
        for _ in range(25):
            if not session.is_active:
                break
            item = engine.select_next_item(session)
            if not item:
                break
            engine.record_response(session, item, correct=True, response_time_sec=10.0)

        # Should have stopped (converged or max items)
        assert session.stop_reason != StopReason.NOT_STOPPED
        assert session.ability.theta > 0.5  # High ability (positive θ)

    def test_result_report(self):
        engine = self._make_engine()
        session = engine.start_session("student_1", Domain.ARITHMETIC, grade=3)
        item = engine.select_next_item(session)
        engine.record_response(session, item, correct=True, response_time_sec=10.0)
        session.stop_reason = StopReason.MAX_ITEMS
        result = engine.get_result(session)
        assert "kiwiscore" in result
        assert "accuracy" in result


# ============================================================
# Path Engine Tests
# ============================================================

class TestPathEngine:
    def test_foundation_track(self):
        """Student far below grade level → foundation track."""
        engine = PathEngine()
        path = engine.generate_path(
            student_id="s1",
            domain_scores={"numbers": -2.5, "arithmetic": -2.0, "fractions": -3.0,
                          "geometry": -2.0, "measurement": -2.5},
            grade=4,
        )
        assert path.overall_track == Track.FOUNDATION

    def test_accelerate_track(self):
        """Student above grade level → accelerate track."""
        engine = PathEngine()
        path = engine.generate_path(
            student_id="s2",
            domain_scores={"numbers": 2.0, "arithmetic": 1.5, "fractions": 1.0,
                          "geometry": 1.8, "measurement": 1.5},
            grade=3,
        )
        assert path.overall_track == Track.ACCELERATE

    def test_path_has_recommendations(self):
        """Path should produce actionable recommendations."""
        engine = PathEngine()
        path = engine.generate_path(
            student_id="s3",
            domain_scores={"numbers": -0.5, "arithmetic": -1.0, "fractions": -2.0,
                          "geometry": 0.0, "measurement": -0.5},
            grade=4,
        )
        assert len(path.recommendations) > 0
        assert "fractions" in path.focus_domains

    def test_path_to_dict(self):
        engine = PathEngine()
        path = engine.generate_path(
            student_id="s4",
            domain_scores={"numbers": 0.0, "arithmetic": -0.5, "fractions": -1.0,
                          "geometry": 0.5, "measurement": 0.0},
            grade=3,
        )
        d = path.to_dict()
        assert "foundation" in d
        assert "school" in d
        assert "accelerate" in d
        assert "total_sessions_estimated" in d


# ============================================================
# Spaced Repetition Tests
# ============================================================

class TestSpacedRep:
    def test_new_skill_needs_review(self):
        sr = SpacedRepEngine()
        mem = sr.get_memory("student_1", "addition")
        assert mem.needs_review()

    def test_correct_increases_strength(self):
        sr = SpacedRepEngine()
        mem = sr.record_practice("student_1", "addition", correct=True)
        assert mem.strength > 0
        assert mem.consecutive_correct == 1

    def test_incorrect_decreases_strength(self):
        sr = SpacedRepEngine()
        sr.record_practice("student_1", "addition", correct=True)
        sr.record_practice("student_1", "addition", correct=True)
        mem = sr.record_practice("student_1", "addition", correct=False)
        assert mem.consecutive_correct == 0

    def test_recall_decays_over_time(self):
        sr = SpacedRepEngine()
        now = time.time()
        sr.record_practice("student_1", "addition", correct=True, current_time=now)
        mem = sr.get_memory("student_1", "addition")

        # Immediately after: high recall
        p_now = mem.recall_probability(now)
        assert p_now > 0.95

        # 48 hours later: lower recall
        p_later = mem.recall_probability(now + 48 * 3600)
        assert p_later < p_now

    def test_session_mix(self):
        sr = SpacedRepEngine()
        now = time.time()
        # Practice some skills
        sr.record_practice("s1", "addition", True, now - 100000)
        sr.record_practice("s1", "subtraction", True, now - 200000)
        sr.record_practice("s1", "multiplication", True, now - 50000)

        mix = sr.build_session_mix("s1", new_skills=["fractions", "decimals"], total_items=10, current_time=now)
        assert "new" in mix
        assert "review" in mix
        assert "adaptive" in mix


# ============================================================
# Scoring Tests
# ============================================================

class TestScoring:
    def test_theta_to_kiwiscore(self):
        assert theta_to_kiwiscore(0.0) == 200
        assert theta_to_kiwiscore(1.0) == 230
        assert theta_to_kiwiscore(-1.0) == 170

    def test_percentile_at_grade_mean(self):
        """Score at grade mean should be ~50th percentile."""
        pct = kiwiscore_to_percentile(180, grade=3)  # Grade 3 mean
        assert 40 <= pct <= 60

    def test_full_report(self):
        report = FullAssessmentReport.from_domain_scores(
            student_id="test_student",
            grade=3,
            curriculum="NCERT",
            domain_results={
                "numbers": (0.5, 0.25),
                "arithmetic": (-0.3, 0.28),
                "fractions": (-1.5, 0.30),
                "geometry": (0.2, 0.27),
                "measurement": (-0.1, 0.26),
            },
        )
        assert report.overall_kiwiscore > 0
        assert len(report.domains) == 5
        assert report.recommended_track in ("foundation", "school", "accelerate")
        assert len(report.parent_summary) > 50


# ============================================================
# Calibration Tests
# ============================================================

class TestCalibration:
    def test_calibrate_with_sufficient_data(self):
        item = ItemParameters("cal_test", a=1.0, b=0.0, c=0.25)
        calibrator = ItemCalibrator()

        # Generate synthetic responses from students of varying ability
        responses = []
        for i in range(200):
            theta = -2.0 + i * 0.02  # θ from -2 to +2
            p = item.probability(theta)
            correct = (i % 3 != 0)  # ~67% correct rate
            responses.append(ResponseRecord(
                student_id=f"s_{i}",
                item_id="cal_test",
                correct=correct,
                response_time_sec=20.0,
                theta_at_response=theta,
            ))

        result = calibrator.calibrate_item(item, responses)
        assert result.n_responses == 200
        assert result.fit_statistic > 0

    def test_insufficient_data_returns_original(self):
        item = ItemParameters("cal_test2", a=1.5, b=0.5, c=0.2)
        calibrator = ItemCalibrator()
        responses = [
            ResponseRecord("s1", "cal_test2", True, 10.0, 0.0)
            for _ in range(10)
        ]
        result = calibrator.calibrate_item(item, responses)
        assert result.new_params == (item.a, item.b, item.c)
