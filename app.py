
from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import sqlite3

app = Flask(__name__)

# Carregar os dados iniciais da planilha
df = pd.read_excel('EXPORT_20250507_145515.XLSX', sheet_name='Sheet1')
df.to_sql('sap_data', sqlite3.connect('database.db'), if_exists='replace', index=False)

# Banco de dados
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    results = []
    if request.method == 'POST':
        sap = request.form['sap']
        conn = get_db_connection()
        results = conn.execute('SELECT * FROM sap_data WHERE Material = ?', (sap,)).fetchall()
        conn.close()
    return render_template('search.html', results=results)

@app.route('/request_change', methods=['GET', 'POST'])
def request_change():
    if request.method == 'POST':
        sap = request.form['sap']
        new_address = request.form['new_address']
        conn = get_db_connection()
        conn.execute('INSERT INTO change_requests (sap, new_address, status) VALUES (?, ?, ?)', 
                     (sap, new_address, 'Pending'))
        conn.commit()
        conn.close()
        return redirect(url_for('request_change'))
    return render_template('request_change.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    conn = get_db_connection()
    requests = conn.execute('SELECT * FROM change_requests WHERE status = "Pending"').fetchall()
    conn.close()
    return render_template('admin.html', requests=requests)

@app.route('/admin/approve/<int:id>')
def approve(id):
    conn = get_db_connection()
    req = conn.execute('SELECT * FROM change_requests WHERE id = ?', (id,)).fetchone()
    if req:
        conn.execute('UPDATE sap_data SET "Posição no depósito" = ? WHERE Material = ?', 
                     (req["new_address"], req["sap"]))
        conn.execute('UPDATE change_requests SET status = "Approved" WHERE id = ?', (id,))
        conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/admin/reject/<int:id>')
def reject(id):
    conn = get_db_connection()
    conn.execute('UPDATE change_requests SET status = "Rejected" WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS change_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sap TEXT NOT NULL,
                    new_address TEXT NOT NULL,
                    status TEXT NOT NULL)''')
    conn.commit()
    conn.close()
    app.run(debug=True)
