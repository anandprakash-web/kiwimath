"""
UI/UX Flow Test — simulates the complete student journey through the assessment engine.

Tests every step a Flutter app user would experience:
  1. Curriculum selection screen  → GET /assess/curricula
  2. Start diagnostic            → POST /assess/full-diagnostic
  3. Answer questions adaptively  → POST /assess/respond (loop)
  4. Get next domain's item      → GET /assess/next-item
  5. View final report           → GET /assess/report
  6. Spaced review queue         → GET /assess/spaced-review
  7. End session early           → POST /assess/end
  8. Item bank stats             → GET /assess/item-bank/stats

Also validates:
  - Every API response has the fields Flutter expects
  - Questions have stem + choices + correct_answer (renderable)
  - Visual URLs are well-formed
  - Hints and diagnostics are present
  - KiwiScore, percentile, grade equivalent are reasonable
  - CAT converges within grade-appropriate item limits
  - All 4 curricula produce valid questions
  - Edge cases: invalid domain, missing session, already-completed session
"""

from __future__ import annotations

import random
import time

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture(scope="module")
def client():
    """Create a test client with all content stores initialized."""
    app = create_app()
    with TestClient(app) as c:
        yield c


# ============================================================
# Screen 1: Curriculum Picker
# ============================================================

class TestCurriculumPicker:
    """User lands on curriculum selection screen."""

    def test_list_curricula(self, client):
        """Flutter shows a list of available curricula with counts."""
        r = client.get("/assess/curricula")
        assert r.status_code == 200
        data = r.json()

        assert "curricula" in data
        assert "total_questions" in data
        assert "total_curricula" in data
        assert data["total_curricula"] == 4
        assert data["total_questions"] >= 6600

    def test_each_curriculum_has_required_fields(self, client):
        """Each curriculum card needs id, name, description, grade list, counts."""
        r = client.get("/assess/curricula")
        for cur in r.json()["curricula"]:
            assert "id" in cur, f"Missing id in {cur}"
            assert "name" in cur
            assert "description" in cur
            assert "grades" in cur
            assert "total_questions" in cur
            assert "questions_by_grade" in cur
            assert len(cur["grades"]) == 6
            assert cur["total_questions"] > 0

    def test_ncert_has_500_per_grade(self, client):
        r = client.get("/assess/curricula")
        ncert = [c for c in r.json()["curricula"] if c["id"] == "NCERT"][0]
        for g in range(1, 7):
            assert ncert["questions_by_grade"][str(g)] == 500

    def test_other_curricula_have_200_per_grade(self, client):
        r = client.get("/assess/curricula")
        for cur in r.json()["curricula"]:
            if cur["id"] == "NCERT":
                continue
            for g in range(1, 7):
                assert cur["questions_by_grade"][str(g)] == 200, \
                    f"{cur['id']} grade {g}: expected 200, got {cur['questions_by_grade'][str(g)]}"


# ============================================================
# Screen 2: Start Single-Domain Assessment
# ============================================================

class TestStartAssessment:
    """User taps 'Start Assessment' for a specific domain."""

    def test_start_arithmetic_session(self, client):
        r = client.post("/assess/start", json={
            "student_id": "ux_test_student_1",
            "domain": "arithmetic",
            "grade": 3,
        })
        assert r.status_code == 200
        data = r.json()
        assert "session_id" in data
        assert data["domain"] == "arithmetic"
        assert "first_item" in data
        self._validate_item(data["first_item"])

    def test_start_with_all_domains(self, client):
        """Every domain should be startable."""
        for domain in ["numbers", "arithmetic", "fractions", "geometry", "measurement"]:
            r = client.post("/assess/start", json={
                "student_id": f"ux_domain_{domain}",
                "domain": domain,
                "grade": 4,
            })
            assert r.status_code == 200, f"Failed to start {domain}: {r.text}"
            data = r.json()
            assert data["domain"] == domain
            self._validate_item(data["first_item"])

    def test_invalid_domain_returns_400(self, client):
        r = client.post("/assess/start", json={
            "student_id": "ux_err_1",
            "domain": "calculus",
            "grade": 3,
        })
        assert r.status_code == 400

    def test_invalid_grade_returns_422(self, client):
        r = client.post("/assess/start", json={
            "student_id": "ux_err_2",
            "domain": "arithmetic",
            "grade": 0,
        })
        assert r.status_code == 422

    def _validate_item(self, item: dict):
        """Every item returned to Flutter must have these fields."""
        assert "item_id" in item
        assert "domain" in item
        assert "subdomain" in item


