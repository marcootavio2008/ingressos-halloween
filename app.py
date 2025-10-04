import os
from flask import Flask, render_template, request, redirect, url_for, flash
import mercadopago
import smtplib
import email.message

app = Flask(__name__)
app.secret_key = 'cx1228@'

MERCADO_TOKEN = "APP_USR-4269419174287132-100118-d5000064cd6d942fc03f594ab2d77212-50261275"
sdk = mercadopago.SDK(MERCADO_TOKEN)

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

    if not sdk:
        flash("Erro: Mercado Pago não configurado.", "error")
        return redirect(url_for("buy"))

    # cria preferência
    preference_data = {
        "items": [
            {
                "title": "Ingresso",
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
    }

    pref = sdk.preference().create(preference_data)
    init_point = pref["response"]["init_point"]

    return redirect(init_point)


@app.route("/success")
def success():
    return render_template("success.html", status="Pagamento aprovado 🎉")
    msg = email.message.Message()
    msg['Subject'] = 'Ingresso Halloween'
    msg['From'] = 'acfantasy3@gmail.com'
    for nome, email_pessoa in emails.items():
        if pessoa.lower().strip() in nome.lower():
            msg['To'] = email
            password = 'hkcaouharwcfxpyj'
            msg.add_header('Content-Type', 'text/html')
            msg.set_payload("Segue o QR code para apresentar na portaria do evnto")
            with open('frame.png', 'rb') as fp:
                img_data = fp.read()
            msg.add_attachment(img_data, maintype='image', subtype='png', filename='frame.png')
            s = smtplib.SMTP('smtp.gmail.com: 587')
            s.starttls()
            s.login(msg['From'], password)
            s.sendmail(msg['From'], [msg['To']], msg.as_string().encode('utf-8'))
            


@app.route("/failure")
def failure():
    return render_template("success.html", status="Pagamento não aprovado ❌")


@app.route("/pending")
def pending():
    return render_template("success.html", status="Pagamento pendente ⏳")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
