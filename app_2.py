
import pymysql.cursors
import openpyxl
from datetime import datetime
from flask import Flask, request, render_template
import os
import pandas as pd
import numpy as np

app = Flask(__name__)

#upload_folder='/app/data_2_examine'
upload_folder='C:/Users/paulb/OneDrive/Documents/MyWork/MyTranscationsAnalysis/data_2_examine'
app.config['upload_folder'] = upload_folder

def connect_to_db():
    db = pymysql.connect(host='localhost',
    user='root',         
    passwd='pass', 
    port=3306,
    database='boi')
    return db
          

@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        filename = file.filename
        file.save(os.path.join(app.config['upload_folder'], filename))
        os.chdir(upload_folder)
        for upload_file in os.listdir():
            if upload_file.endswith(".xlsx"):
                df = pd.read_excel(upload_file, engine='openpyxl')
                break
            elif upload_file.endswith(".csv"):
                df = pd.read_csv(upload_file)
                break
        db = connect_to_db()
        cursor=db.cursor()
        query1 = ("truncate items;")
        cursor.execute(query1)

        df['insertdate'] = datetime.now()
        #df['date'] = df.iloc[:, 0]
        #df['date'] = pd.to_datetime(df.iloc[:,0], format='%Y-%m-%d')
        df['date'] = pd.to_datetime(df.iloc[:,0].replace(np.nan, '20/02/2023'), format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
        df['full_transaction'] = df.iloc[:, 1].replace(np.nan, None)
        df['vendor_data'] = df.iloc[:, 1]
        vendor = []
        for i in range(len(df)):
            vendor_data = str(df['vendor_data'].iloc[i])
            if vendor_data[:3] == 'POS':
                vendor.append(' '.join(vendor_data.split(' ')[1:])) 
            else:
                vendor.append(vendor_data) 
        df['vendor'] = vendor
        df['debit'] = df.iloc[:, 2].replace(np.nan, 0)
        df['credit'] = df.iloc[:, 3].replace(np.nan, None)
        df['balance'] = df.iloc[:, 4].replace(np.nan, None)
        for i, row in df.iterrows():
            try:
                query2 = """INSERT INTO items (insertdate,date,full_transaction,vendor,debit,credit,balance) VALUES (%s,%s,%s,%s,%s,%s,%s)"""
                values = (row['insertdate'], row['date'], row['full_transaction'], row['vendor'], row['debit'], row['credit'], row['balance'])
                cursor.execute (query2, values)
                db.commit()
            except:
                print("Unable to connect to db")
                cursor.rollback()
    return render_template('index.html')
  
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8090) 