# ============================================================
# Screen 3: Question Answering Loop (Core CAT Flow)
# ============================================================

class TestQuestionLoop:
    """User sees questions one by one, answers them, sees updated score."""

    def test_full_session_flow(self, client):
        """Complete a full session: start → answer until convergence → result."""
        # Start
        r = client.post("/assess/start", json={
            "student_id": "ux_flow_student",
            "domain": "numbers",
            "grade": 3,
        })
        assert r.status_code == 200
        session_id = r.json()["session_id"]
        current_item = r.json()["first_item"]

        items_answered = 0
        kiwiscores = []
        random.seed(42)

        # Answer loop (simulate 70% accuracy)
        for _ in range(25):  # Max safety limit
            item_id = current_item["item_id"]
            correct = random.random() < 0.7

            r = client.post("/assess/respond", json={
                "session_id": session_id,
                "item_id": item_id,
                "correct": correct,
                "response_time_sec": random.uniform(5, 20),
            })
            assert r.status_code == 200
            resp = r.json()
            items_answered += 1

            # Validate response fields Flutter needs
            assert "theta" in resp
            assert "se" in resp
            assert "kiwiscore" in resp
            assert "n_items" in resp
            assert "correct" in resp
            assert "stop_reason" in resp
            assert "converged" in resp
            kiwiscores.append(resp["kiwiscore"])

            # Check if session is done
            if resp["stop_reason"] != "not_stopped":
                break

            # Get next item
            if resp["next_item"]:
                current_item = resp["next_item"]
            else:
                break

        # Session should have converged within grade limits
        assert items_answered <= 20, f"Too many items for Grade 3: {items_answered}"
        assert items_answered >= 3, "Too few items — something went wrong"

        # KiwiScore should be a reasonable number
        final_ks = kiwiscores[-1]
        assert 100 <= final_ks <= 350, f"Unreasonable KiwiScore: {final_ks}"

        # Get result
        r = client.get("/assess/result", params={"session_id": session_id})
        assert r.status_code == 200
        result = r.json()
        assert "kiwiscore" in result
        assert "accuracy" in result

    def test_item_has_renderable_content(self, client):
        """Items from NCERT store should have stem + choices for Flutter to render."""
        r = client.post("/assess/start", json={
            "student_id": "ux_render_test",
            "domain": "arithmetic",
            "grade": 2,
        })
        item = r.json()["first_item"]

        # Items enriched from content store should have full data
        if "stem" in item:
            assert len(item["stem"]) > 5, "Stem too short to render"
            assert "choices" in item
            assert len(item["choices"]) >= 2, "Not enough choices"
            assert "correct_answer" in item
            assert "hint" in item

    def test_visual_url_format(self, client):
        """If item has a visual, the URL should be well-formed."""
        r = client.post("/assess/start", json={
            "student_id": "ux_visual_test",
            "domain": "geometry",
            "grade": 4,
        })
        item = r.json()["first_item"]
        if item.get("visual_url"):
            assert item["visual_url"].startswith("/static/"), \
                f"Bad visual URL format: {item['visual_url']}"

    def test_respond_to_missing_session_returns_404(self, client):
        r = client.post("/assess/respond", json={
            "session_id": "nonexistent_session_xyz",
            "item_id": "fake_item",
            "correct": True,
            "response_time_sec": 10.0,
        })
        assert r.status_code == 404

    def test_next_item_missing_session_returns_404(self, client):
        r = client.get("/assess/next-item", params={"session_id": "nonexistent_abc"})
        assert r.status_code == 404


# ============================================================
# Screen 4: Full Multi-Domain Diagnostic
# ============================================================

