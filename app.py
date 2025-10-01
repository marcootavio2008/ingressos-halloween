import os
from flask import Flask, render_template, request, redirect, url_for, flash
import mercadopago

app = Flask(__name__)
app.secret_key = 'cx1228@'  # necessário para flash messages

# coloque seu access token (sandbox ou produção) no ambiente
MERCADO_TOKEN = "APP_USR-8965396489010178-100118-88682f7280895d5fc63c4ad811f40428-2726179168"
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

    # POST → dados do formulário
    name = request.form.get("name")
    age = request.form.get("age")
    ticket_type = request.form.get("ticket_type", "comum")

    if not sdk:
        flash("Erro: Mercado Pago não configurado.", "error")
        return redirect(url_for("buy"))

    # cria preferência
    preference_data = {
        "items": [
            {
                "title": f"Ingresso {ticket_type.upper()}",
                "quantity": 1,
                "unit_price": 47.5
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
    init_point = pref["init_point"]

    return redirect(init_point)


@app.route("/success")
def success():
    return render_template("success.html", status="Pagamento aprovado 🎉")


@app.route("/failure")
def failure():
    return render_template("success.html", status="Pagamento não aprovado ❌")


@app.route("/pending")
def pending():
    return render_template("success.html", status="Pagamento pendente ⏳")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
