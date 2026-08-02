import database

def seed():
    database.init_db()
    # Seeding disabled for fresh production use
    pass

if __name__ == "__main__":
    seed()