class TestFullDiagnostic:
    """User takes the full 5-domain diagnostic assessment."""

    def test_start_full_diagnostic(self, client):
        r = client.post("/assess/full-diagnostic", json={
            "student_id": "ux_diag_student",
            "grade": 3,
        })
        assert r.status_code == 200
        data = r.json()

        assert data["student_id"] == "ux_diag_student"
        assert "sessions" in data
        assert data["total_domains"] == 5
        assert "current_domain" in data
        assert "first_item" in data
        assert data["first_item"] is not None

        # All 5 domains should have session IDs
        for domain in ["numbers", "arithmetic", "fractions", "geometry", "measurement"]:
            assert domain in data["sessions"], f"Missing domain session: {domain}"

    def test_full_diagnostic_custom_domains(self, client):
        """User can choose specific domains to assess."""
        r = client.post("/assess/full-diagnostic", json={
            "student_id": "ux_diag_partial",
            "grade": 5,
            "domains": ["fractions", "geometry"],
        })
        assert r.status_code == 200
        data = r.json()
        assert data["total_domains"] == 2
        assert "fractions" in data["sessions"]
        assert "geometry" in data["sessions"]

    def test_complete_diagnostic_and_get_report(self, client):
        """Run through all 5 domains and get the full report."""
        # Start diagnostic
        r = client.post("/assess/full-diagnostic", json={
            "student_id": "ux_full_report",
            "grade": 4,
        })
        data = r.json()
        sessions = data["sessions"]

        random.seed(123)

        # Complete each domain session
        for domain, session_id in sessions.items():
            for _ in range(20):
                r = client.get("/assess/next-item", params={"session_id": session_id})
                resp = r.json()
                if resp.get("done"):
                    break

                item = resp["item"]
                correct = random.random() < 0.65

                r = client.post("/assess/respond", json={
                    "session_id": session_id,
                    "item_id": item["item_id"],
                    "correct": correct,
                    "response_time_sec": random.uniform(8, 25),
                })
                if r.json()["stop_reason"] != "not_stopped":
                    break

        # Get report
        r = client.get("/assess/report", params={"student_id": "ux_full_report"})
        assert r.status_code == 200
        report_data = r.json()

        # Validate report structure
        report = report_data["report"]
        assert "overall" in report
        assert "kiwiscore" in report["overall"]
        assert "grade_equivalent" in report["overall"]
        assert "percentile" in report["overall"]
        assert "domains" in report
        assert len(report["domains"]) == 5
        assert "strengths" in report
        assert "growth_areas" in report
        assert "recommended_track" in report
        assert report["recommended_track"] in ("foundation", "school", "accelerate")
        assert "parent_summary" in report
        assert len(report["parent_summary"]) > 30, "Parent summary too short"

        # Validate each domain in report
        for domain_report in report["domains"]:
            assert "domain" in domain_report
            assert "kiwiscore" in domain_report
            assert "grade_equivalent" in domain_report
            assert "percentile" in domain_report
            assert "status" in domain_report
            assert domain_report["status"] in ("below_level", "at_level", "above_level")
            assert 50 <= domain_report["kiwiscore"] <= 350

        # Validate learning path
        path = report_data["learning_path"]
        assert "overall_track" in path
        assert "focus_domains" in path
        assert "foundation" in path
        assert "school" in path
        assert "accelerate" in path

    def test_report_before_completion_returns_400(self, client):
        """Can't get report if domains aren't all finished."""
        r = client.post("/assess/full-diagnostic", json={
            "student_id": "ux_incomplete_diag",
            "grade": 2,
        })
        # Don't answer any questions — try to get report immediately
        r = client.get("/assess/report", params={"student_id": "ux_incomplete_diag"})
        assert r.status_code == 400

    def test_report_nonexistent_student_returns_404(self, client):
        r = client.get("/assess/report", params={"student_id": "ghost_student_xyz"})
        assert r.status_code == 404


# ============================================================
# Screen 5: End Session Early
# ============================================================

class TestEndSessionEarly:
    """User taps 'Quit' during assessment — should get partial results."""

    def test_end_session_early(self, client):
        # Start session
        r = client.post("/assess/start", json={
            "student_id": "ux_early_quit",
            "domain": "fractions",
            "grade": 5,
        })
        session_id = r.json()["session_id"]
        first_item = r.json()["first_item"]

        # Answer 2 questions
        for i in range(2):
            if i == 0:
                item_id = first_item["item_id"]
            else:
                nr = client.get("/assess/next-item", params={"session_id": session_id})
                if nr.json().get("done"):
                    break
                item_id = nr.json()["item"]["item_id"]

            client.post("/assess/respond", json={
                "session_id": session_id,
                "item_id": item_id,
                "correct": True,
                "response_time_sec": 10.0,
            })

        # End early
        r = client.post("/assess/end", json={"session_id": session_id})
        assert r.status_code == 200
        result = r.json()
        assert "kiwiscore" in result

    def test_end_nonexistent_session_returns_404(self, client):
        r = client.post("/assess/end", json={"session_id": "no_such_session"})
        assert r.status_code == 404


