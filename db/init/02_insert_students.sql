INSERT INTO students (student_id, name, group_name, email)
VALUES
    ('S001', 'Artem Morozov', 'CS-21', 'artem@example.com'),
    ('S002', 'Ivan Petrov', 'CS-22', 'ivan@example.com')
ON CONFLICT (student_id) DO NOTHING;
