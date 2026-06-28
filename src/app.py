from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
import pandas as pd
from datetime import datetime

app = Flask(__name__)
app.secret_key = "ayush123"


# ================= DATABASE =================

def init_db():
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()

    # Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    ''')

    # Income Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS income(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL,
            source TEXT,
            date TEXT
        )
    ''')

    # Expense Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expense(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL,
            category TEXT,
            date TEXT
        )
    ''')

    conn.commit()
    conn.close()


init_db()

# ================= SIGNUP =================

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':

     username = request.form['username']
     email = request.form['email']
     password = request.form['password']

    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users(username, email, password) VALUES (?, ?, ?)",
            (username, email, password)
        )

        conn.commit()
        conn.close()

        return redirect('/login')

    except sqlite3.IntegrityError:
        conn.close()
        return "Email already exists! Please use another email."

        return render_template('signup.html')
       
# ================= LOGIN =================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('finance.db')
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        )

        user = cursor.fetchone()

        conn.close()

        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]

            return redirect('/')

        else:
            return "Invalid Email or Password"

    return render_template('login.html')

# ================= HOME =================

@app.route('/')
def home():

    if 'user_id' not in session:
     return redirect('/login')

    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM income")
    incomes = cursor.fetchall()

    cursor.execute("SELECT * FROM expense")
    expenses = cursor.fetchall()

    cursor.execute("SELECT SUM(amount) FROM income")
    total_income = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(amount) FROM expense")
    total_expense = cursor.fetchone()[0]

    conn.close()

    if total_income is None:
        total_income = 0

    if total_expense is None:
        total_expense = 0

    balance = total_income - total_expense

    return render_template(
        'index.html',
        incomes=incomes,
        expenses=expenses,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance
    )



# ================= LOGOUT =================

@app.route('/logout')
def logout():

    session.pop('user_id', None)
    session.pop('username',None)

    return redirect('/login')


# ================= ADD INCOME =================

@app.route('/add-income', methods=['GET', 'POST'])
def add_income():

    if request.method == 'POST':

        amount = request.form['amount']
        source = request.form['source']
        date = datetime.now().strftime("%d-%m-%Y")

        conn = sqlite3.connect('finance.db')
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO income(amount, source, date) VALUES (?, ?, ?)",
            (amount, source, date)
        )

        conn.commit()
        conn.close()

        return redirect('/')

    return render_template('add_income.html')


# ================= ADD EXPENSE =================

@app.route('/add-expense', methods=['GET', 'POST'])
def add_expense():

    if request.method == 'POST':

        amount = request.form['amount']
        category = request.form['category']
        date = datetime.now().strftime("%d-%m-%Y")

        conn = sqlite3.connect('finance.db')
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO expense(amount, category, date) VALUES (?, ?, ?)",
            (amount, category, date)
        )

        conn.commit()
        conn.close()

        return redirect('/')

    return render_template('add_expense.html')


# ================= DELETE INCOME =================

@app.route('/delete-income/<int:id>')
def delete_income(id):

    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM income WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect('/')


# ================= DELETE EXPENSE =================

@app.route('/delete-expense/<int:id>')
def delete_expense(id):

    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM expense WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect('/')


# ================= EXPORT EXCEL =================

@app.route('/export')
def export():

    conn = sqlite3.connect('finance.db')

    income_df = pd.read_sql_query(
        "SELECT * FROM income",
        conn
    )

    expense_df = pd.read_sql_query(
        "SELECT * FROM expense",
        conn
    )

    conn.close()

    with pd.ExcelWriter("finance_report.xlsx") as writer:

        income_df.to_excel(
            writer,
            sheet_name="Income",
            index=False
        )

        expense_df.to_excel(
            writer,
            sheet_name="Expense",
            index=False
        )

    return send_file(
        "finance_report.xlsx",
        as_attachment=True
    )


# ================= RUN APP =================

if __name__ == '__main__':
    app.run(debug=True)