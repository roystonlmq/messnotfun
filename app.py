import os

from cs50 import SQL
from datetime import datetime
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, sgd

# Configure application
app = Flask(__name__)

# # Custom filter
app.jinja_env.filters["sgd"] = sgd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///mess.db")

USER_CONFIG = {'add_user': 'Add User', 'remove-personnel': 'Remove User'}

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show overview of all users"""
    # Get spending of user
    personnel = db.execute('SELECT personnel.personnel_id, name, deposit FROM personnel')
    spending = db.execute("""SELECT p.personnel_id, c.claim_name, s.amount * s.cost AS individual_cost, s.datetime
                            FROM spending s
                            JOIN claim_type c ON s.claim_id = c.claim_id
                            JOIN personnel p ON s.personnel_id = p.personnel_id
                            """)
    claims = db.execute("""SELECT p.personnel_id, c.claim_name, SUM(s.amount * s.cost) AS total_cost, s.datetime
                            FROM spending s
                            JOIN claim_type c ON s.claim_id = c.claim_id
                            JOIN personnel p ON s.personnel_id = p.personnel_id
                            GROUP BY c.claim_name
                            """)
    print(claims)
    print(spending)
    print(personnel)
    return render_template('index.html', personnel=personnel, spending=spending, claims=claims)


@app.route('/user_config', methods=['POST', 'GET'])
@login_required
def user_config():
    """Allows admin to add or remove personnel"""
    # GET
    if request.method != 'POST':
        return render_template('user_config.html', USER_CONFIG=USER_CONFIG)
    select = request.form.get('config')
    return redirect(f'/{select}')


# Claims
@app.route('/claims', methods=['GET', 'POST'])
@login_required
def claims_config():
    """ Read Claims, Update an Individual's Claim """
    # Get all claims
    claims = db.execute('SELECT claim_id, claim_name FROM claim_type')
    spending = db.execute("""SELECT spending.personnel_id, spending.claim_id, spending.amount, spending.cost, SUM(spending.amount * spending.cost) AS total_cost, claim_type.claim_name
                            FROM spending
                            JOIN claim_type ON spending.claim_id = claim_type.claim_id
                            GROUP BY spending.personnel_id, spending.claim_id""")
    individual_user_claim = db.execute("""SELECT s.id, p.personnel_id, c.claim_name, s.amount * s.cost AS individual_cost, s.datetime
                                            FROM spending s
                                            JOIN claim_type c ON s.claim_id = c.claim_id
                                            JOIN personnel p ON s.personnel_id = p.personnel_id
                                            """)
    # print(individual_user_claim)
    # print(spending)
    personnel = db.execute('SELECT personnel_id, name FROM personnel')
    if request.method != 'POST':
        return render_template('claims.html',
        claims=claims, personnel=personnel, spending=spending, individual_user_claim=individual_user_claim)

    # Update a personnel's claim
    personnel_id = request.form.get('personnelID')
    claim_id = request.form.get('claimID')
    try:
        number_of_claims = int(request.form.get('numberOfClaims'))
        cost_per_claim = float(request.form.get('costPerClaim'))
    # RemoveUserClaim does not require number/cost
    except TypeError:
        pass

    claim_action = request.form.get('userClaimAction')
    if claim_action == 'addUserClaim':
        flash('Added new claim!')
        # Insert into spending table DB
        db.execute('INSERT INTO spending (personnel_id, claim_id, amount, cost) VALUES (?, ?, ?, ?)',
                personnel_id, claim_id, number_of_claims, cost_per_claim)
    elif claim_action == 'editUserClaim':
        flash('Edited claim!')
        spending_id = request.form.get('spendingID')
        db.execute('UPDATE spending SET amount = ?, cost = ?, datetime = ? WHERE id = ?',
        number_of_claims, cost_per_claim, datetime.now(), spending_id)
    else:
        flash('Removed claim!', 'error')
        spending_id = request.form.get('spendingID')
        print(spending_id)
        db.execute('DELETE FROM spending WHERE id = ?', spending_id)

    return redirect('/')


@app.route('/add_claim_type', methods=['POST'])
@login_required
def add_claim_type():
    """ Create new Claim Type """
    add_claim = request.form.get('addClaim')

    # Validation
    if not add_claim:
        return apology('Please key in something for the claim name')
    flash(f'{add_claim} has been added to the list of claims!')
    # update DB
    db.execute('INSERT INTO claim_type (claim_name) VALUES (?)', add_claim)
    return redirect('/claims')


