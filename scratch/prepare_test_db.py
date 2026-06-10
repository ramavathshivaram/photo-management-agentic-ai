import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Set one face to Priya
cursor.execute("UPDATE faces SET label = 'Priya' WHERE photo_id = 5")

# Rename photo 5 and set event to Wedding
cursor.execute("UPDATE photos SET original_filename = 'priya_wedding_01.jpg', event = 'Wedding', recognized_person = 'Priya' WHERE id = 5")

conn.commit()
conn.close()
print("Test database state prepared successfully!")
