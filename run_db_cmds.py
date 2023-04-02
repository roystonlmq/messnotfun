from cs50 import SQL

db = SQL("sqlite:///mess.db")

# Create personnel table
db.execute('''CREATE TABLE personnel (personnel_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                name TEXT NOT NULL, deposit NUMERIC NOT NULL)
            ''')

# # Create claim_type table
db.execute('''CREATE TABLE claim_type (claim_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                claim_name TEXT NOT NULL)''')


# Create spending table
db.execute('''CREATE TABLE spending (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
              personnel_id INTEGER NOT NULL, claim_id INTEGER NOT NULL,
              amount NUMERIC NOT NULL, cost NUMERIC NOT NULL,
              FOREIGN KEY (claim_id) REFERENCES claim_type (claim_id)
              ON UPDATE CASCADE ON DELETE CASCADE,
              FOREIGN KEY (personnel_id) REFERENCES personnel (personnel_id)
              ON UPDATE CASCADE ON DELETE CASCADE)
           ''')