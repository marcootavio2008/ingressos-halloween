import io
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response
import mercadopago
import qrcode
import smtplib
from email.message import EmailMessage

app = Flask(__name__)
app.secret_key = 'cx1228@'

# Mercado Pago
MERCADO_TOKEN = "APP_USR-4269419174287132-100118-d5000064cd6d942fc03f594ab2d77212-50261275"
sdk = mercadopago.SDK(MERCADO_TOKEN)

# Banco de ingressos em memória
tickets = {}

# Configuração do email
EMAIL_FROM = 'seuemail@dominio.com'
EMAIL_PASS = 'SENHA_DO_EMAIL'
SMTP_SERVER = 'smtp.dominio.com'
SMTP_PORT = 465


@app.route("/")
def home():
    return redirect(url_for("about"))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/buy", methods=["GET", "POST"])
def buy():
    if request.method == "GET":
        return render_template("buy.html")

    name = request.form.get("name")
    age = request.form.get("age")
    email = request.form.get("email")

    if not name or not age or not email:
        flash("Nome, idade e email são obrigatórios!", "error")
        return redirect(url_for("buy"))

    ticket_id = str(uuid.uuid4())
    tickets[ticket_id] = {"nome": name, "idade": age, "status": "aguardando", "email": email}

    preference_data = {
        "items": [{"title": "Ingresso Baile Halloween 🎃", 
                   "quantity": 1, 
                   "unit_price": 5.0}],
        "payer": {"name": name, "email": email},
        "external_reference": ticket_id,
        "back_urls": {
            "success": url_for("success", _external=True),
            "failure": url_for("failure", _external=True),
            "pending": url_for("pending", _external=True)
        },
        "auto_return": "approved",
    }

    pref = sdk.preference().create(preference_data)
    return redirect(pref["response"]["init_point"])


# Webhook do Mercado Pago
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if "data" in data and "id" in data["data"]:
        payment_id = data["data"]["id"]
        payment = sdk.payment().get(payment_id)
        if payment and payment["response"]["status"] == "approved":
            ticket_id = payment["response"].get("external_reference")
            if ticket_id in tickets:
                tickets[ticket_id]["status"] = "pago"
                enviar_email_qrcode(tickets[ticket_id]['email'], ticket_id)
    return jsonify({"status": "ok"})


@app.route("/success")
def success():
    ticket_id = request.args.get("external_reference")
    if not ticket_id or ticket_id not in tickets:
        return "Ingresso inválido ❌", 404
    return redirect(url_for("ingresso", ticket_id=ticket_id))


@app.route("/failure")
def failure():
    return render_template("success.html", status="Pagamento não aprovado ❌")


@app.route("/pending")
def pending():
    return render_template("success.html", status="Pagamento pendente ⏳")


@app.route("/ingresso/<ticket_id>")
def ingresso(ticket_id):
    if ticket_id not in tickets:
        return "Ingresso inválido ❌", 404
    ticket = tickets[ticket_id]
    return render_template("ticket.html", ticket=ticket, ticket_id=ticket_id)


@app.route("/qrcode/<ticket_id>")
def qrcode_img(ticket_id):
    if ticket_id not in tickets:
        return "Ingresso inválido ❌", 404
    url = url_for("ingresso", ticket_id=ticket_id, _external=True)
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return Response(buf, mimetype="image/png")


def gerar_qrcode(ticket_id):
    url = f"https://ingressos-halloween.onrender.com/ingresso/{ticket_id}"
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def enviar_email_qrcode(email_destino, ticket_id):
    buf = gerar_qrcode(ticket_id)
    msg = EmailMessage()
    msg['Subject'] = 'Seu ingresso para o Baile de Halloween 🎃'
    msg['From'] = EMAIL_FROM
    msg['To'] = email_destino
    msg.set_content('Segue seu ingresso com QR Code. Mostre no dia do evento!')

    msg.add_attachment(buf.read(), maintype='image', subtype='png', filename='qrcode.png')

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.login(EMAIL_FROM, EMAIL_PASS)
        smtp.send_message(msg)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