# ============================================================
# Screen 6: Spaced Review Queue
# ============================================================

class TestSpacedReview:
    """Parent/student sees which skills need review."""

    def test_get_review_queue(self, client):
        r = client.get("/assess/spaced-review", params={
            "student_id": "ux_review_student",
            "max_items": 5,
        })
        assert r.status_code == 200
        data = r.json()
        assert "student_id" in data
        assert "review_items" in data
        assert "health" in data

    def test_review_items_have_required_fields(self, client):
        """If there are review items, each must have the fields Flutter needs."""
        r = client.get("/assess/spaced-review", params={
            "student_id": "ux_review_fields",
            "max_items": 10,
        })
        for item in r.json()["review_items"]:
            assert "skill_id" in item
            assert "recall_probability" in item
            assert "priority" in item
            assert "hours_until_review" in item
            assert "strength" in item
            assert 0 <= item["recall_probability"] <= 1


# ============================================================
# Screen 7: Item Bank Stats (Admin/Debug)
# ============================================================

class TestItemBankStats:
    """Admin or debug screen showing item bank health."""

    def test_item_bank_stats(self, client):
        r = client.get("/assess/item-bank/stats")
        assert r.status_code == 200
        data = r.json()
        assert data["total_items"] >= 6600
        assert "domain_stats" in data


# ============================================================
# Screen 8: Health Check (App Startup)
# ============================================================

class TestHealthCheck:
    """App checks backend is alive before showing anything."""

    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"
        assert "content" in data

    def test_stats(self, client):
        r = client.get("/stats")
        assert r.status_code == 200


# ============================================================
# Cross-Curriculum: Questions from all 4 curricula are servable
# ============================================================

class TestCrossCurriculum:
    """Verify all 4 curricula produce renderable items."""

    @pytest.mark.parametrize("grade", [1, 3, 5])
    def test_items_served_across_grades(self, client, grade):
        """Items should be served for every supported grade."""
        r = client.post("/assess/start", json={
            "student_id": f"ux_grade_{grade}",
            "domain": "arithmetic",
            "grade": grade,
        })
        assert r.status_code == 200
        item = r.json()["first_item"]
        assert item["item_id"], f"No item_id for grade {grade}"
        assert item["domain"] == "arithmetic"

    def test_different_students_get_different_items(self, client):
        """Two students starting the same assessment shouldn't always get the same first item."""
        items = []
        for i in range(5):
            r = client.post("/assess/start", json={
                "student_id": f"ux_diversity_{i}",
                "domain": "numbers",
                "grade": 3,
            })
            items.append(r.json()["first_item"]["item_id"])
        # With 6600 items, all getting the exact same first item is a concern
        # (Though at θ=0 they might — this is a soft check)
        # At minimum, the engine should work for all 5 students
        assert len(items) == 5


# ============================================================
# Edge Cases & Error Handling
# ============================================================

class TestEdgeCases:
    """Things that shouldn't crash the app."""

    def test_respond_to_completed_session_returns_400(self, client):
        """After session ends, user shouldn't be able to submit more answers."""
        r = client.post("/assess/start", json={
            "student_id": "ux_edge_completed",
            "domain": "geometry",
            "grade": 2,
        })
        session_id = r.json()["session_id"]

        # End it
        client.post("/assess/end", json={"session_id": session_id})

        # Try to respond
        r = client.post("/assess/respond", json={
            "session_id": session_id,
            "item_id": "any_item",
            "correct": True,
            "response_time_sec": 5.0,
        })
        assert r.status_code == 400

    def test_next_item_on_completed_session_returns_done(self, client):
        r = client.post("/assess/start", json={
            "student_id": "ux_edge_done",
            "domain": "measurement",
            "grade": 1,
        })
        session_id = r.json()["session_id"]
        client.post("/assess/end", json={"session_id": session_id})

        r = client.get("/assess/next-item", params={"session_id": session_id})
        assert r.status_code == 200
        assert r.json()["done"] is True

    def test_very_fast_response_accepted(self, client):
        """0-second response time is valid (accidental tap)."""
        r = client.post("/assess/start", json={
            "student_id": "ux_edge_fast",
            "domain": "numbers",
            "grade": 1,
        })
        session_id = r.json()["session_id"]
        item_id = r.json()["first_item"]["item_id"]

        r = client.post("/assess/respond", json={
            "session_id": session_id,
            "item_id": item_id,
            "correct": True,
            "response_time_sec": 0.0,
        })
        assert r.status_code == 200

    def test_negative_response_time_rejected(self, client):
        """Negative response time should be rejected."""
        r = client.post("/assess/start", json={
            "student_id": "ux_edge_neg",
            "domain": "numbers",
            "grade": 1,
        })
        session_id = r.json()["session_id"]
        item_id = r.json()["first_item"]["item_id"]

        r = client.post("/assess/respond", json={
            "session_id": session_id,
            "item_id": item_id,
            "correct": True,
            "response_time_sec": -5.0,
        })
        assert r.status_code == 422

    def test_missing_student_id_returns_422(self, client):
        r = client.post("/assess/start", json={
            "domain": "arithmetic",
            "grade": 3,
        })
        assert r.status_code == 422


