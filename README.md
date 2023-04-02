# MessNotFun
#### Description:
The purpose of the website allows users to manage personnel's finances in an organisation. Finances include deposits 
and work-related claims/expenditures. Previously, an actual organisation was relying on
Google Sheets for all calculations. This website hopes to minimise the time it takes to learn how to
key in the required data, minimise human errors and display data in a user-friendly manner.

#### Design:
##### DB Schema
<p>
CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT NOT NULL, hash TEXT NOT NULL);
</p>
<p>
CREATE TABLE personnel (personnel_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                name TEXT NOT NULL, deposit NUMERIC NOT NULL);
</p>
<p>
CREATE TABLE claim_type (claim_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                claim_name TEXT NOT NULL);
</p>
<p>
CREATE TABLE spending (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
              personnel_id INTEGER NOT NULL, claim_id INTEGER NOT NULL,
              amount NUMERIC NOT NULL, cost NUMERIC NOT NULL, datetime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY (claim_id) REFERENCES claim_type (claim_id)
              ON UPDATE CASCADE ON DELETE CASCADE,
              FOREIGN KEY (personnel_id) REFERENCES personnel (personnel_id)
              ON UPDATE CASCADE ON DELETE CASCADE);
</p>

##### Website Framework/Stack
<p>
The website was created with Flask, leveraged SQLite3 for DB and Python as the back-end.
A large part of the design was inspired from CS50's Finance PSet and utilized popular Bootstrap templates.
</p>

#### Future Improvements
<p>
Use other types of databases (postgresql/SQLAlchemy) to prevent dependence on CS50's library
Export to csv/pdf
Mobile-friendliness
</p>