# reset_db.py
from django.db import connection

def reset_db():
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM filesharing_collection;")
        cursor.execute("DELETE FROM crm_project;")
        cursor.execute("ALTER SEQUENCE crm_project_id_seq RESTART WITH 1;")
        cursor.execute("ALTER SEQUENCE filesharing_collection_id_seq RESTART WITH 1;")
        # Перевірка після очищення
        cursor.execute("SELECT * FROM crm_project;")
        print("crm_project:", cursor.fetchall())
        cursor.execute("SELECT * FROM filesharing_collection;")
        print("filesharing_collection:", cursor.fetchall())

# Використання в shell:
# >>> from reset_db import reset_db
# >>> reset_db()
# crm_project: []
# filesharing_collection: []