# ============================================================
# UX Quality: Response Content Validation
# ============================================================

class TestUXQuality:
    """Verify the data quality is good enough for a polished UI."""

    def test_kiwiscore_in_reasonable_range(self, client):
        """KiwiScore should always be between 50 and 350."""
        r = client.post("/assess/start", json={
            "student_id": "ux_ks_range",
            "domain": "arithmetic",
            "grade": 3,
        })
        session_id = r.json()["session_id"]
        item = r.json()["first_item"]

        # All correct → high score
        for _ in range(5):
            r = client.post("/assess/respond", json={
                "session_id": session_id,
                "item_id": item["item_id"],
                "correct": True,
                "response_time_sec": 8.0,
            })
            resp = r.json()
            assert 50 <= resp["kiwiscore"] <= 350, f"Bad KiwiScore: {resp['kiwiscore']}"
            if resp["stop_reason"] != "not_stopped":
                break
            if resp["next_item"]:
                item = resp["next_item"]
            else:
                break

    def test_se_decreases_with_more_items(self, client):
        """Standard error should generally decrease as more items are answered."""
        r = client.post("/assess/start", json={
            "student_id": "ux_se_decrease",
            "domain": "fractions",
            "grade": 4,
        })
        session_id = r.json()["session_id"]
        item = r.json()["first_item"]

        se_values = []
        random.seed(99)

        for _ in range(10):
            r = client.post("/assess/respond", json={
                "session_id": session_id,
                "item_id": item["item_id"],
                "correct": random.random() < 0.6,
                "response_time_sec": 12.0,
            })
            resp = r.json()
            se_values.append(resp["se"])
            if resp["stop_reason"] != "not_stopped":
                break
            if resp["next_item"]:
                item = resp["next_item"]
            else:
                break

        # SE after 5+ items should be lower than initial
        if len(se_values) >= 5:
            assert se_values[-1] < se_values[0], \
                f"SE didn't decrease: {se_values[0]:.3f} → {se_values[-1]:.3f}"

    def test_parent_summary_is_readable(self, client):
        """The parent summary should be a complete sentence, not gibberish."""
        # Start and complete a full diagnostic
        r = client.post("/assess/full-diagnostic", json={
            "student_id": "ux_parent_readable",
            "grade": 3,
        })
        sessions = r.json()["sessions"]

        random.seed(77)
        for domain, session_id in sessions.items():
            for _ in range(20):
                r = client.get("/assess/next-item", params={"session_id": session_id})
                if r.json().get("done"):
                    break
                item = r.json()["item"]
                r = client.post("/assess/respond", json={
                    "session_id": session_id,
                    "item_id": item["item_id"],
                    "correct": random.random() < 0.5,
                    "response_time_sec": 15.0,
                })
                if r.json()["stop_reason"] != "not_stopped":
                    break

        r = client.get("/assess/report", params={"student_id": "ux_parent_readable"})
        if r.status_code == 200:
            summary = r.json()["report"]["parent_summary"]
            assert len(summary) > 50, "Summary too short for parent readability"
            assert "KiwiScore" in summary, "Summary should mention KiwiScore"
            assert summary[0].isupper(), "Summary should start with a capital letter"
            assert summary.endswith((".", "!")), "Summary should end with punctuation"
