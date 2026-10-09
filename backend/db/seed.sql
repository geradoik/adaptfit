-- Exercise catalogue with deliberately coarse muscle groups (beginner-friendly, two-level menu).
-- Safe to re-run. evidence_rules is intentionally NOT seeded in week 1 (week 4 task).
INSERT OR IGNORE INTO exercises (name, muscle_group) VALUES
    ('Bench press',            'chest'),
    ('Push-up',                'chest'),
    ('Incline dumbbell press', 'chest'),
    ('Pull-up',                'back'),
    ('Barbell row',            'back'),
    ('Lat pulldown',           'back'),
    ('Squat',                  'legs'),
    ('Leg press',              'legs'),
    ('Lunge',                  'legs'),
    ('Deadlift',               'legs'),
    ('Romanian deadlift',      'legs'),
    ('Overhead press',         'shoulders'),
    ('Lateral raise',          'shoulders'),
    ('Face pull',              'shoulders'),
    ('Biceps curl',            'arms'),
    ('Triceps pushdown',       'arms'),
    ('Dips',                   'arms'),
    ('Plank',                  'core'),
    ('Crunch',                 'core'),
    ('Hanging leg raise',      'core');
