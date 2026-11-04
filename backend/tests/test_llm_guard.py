import unittest
from datetime import  date 
from app import db, demo_seed, llm_context as lc, llm_guard as g, metrics_service
 
def make_context():
    conn = db.connect(":memory:")
    db.init_db(conn)
    uid = demo_seed.seed_demo(conn)
    as_of = date(2026, 10, 12)
    results = metrics_service.compute_all(conn, uid, as_of, store=False)
    return conn, uid, lc.build_context(conn, uid, as_of, results)
 
 
class GuardTests(unittest.TestCase):
    def setUp(self):
        self.conn, self.uid, self.ctx = make_context()
        self.addCleanup(self.conn.close)
 
    def check(self, reply):
        return g.check_reply(reply, self.ctx)
 
    def test_a_good_reply_passes(self):
        self.assertEqual(self.check("Try [[Incline dumbbell press]] twice a week [E3]. Eat 2200 kcal."), [])
 
    def test_empty_or_non_text_reply_fails(self):
        for bad in ("", "   ", None, 5):
            self.assertEqual(self.check(bad), ["Empty reply"])
 
    def test_unknown_citation_fails(self):
        self.assertEqual(self.check("Studies show it [E9]."), ["Unknown citation: [E9]"])
        self.assertEqual(self.check("See [E2] and [E6]."), [])
 
    def test_unknown_exercise_fails_and_known_one_is_case_insensitive(self):
        self.assertEqual(self.check("Do [[Burpees]]."), ["Unknown exercise: Burpees"])
        self.assertEqual(self.check("Do [[bench PRESS]]."), [])
 
    def test_low_calorie_figures_fail(self):
        self.assertTrue(self.check("Eat only 900 kcal a day."))
        self.assertTrue(self.check("Aim for 1,000 calories."))
        self.assertEqual(self.check("Aim for 1,800 calories."), [])
 
    def test_unsafe_words_fail(self):
        self.assertTrue(self.check("You could starve yourself for a week."))
 
    def test_too_long_fails(self):
        self.assertTrue(self.check("word " * 400))
 
    def test_cited_ids_in_order_without_repeats(self):
        self.assertEqual(g.cited_ids("[E3] then [E2] then [E3]"), ["E3", "E2"])
 
    def test_finish_reply_strips_brackets_and_adds_disclaimer(self):
        shown = g.finish_reply("Do [[Push-up]] daily. ")
        self.assertTrue(shown.startswith("Do Push-up daily."))
        self.assertNotIn("[[", shown)
        self.assertTrue(shown.endswith("General fitness guidance, not medical advice."))
 
 
if __name__ == "__main__":
    unittest.main()