@app.route('/edit_claim_type', methods=['POST'])
@login_required
def edit_claim_type():
    """ Edit existing claim type """
    original_claim_id = request.form.get('originalClaimID')
    update_claim = request.form.get('updatedClaim')
    print(original_claim_id, update_claim)
    # Validation
    if not update_claim:
        return apology('Please key in something for the new claim name')
    flash(f'Changed to {update_claim}!')
    db.execute('UPDATE claim_type SET claim_name = ? WHERE claim_id = ?', update_claim, original_claim_id)
    return redirect('/claims')


@app.route('/remove_claim_type', methods=['POST'])
@login_required
def remove_claim_type():
    """ Remove existing claim type """
    claim_id = request.form.get('removeClaimID')
    db.execute('DELETE FROM claim_type WHERE claim_id = ?', claim_id)
    return redirect('/claims')


@app.route('/add_user', methods=['POST', 'GET'])
@login_required
def add_user():
    # GET
    if request.method != 'POST':
        return render_template('add_user.html')

    # POST
    # Validate name
    input_name = request.form.get('user')
    if not input_name:
        return apology('Name is a required field')
    existing_personnel = db.execute('SELECT name FROM personnel')

    for personnel in existing_personnel:
        if personnel['name'] == input_name:
            return apology('User already exists!')

    # Validate deposit
    deposit = request.form.get('deposit')
    if float(deposit) < 0:
        return apology('Invalid value for deposit')


    # Update DB
    db.execute('INSERT INTO personnel (name, deposit) VALUES (?, ?)', input_name.lower(), float(deposit))

    # Redirect to home
    flash(f'{input_name} has been added.')
    return redirect('/')


@app.route('/remove-personnel', methods=['GET', 'POST'])
def remove_user():
    """ Remove user """
    if request.method != 'POST':
        personnel = db.execute('SELECT personnel_id, name FROM personnel')
        return render_template('remove-personnel.html', personnel=personnel)
    personnel_id, _ = request.form.get('personnel').split('-')
    flash('Personnel removed!')
    db.execute('DELETE from personnel WHERE personnel_id = ?', personnel_id)
    return redirect('/')


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():
    """Deposit Money"""
    personnel = db.execute('SELECT personnel_id, name, deposit FROM personnel')
    if request.method != 'POST':
        return render_template('deposit.html', personnel=personnel)
    # Get personnel ID for transaction
    personnel_id = request.form.get('personnelID')

    # Get input deposit
    new_deposit = float(request.form.get('deposit'))

    # Get current deposit
    current_deposit = db.execute('SELECT deposit FROM personnel WHERE personnel_id = ?',
                                 personnel_id)[0]['deposit']

    # Update deposit in DB
    new_deposit += current_deposit
    db.execute('UPDATE personnel SET deposit = ? WHERE personnel_id = ?',
               new_deposit, personnel_id)
    flash('Deposit successfully!')
    return redirect('/')



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # checks if name is blank

    if request.method != 'POST':
        return render_template('register.html')
    username = request.form.get('username')

    # Check for empty field
    if not len(username):
        return apology('Registration Fail')

    # Check for existing username
    existing_users = db.execute('SELECT username FROM users')
    for user_data in existing_users:
        if user_data['username'] != username:
            continue
        return apology('Use another username')

    pwd = request.form.get('password')
    cfm_pwd = request.form.get('confirmation')
    if pwd != cfm_pwd or not pwd:
        return apology('Registration Fail')
    # store username and pwd
    hashed_pwd = generate_password_hash(pwd)
    db.execute('INSERT INTO users (username, hash) VALUES (?, ?)', username, hashed_pwd)
    flash('Registered successfully. Please login.')
    return render_template('login.html')


@app.route("/chgpwd", methods=["GET", "POST"])
@login_required
def change_pwd():
    """Change user's pwd"""

    if request.method != 'POST':
        return render_template('chgpwd.html')

    curr_pwd = request.form.get('curr_password')

    db_hashed_pwd = db.execute('SELECT hash FROM users where id = ?', session['user_id'])[0]['hash']
    if not check_password_hash(db_hashed_pwd, curr_pwd):
        return apology('Invalid info')

    new_pwd = request.form.get('new_password')

    verify_new_pwd = request.form.get('new_password_2')
    print(new_pwd, verify_new_pwd)

    if new_pwd != verify_new_pwd:
        return apology('Passwords did not match')

    new_hash = generate_password_hash(new_pwd)

    # update hash
    db.execute('UPDATE users SET hash = ? WHERE id = ?', new_hash, session['user_id'])
    logout()
    flash('Password changed! Log in again.')
    return render_template('login.html')
