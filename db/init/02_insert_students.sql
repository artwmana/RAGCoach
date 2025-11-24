INSERT INTO students (student_id, name, group_name)
VALUES
    ('55', 'Artem', '578105')
ON CONFLICT (student_id) DO NOTHING;
