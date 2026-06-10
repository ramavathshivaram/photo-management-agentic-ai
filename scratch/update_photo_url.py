import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()
cursor.execute("UPDATE photos SET secure_url = 'https://res.cloudinary.com/demo/image/upload/sample.jpg' WHERE id = 1")
conn.commit()
conn.close()
print("Successfully updated photo ID 1 secure_url to public Cloudinary URL.")
