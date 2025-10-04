import os
import uuid
import io
import qrcode
import requests
import smtplib
from urllib.parse import urlencode
from flask import Flask, render_template, request, redirect, url_for, flash
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import mercadopago
import PIL

app = Flask(__name__)
app.secret_key = 'cx1228@'

# Configuração Mercado Pago
MERCADO_TOKEN = "APP_USR-4269419174287132-100118-d5000064cd6d942fc03f594ab2d77212-50261275"
sdk = mercadopago.SDK(MERCADO_TOKEN)

# Função para gerar QR Code em memória
def gerar_qrcode(conteudo):
    img = qrcode.make(conteudo)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

# Função para verificar status do pagamento
def verificar_pagamento(payment_id):
    url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
    headers = {"Authorization": f"Bearer {MERCADO_TOKEN}"}
    response = requests.get(url, headers=headers)
    return response.json()

# Função para enviar e-mail com QR Code
def enviar_email_com_qrcode(destinatario, corpo, qr_buffer):
    remetente = "acfantasy3@gmail.com"
    senha = "hkcaouharwcfxpyj"

    msg = MIMEMultipart()
    msg["Subject"] = "Ingressos Halloween"
    msg["From"] = remetente
    msg["To"] = destinatario
    msg.attach(MIMEText(corpo, "plain"))
    imagem = MIMEImage(qr_buffer.read(), name="qrcode.png")
    msg.attach(imagem)
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(remetente, senha)
            server.sendmail(remetente, destinatario, msg.as_string())
        print("Email com QR Code enviado!")
    except Exception as e:
        print(f"Erro ao enviar email: {e}")

# Rota inicial
@app.route("/")
def home():
    return redirect(url_for("about"))

@app.route("/about")
def about():
    return render_template("about.html")

# Rota de compra
@app.route("/buy", methods=["GET", "POST"])
def buy():
    if request.method == "GET":
        return render_template("buy.html")

    name = request.form.get("name")
    age = request.form.get("age")
    email = request.form.get("email")

    if not sdk:
        flash("Erro: Mercado Pago não configurado.", "error")
        return redirect(url_for("buy"))

    # Cria preferência de pagamento
    preference_data = {
        "items": [{
            "title": "Ingresso Halloween",
            "quantity": 1,
            "unit_price": 5
        }],
        "payer": {"name": name},
        "back_urls": {
            "success": url_for("success", _external=True),
            "failure": url_for("failure", _external=True),
            "pending": url_for("pending", _external=True),
        },
        "auto_return": "approved",
        "notification_url": "https://ingressos-halloween.onrender.com/notificacao",
        "external_reference": urlencode({"name": name, "age": age, "email": email})
    }

    pref = sdk.preference().create(preference_data)
    init_point = pref["response"]["init_point"]
    return redirect(init_point)

# Rota de notificação do Mercado Pago
@app.route("/notificacao", methods=["POST"])
def notificacao():
    data = request.json
    if not data or "data" not in data or "id" not in data["data"]:
        return "Ignorado", 400

    payment_id = data["data"]["id"]
    pagamento = verificar_pagamento(payment_id)

    if pagamento.get("status") == "approved":
        ref = pagamento.get("external_reference", "")
        params = dict(x.split("=") for x in ref.split("&"))
        name = params.get("name")
        age = params.get("age")
        email = params.get("email")

        dados = {"name": name, "age": age, "email": email}
        url_base = "https://ingressos-halloween.onrender.com/ingresso"
        url_com_dados = f"{url_base}?{urlencode(dados)}"
        qr_buffer = gerar_qrcode(url_com_dados)

        enviar_email_com_qrcode(
            destinatario=email,
            corpo="Segue o QR code para identificação na portaria do evento!",
            qr_buffer=qr_buffer
        )
        return "Email enviado", 200

    return "Pagamento não aprovado", 200

# Rota de sucesso
@app.route("/success")
def success():
    return render_template("success.html", status="Pagamento aprovado 🎉")

# Rota de ingresso via QR Code
@app.route("/ingresso")
def ingresso():
    name = request.args.get("name")
    email = request.args.get("email")
    age = request.args.get("age")

    if not all([name, email, age]):
        return "Dados incompletos", 400

    return render_template("ingresso.html", name=name, email=email, age=age)

# Rotas de falha e pendente
@app.route("/failure")
def failure():
    return render_template("success.html", status="Pagamento não aprovado ❌")

@app.route("/pending")
def pending():
    return render_template("success.html", status="Pagamento pendente ⏳")

# Executa o servidor
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
