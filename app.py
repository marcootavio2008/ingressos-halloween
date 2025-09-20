from flask import Flask, render_template, request, redirect, url_for, flash
import os
import re
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'cx1228@'  # necessário para flash messages

# --- CONFIG ---
PIX_KEY = '011a7ecd-24c3-4552-bbd0-e09510ad4093'  # <--- troque para sua chave PIX real

# --- Rotas ---
@app.route('/')
def home():
    return redirect(url_for('about'))

@app.route('/about')
def about():
    # Adiciona botão para ir para a página de compra
    return render_template('about.html', title='Sobre', buy_url=url_for('buy'))

@app.route('/buy', methods=['GET', 'POST'])
def buy():
    if request.method == 'GET':
        return render_template('buy.html', title='Comprar', pix_key=PIX_KEY, home_url=url_for('about'))

    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    age_raw = request.form.get('age', '').strip()
    ticket_type = request.form.get('ticket_type', 'comum')

    if not name or not email:
        flash('Nome e email são obrigatórios.', 'error')
        return redirect(url_for('buy'))

    try:
        age = int(age_raw)
    except ValueError:
        flash('Idade inválida.', 'error')
        return redirect(url_for('buy'))

    if ticket_type == 'vip' and age < 18:
        flash('Ingresso VIP somente para maiores de 18 anos.', 'error')
        return redirect(url_for('buy'))

    return render_template('confirm.html', title='Confirmado',
                           name=name, email=email, ticket_type=ticket_type, home_url=url_for('about'))

if __name__ == '__main__':
    app.run(debug=True, port=8000)
