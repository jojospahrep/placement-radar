"""Run with:  python -m unittest discover tests"""
import unittest
from datetime import date

from radar import classify, pipeline


class RoleType(unittest.TestCase):
    def test_types(self):
        cases = {
            "GE Aerospace Systems Engineering – 12 Month Placement": "placement",
            "Undergraduate Placement Year 2027 - AI Business Solutions": "placement",
            "Electrical and Electronic Engineering Co-Op": "placement",
            "Hardware Summer Intern 2027": "internship",
            "Aerodynamics Engineering Intern- Summer 2027": "internship",
            "Engineering Spring Week 2027": "insight",
            "Software Engineering Internship (Placement Year)": "placement",
        }
        for title, want in cases.items():
            self.assertEqual(classify.role_type(title), want, title)

    def test_not_student_roles(self):
        for t in ["Internal Audit Manager", "International Sales Lead", "Senior Mechanical Engineer",
                  "Engineering Apprentice", "PhD Intern, Robotics", "Placement Coordinator", "Werkstudent Embedded"]:
            self.assertIsNone(classify.role_type(t), t)

    def test_ambiguous_title_uses_description(self):
        self.assertEqual(classify.role_type("Engineering Intern", "A 12-month industrial placement from September 2027"), "placement")
        self.assertEqual(classify.role_type("Engineering Intern", "Join us for 10 weeks this summer"), "internship")


class Location(unittest.TestCase):
    def test_uk(self):
        for loc in ["Bristol, UK", "GBR - Farnborough, UK", "United Kingdom - Marlow", "Cambridge, England", "Belfast"]:
            self.assertTrue(classify.is_uk(loc), loc)

    def test_not_uk(self):
        for loc in ["Cambridge, MA", "London, Ontario", "Lake Macquarie, New South Wales", "Munich, Germany", "Austin, TX, United States"]:
            self.assertFalse(classify.is_uk(loc), loc)

    def test_country_field_wins(self):
        self.assertTrue(classify.is_uk("Remote", "GB"))
        self.assertFalse(classify.is_uk("London", "CA"))


class Deadlines(unittest.TestCase):
    today = date(2026, 10, 22)

    def test_formats(self):
        cases = {
            "Closing Date: 1st of November 2026": "2026-11-01",
            "Please submit your application by Friday 6 November 2026.": "2026-11-06",
            "Applications close on 22/10/2026": "2026-10-22",
            "Application deadline: January 15, 2027": "2027-01-15",
        }
        for text, want in cases.items():
            self.assertEqual(classify.find_deadline(text, self.today), want, text)

    def test_ignores_implausible(self):
        self.assertIsNone(classify.find_deadline("Founded in 1990, closing date 1 Jan 2019", self.today))
        self.assertIsNone(classify.find_deadline("We review applications on a rolling basis.", self.today))

    def test_cycle(self):
        self.assertEqual(classify.find_cycle("Industrial placement 2027-28"), "2027/28")
        self.assertEqual(classify.find_cycle("Summer 2027 internship"), "2027")


class Disciplines(unittest.TestCase):
    def test_title_tags(self):
        self.assertIn("Aerospace", classify.disciplines("Aerodynamics Engineering Intern"))
        self.assertIn("Electrical & Electronic", classify.disciplines("Firmware Summer Intern"))

    def test_non_engineering_dropped(self):
        self.assertFalse(classify.is_engineering("Finance and Accounting Intern", ["Software & Data"]))
        self.assertFalse(classify.is_engineering("People Intern - Year in Industry", ["Energy & Nuclear"]))
        self.assertTrue(classify.is_engineering("Sales Engineer Intern", []))


def raw(title, url, location="Bristol, UK", source="greenhouse"):
    return dict(company="Acme", sector="X", source=source, title=title, location=location, country="",
                url=url, description="", posted="", deadline=None)


class Lifecycle(unittest.TestCase):
    def setUp(self):
        self.store = {"jobs": {}, "sources": {}}
        pipeline.CHANGES = pipeline.ROOT / "data" / "_test_changes.jsonl"

    def tearDown(self):
        pipeline.CHANGES.unlink(missing_ok=True)

    def run_once(self, raws, ok=True):
        health = {"greenhouse:acme": {"ok": ok}}
        return pipeline.merge(self.store, {"greenhouse:acme": raws if ok else []}, health, date(2026, 10, 22))

    def test_new_then_closed_after_two_misses(self):
        r = raw("Mechanical Engineering Intern Summer 2027", "https://x/1")
        self.assertEqual(self.run_once([r])["new"], 1)
        self.assertEqual(self.run_once([])["closed"], 0)  # first miss tolerated
        self.assertEqual(self.run_once([])["closed"], 1)

    def test_failed_source_never_closes(self):
        self.run_once([raw("Mechanical Engineering Intern Summer 2027", "https://x/1")])
        for _ in range(3):
            self.assertEqual(self.run_once([], ok=False)["closed"], 0)

    def test_duplicates_collapse(self):
        s = self.run_once([raw("Hardware Summer Intern 2027", "https://x/1", "Bristol, UK"),
                           raw("Hardware Summer Intern 2027", "https://x/2", "Cambridge, UK")])
        self.assertEqual(s["open"], 1)
        primary = next(j for j in self.store["jobs"].values() if not j.get("duplicate_of"))
        self.assertEqual(primary["also_at"], ["Cambridge, UK"])

    def test_non_uk_rejected_and_cached(self):
        self.run_once([raw("Hardware Summer Intern 2027", "https://x/9", "Austin, TX", source="workday")])
        self.assertEqual(self.store["jobs"], {})
        self.assertIn("https://x/9", self.store["rejects"])


if __name__ == "__main__":
    unittest.main()
