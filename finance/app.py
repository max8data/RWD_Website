import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


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

    # Use database's history table to extract data for building personal portfolio
    # First get user id from session
    id = session["user_id"]
    portfolio = []

    # Get distinct symbol and share's number.
    symbol = db.execute(
        "SELECT DISTINCT symbol, SUM(shares) AS shares FROM history WHERE id = ? GROUP BY symbol HAVING SUM(shares) > 0", id)
    print(f"symbol in index:{symbol}")
    # Get current price using lookup() then append symbol, shares, current price, to portfolio: list of dictionary
    for sym in symbol:
        price_row = lookup(sym["symbol"])
        if price_row is not None:
            price = price_row["price"]
            print(f"price in index: {type(price)}")
        else:
            price = None
        portfolio.append({"symbol": sym["symbol"], "shares": sym["shares"], "price": price})
        print(f"init_portfolio in index: {portfolio}")
        for item in portfolio:
            print(f"symbol in portfolio: {type(item['symbol'])}")
            print(f"shares in portfolio: {type(item['shares'])}")
            print(f"price in portfolio: {type(item['price'])}")

    # Get cash from history table, filter by session id
    cash_row = db.execute("SELECT cash FROM history WHERE id = ? ORDER BY timestamp DESC LIMIT 1", id)

    if cash_row:
        cash = cash_row[0]["cash"]
        print(f"cash in index: {type(cash)}")
    # If user has no row in history table, then use user table's default cash value
    else:
        cash = db.execute("SELECT cash FROM users WHERE id = ?", id)[0]["cash"]
    print(f"cash in index:{cash} {type(cash)}")
    # Total asset = cash + all stock value
    total_asset = cash
    print(f"init_total_asset in index:{total_asset} {type(total_asset)}")
    for item in portfolio:
        total_asset += item["price"] * item["shares"]
        item["total"] = item["price"] * item["shares"]
    print(f"total_asset in index:{total_asset} {type(total_asset)}")
    print(f"portfolio in index: {portfolio}")
    print(f"cash in index before passing: {cash}")

    return render_template("index.html", portfolio=portfolio, cash=cash, total_asset=total_asset)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    # If via get, return a form for users to fill out what symbol and how many to buy.
    if request.method == "GET":
        return render_template("buy.html")

    # If via POST means users fill out the form and want to buy: check for stock existence and affordability.
    if request.method == "POST":

        # Checks if there are inputs
        symbol = request.form.get("symbol")
        if not symbol:
            return apology("Plz type in stock symbol")
        shares_input = request.form.get("shares")
        if not shares_input or not shares_input.isdigit():
            return apology("Plz check shares field")
        elif int(shares_input) < 1:
            return apology("Min share purchase is 1")
        shares = int(request.form.get("shares"))

        # Checks if inputs can be used to fetch quote by lookup() function
        quote = lookup(symbol)
        if not quote:
            return apology("No quote for such symbol")
        price = lookup(symbol)["price"]
        print(f"price in buy: {type(price)}")
        if not price:
            return apology("No price for such symbol")
        try:
            symbol = symbol.upper()
        except AttributeError:
            symbol = symbol

        # Checks for users' affordability and update user's cash status
        rows = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        cash = rows[0]["cash"]
        print(f"cash in buy: {type(cash)}")
        sum = price * shares
        balance = cash - sum
        print(f"balance in buy: {type(balance)}")

        if balance > 0:
            # To keep logs in history table: first get username
            username_row = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])
            username = username_row[0]["username"]

            # Insert the transaction to the history table
            db.execute("INSERT INTO history (id, username, shares, symbol, cash, price) VALUES(?, ?, ?, ?, ?, ?)",
                       session["user_id"], username, shares, symbol, balance, price)
            # Updte user's cash in user table
            db.execute("UPDATE users SET cash = ? WHERE id = ?", balance, session["user_id"])

            flash("You've bought it!")
            return redirect("/")
        else:
            return apology(f"Low on cash, please check")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    rows = db.execute("SELECT symbol, shares, timestamp, price FROM history WHERE id=?", session["user_id"])
    count_row = db.execute("SELECT COUNT(*) AS count FROM history WHERE id=?", session["user_id"])
    counts = count_row[0]["count"]

    return render_template("history.html", rows=rows, counts=counts)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any previous activities
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
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["username"] = request.form.get("username")

        # Redirect user to home page
        flash("This is C$50!")
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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    # When user visit by "get", return the plage for them to query
    if request.method == "GET":
        return render_template("quote.html")

    # When form submit by POST means user type in and want to know the quote(ideally)
    if request.method == "POST":
        # Check if any input, in not, return apology, if yes then make it capitalized and use lookup() to get quote; if no quote then return apology
        symbol = request.form.get("symbol")
        if not symbol:
            return apology("Plz type in stock symbol")
        try:
            symbol = symbol.upper()
        except AttributeError:
            symbol = symbol
        quote = lookup(symbol)
        if not quote:
            return apology("No quote for such symbol")
        price = lookup(symbol)["price"]
        if not price:
            return apology("No price for such symbol")
        print(f"symbol: {type(symbol)}")
        print(f"price: {type(price)}")

        return render_template("quoted.html", symbol=symbol, price=price)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # By get: let users fill out the form
    if request.method == "GET":
        return render_template("register.html")

    # By post: add to db if check ok
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Check if all fields are filled out, if either is blank then return apology
        if not username or not password or not confirmation:
            return apology("Forgot some fields?", 400)

        # Check if username is already in the databse, if so means taken, return apology
        rows = db.execute("SELECT * FROM users WHERE username=?", username)
        if len(rows) != 0 and username == rows[0]["username"]:
            return apology("Username taken", 400)

        # Check if user's password matches password confirmation.
        if password != confirmation:
            return apology("Plz check password", 400)

        # If registration succeeds, insert the data into database and store user session by their id to keep users logged in, then redirect to index.html
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username,
                   generate_password_hash(password, method='pbkdf2', salt_length=16))
        rows = db.execute("SELECT * FROM users WHERE username=?", username)
        session["user_id"] = rows[0]["id"]
        flash("You're one of us now, welcome!")
        return redirect("/")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    # Show user sell form when visit sell page via get
    if request.method == "GET":
        symbols = db.execute(
            "SELECT DISTINCT symbol AS symbol FROM history WHERE id = ? GROUP BY symbol HAVING SUM(shares) > 0", session["user_id"])
        print(f"symbols in sell via get {symbols}")
        return render_template("sell.html", symbols=symbols)

    # When users submit the sell form
    if request.method == "POST":
        # Checks if there's symbol input and if shares inputs digits( .isdigit() checks for whole number and > 0)
        symbol = request.form.get("symbol")
        if not symbol:
            return apology("Plz type in stock symbol")
        shares = request.form.get("shares")
        if not shares or not shares.isdigit():
            return apology("Please enter how many to sell")
        # If shares is a digit then check if it's >= 1, if so then convert it to int and store it in variable shares
        elif int(request.form.get("shares")) < 1:
            return apology("Min share purchase is 1")
        else:
            print(f"init_shares in sell: {type(shares)}\n")
            shares = int(request.form.get("shares"))
            print(f"shares in sell: {type(shares)}\n")

        # Checks if the user own enough shares to sell
        # First get this user's distinct symbol and shares sum using database history table and store the data in a dictionary
        sym_query = db.execute(
            "SELECT DISTINCT symbol, SUM(shares) as shares FROM history WHERE id=? GROUP BY symbol", session["user_id"])
        print(f"sym_query in sell: {sym_query}\n") # [{'symbol': 'AAPL', 'shares': 5}, {'symbol': 'HPQ', 'shares': 0}]

        # Check if the user owns any symbol and if they can afford to sell the desired shared of symbol
        # First get a list of symbols user owns, extracting from sym_query, the list of dictionary above
        if sym_query:
            sym_list = [row["symbol"] for row in sym_query]
            print(f"sym_list in sell: {sym_list}\n") # sym_list in sell: ['AAPL', 'HPQ']
        else:
            return apology("Seems like you haven't done any transactions here")

        if symbol not in sym_list:
            return apology(f"You don't own enough {symbol}")

        # If the selling symbol is in the owned list, check if the user own greater or equal to how many want to sell
        for item in sym_query:
            if symbol == item["symbol"] and shares > item["shares"]:
                return apology(f"Not enough {symbol} to sell")

        # update user's cash status
        price = lookup(symbol)["price"]
        print(f"lookup(symbol)['price'] is type: {type(lookup(symbol)['price'])}\n")
        cash_rows = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        print(f"cash_rows in sell: {cash_rows}\n")
        cash = cash_rows[0]["cash"]
        print(f"cash in sell: {type(cash)}\n")
        sum = price * shares
        print(f"sum in sell: {type(sum)}\n")
        balance = cash + sum
        print(f"balance in sell: {type(balance)}\n")
        # Updte user's cash in user table
        db.execute("UPDATE users SET cash = ? WHERE id = ?", balance, session["user_id"])

        # To keep logs in history table: first get username
        username_row = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])
        username = username_row[0]["username"]

        db.execute("INSERT INTO history (id, username, shares, symbol, cash, price) VALUES(?, ?, ?, ?, ?, ?)",
                   session["user_id"], username, -shares, symbol, balance, price)
        flash("Sold it!")
        return redirect("/")


@app.route("/reset", methods=["GET", "POST"])
@login_required
def reset():
    # Return the reser.html page when users first click "Change Password"
    if request.method == "GET":
        return render_template("reset.html")

    # After users sumbit the reset form, first check if all field are filled out
    if request.method == "POST":
        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")
        new_password_confirmation = request.form.get("new_password_confirmation")
        if not old_password or not new_password or not new_password_confirmation:
            return apology("Please check")

        # If all filled out then first check if new password matches new password confirmation
        if new_password != new_password_confirmation:
            return apology("Please check new password")

        # Check if the old password is correct as compared to database's hash
        user_row = db.execute("SELECT hash FROM users WHERE id=?", session["user_id"])
        if user_row:
            hash = user_row[0]["hash"]
        else:
            return apology("Something went wrong")

        if not check_password_hash(hash, old_password):
            return apology("Please check password")
        else:
            db.execute("UPDATE users SET hash=? WHERE id=?", generate_password_hash(new_password), session["user_id"])

        flash("Password Changed Successfully")
        return redirect("/")

