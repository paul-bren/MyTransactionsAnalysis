
import pymysql.cursors
from datetime import datetime
from flask import Flask, request, render_template, redirect, url_for, flash, session
import os
from forms import LoginForm_1
import pandas as pd
import numpy as np
from datetime import datetime, date
from RegistrationForm import RegistrationForm

app = Flask(__name__)
app.secret_key = 'pass'

#upload_folder='/app/data_2_examine'
upload_folder='C:/Users/paulb/OneDrive/Documents/MyWork/MyTranscationsAnalysis/data_2_examine' # change to above 'upload_folder' when running in docker container
app.config['upload_folder'] = upload_folder

class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password

def connect_to_db():
    db = pymysql.connect(host='localhost', #hostname will be diff once i run this in docker container
    user='root',         
    passwd='pass', 
    port=3306,
    database='boi')
    return db

@app.route("/", methods=['GET', 'POST'])
def loginForm():
    form = LoginForm_1()
    if request.method == 'POST' and form.validate_on_submit():
        # get form data
        username = request.form['username']
        password = request.form['password']

        # check if username exists in database
        db = connect_to_db()
        cursor=db.cursor()
        cursor.execute('SELECT * FROM users WHERE username = %s', [username])
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user:
            # check password against database value
            if user[1] == password:
                session['authenticated'] = True
                # login successful, redirect to user dashboard
                session['username'] = username
                return redirect(url_for('home', username=username))
            else:
                # password is incorrect
                return('Incorrect password. Please try again.')
        else:
            # username is not found
            flash('Username not found. Please try again.')

    # display login page with form
    return render_template('login.html', form=form)

@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    form = RegistrationForm()
    if form.validate_on_submit():
        user_details = User(username=form.username.data, password=form.password.data)
        db = connect_to_db()
        cursor = db.cursor()
        query = ('Insert into users (username, password) values (%s,%s)')
        values = (user_details.username, user_details.password)
        cursor.execute (query, values)
        db.commit()
        cursor.close()
        db.close()
        return redirect(url_for('loginForm'))
        #return('Account created')
    return render_template('create_account.html', title='Create Account', form=form)


@app.route("/home", methods=['GET', 'POST'])
def home():
    if 'authenticated' in session and session['authenticated']:
        print(session['username'])
        return render_template('home.html')
    else:
        return redirect('/')
    #return render_template('home.html')

@app.route("/upload", methods=['GET', 'POST'])
def upload():
    if 'authenticated' in session and session['authenticated']:
        #return render_template('home.html')
        db = connect_to_db()
        cursor=db.cursor()
        if request.method == 'POST':
            file = request.files['file']
            if request.files['file'].filename == '':
                return 'Error: No file selected for upload'
            elif not request.files['file'].filename.endswith((".xlsx", ".csv")):
                return 'Error: Please only upload .xlsx or .csv file formats'
            filename = file.filename
            uploaded_file = None
            file.save(os.path.join(app.config['upload_folder'], filename))
            os.chdir(upload_folder)
            for upload_file in os.listdir():
                if upload_file.endswith(".xlsx"):
                    df = pd.read_excel(upload_file, engine='openpyxl')
                    uploaded_file = upload_file
                    break
                elif upload_file.endswith(".csv"):
                    df = pd.read_csv(upload_file)
                    uploaded_file = upload_file
                    break
            df['insertdate'] = datetime.now()
            df['date'] = pd.to_datetime(df.iloc[:,0].replace(np.nan, '01/01/1991'), format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
            df['full_transaction'] = df.iloc[:, 1].str.replace('\s+', ' ', regex=True).str.rstrip()
            df['vendor_data'] = df.iloc[:, 1].str.replace('\s+', ' ', regex=True).str.rstrip()
            vendor = []
            for i in range(len(df)):
                vendor_data = str(df['vendor_data'].iloc[i])
                if vendor_data[:3] == 'POS':
                    vendor.append(' '.join(vendor_data.split(' ')[1:])) 
                else:
                    vendor.append(vendor_data) 
            df['vendor'] = vendor
            df['debit'] = df.iloc[:, 2].replace(np.nan, 0)
            df['credit'] = df.iloc[:, 3].replace(np.nan, 0)
            df['balance'] = df.iloc[:, 4].replace(np.nan, 0)
    

            max_date_query = ("select max(date) from items where user = %s")
            value_for_max_date = session['username']
            cursor.execute(max_date_query, value_for_max_date)
            max_date_tuple = cursor.fetchone()
            max_date = max_date_tuple[0] if max_date_tuple is not None else None

            for i, row in df.iterrows():
                if i == df.index[-1]:
                    break # remove the bottom line
                elif row['date'] == str(date.today()):
                    continue  # skip the row if the date is today
                elif max_date is not None:
                    row_date = datetime.strptime(row['date'], '%Y-%m-%d')
                    if row_date <= max_date:
                        continue
                try:
                    query2 = """INSERT INTO items (insertdate,date,full_transaction,vendor,debit,credit,balance,user) 
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s) """
                    values = (row['insertdate'], row['date'], row['full_transaction'], row['vendor'], row['debit'], row['credit'], row['balance'], session['username'])
                    cursor.execute (query2, values)
                    db.commit()
                except Exception as e:
                    print("Error:", e)
                    cursor.rollback()
            cursor.close()
            db.close()
            if uploaded_file is not None:
                print(uploaded_file)
                os.remove(os.path.join(app.config['upload_folder'], uploaded_file))
        
            return ("File uploaded successfully")
    else:
        return redirect('/')
    return render_template('upload.html')

@app.route("/DataInsight", methods=['GET', 'POST'])
def data_insights():
    if 'authenticated' in session and session['authenticated']:
        print(session['username'])
        return render_template('DataInsight.html')
    else:
        return redirect('/')

@app.route('/logout')
def logout():
    # clear the session and redirect to login page
    session['authenticated'] = False
    session.clear()
    return redirect(url_for('loginForm'))

  
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8090) 
