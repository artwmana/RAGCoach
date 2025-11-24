INSERT INTO students (student_id, name, group_name)
VALUES
    ('S001', 'Artem Morozov', '51'),
    ('S002', 'Ivan', '52')
ON CONFLICT (student_id) DO NOTHING;
