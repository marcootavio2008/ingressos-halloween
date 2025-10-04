import os
from flask import Flask, render_template, request, redirect, url_for, flash
import mercadopago
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import uuid
import qrcode
import io
from urllib.parse import urlencode

def gerar_qrcode(conteudo):
    img = qrcode.make(conteudo)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

app = Flask(__name__)
app.secret_key = 'cx1228@'
MERCADO_TOKEN = "APP_USR-4269419174287132-100118-d5000064cd6d942fc03f594ab2d77212-50261275"
sdk = mercadopago.SDK(MERCADO_TOKEN)

def verificar_pagamento(payment_id):
    url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
    headers = {
        "Authorization": f"Bearer {MERCADO_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    return response.json()

def enviar_email_com_qrcode(destinatario, corpo, qr_buffer):
    remetente = "acfantasy3@gmail.com"
    senha = "hkcaouharwcfxpyj"
    msg = MIMEMultipart()
    msg["Subject"] = "Ingressos Halloween"
    msg["From"] = remetente
    msg["To"] = destinatario

    msg.attach(MIMEText(corpo, "plain"))

    # Anexa o QR Code PNG
    with open(qr_buffer, "rb") as f:
        imagem = MIMEImage(f.read(), name="buffer.png")
        msg.attach(imagem)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(remetente, senha)
            server.sendmail(remetente, destinatario, msg.as_string())
        print("Email com QR Code enviado!")
    except Exception as e:
        print(f"Erro ao enviar email: {e}")


@app.route("/")
def home():
    return redirect(url_for("about"))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/buy", methods=["GET", "POST"])
def buy():
    global email_destiny, name, age
    if request.method == "GET":
        return render_template("buy.html")

    name = request.form.get("name")
    age = request.form.get("age")
    email_destiny = request.form.get("email")

    if not sdk:
        flash("Erro: Mercado Pago não configurado.", "error")
        return redirect(url_for("buy"))

    # cria preferência
    preference_data = {
        "items": [
            {
                "title": "Ingresso Halloween",
                "quantity": 1,
                "unit_price": 45
            }
        ],
        "payer": {"name": name},
        "back_urls": {
            "success": url_for("success", _external=True),
            "failure": url_for("failure", _external=True),
            "pending": url_for("pending", _external=True),
        },
        "auto_return": "approved",
        "notification_url": "https://ingressos-halloween.onrender.com/notificacao"
    }

    pref = sdk.preference().create(preference_data)
    init_point = pref["response"]["init_point"]

    return redirect(init_point)

@app.route("/notificacao", methods=["POST"])
def notificacao():
    data = request.json
    if not data or "data" not in data or "id" not in data["data"]:
        return "Ignorado", 400

    payment_id = data["data"]["id"]
    pagamento = verificar_pagamento(payment_id)

    if pagamento.get("status") == "approved":
        dados = {
        "name": name,
        "email": email_destiny,
        "age": age}

        url_base = "https://ingressos-halloween.onrender.com/ingresso"
        url_com_dados = f"{url_base}?{urlencode(dados)}"
        qr_buffer = gerar_qrcode(url_com_dados)
        enviar_email_com_qrcode(
            destinatario=email_destiny,
            corpo="Segue o QR code para identificação na portaria do evento!",
            qr_buffer = qr_buffer       
        )
        return "Email enviado", 200

    return "Pagamento não aprovado", 200

@app.route("/success")
def success():
    return render_template("success.html", status="Pagamento aprovado 🎉")

@app.route("/ingresso")
def ingresso():
    nome = request.args.get("name")
    email = request.args.get("email")
    data = request.args.get("age")

    if not all([id, nome, email, data]):
        return "Dados incompletos", 400

    return render_template("ingresso.html", name=name, email=email, age=age)

@app.route("/failure")
def failure():
    return render_template("success.html", status="Pagamento não aprovado ❌")


@app.route("/pending")
def pending():
    return render_template("success.html", status="Pagamento pendente ⏳")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
