import psycopg2

HOST = "localhost"
PORT = 5432
USER = "admin"
PASSWORD = "secret" # not secret at all
DATABASE = "exam_bot"

conn = psycopg2.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
        dbname=DATABASE
    )

def adding(student_id, name, group_name) -> None:
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(f"""INSERT INTO students (student_id, name, group_name)
            VALUES
            ('{student_id}', '{name}', '{group_name}')
            ON CONFLICT (student_id) DO NOTHING;""")
    cur.close()
    conn.close()
    
def main() -> None:
    adding('test_id', 'Ivan Ivanov', 'test_group')

if __name__ == 'main':
    main()