import os
from flask import Flask, render_template, request, redirect, url_for, flash
import mercadopago
import uuid
import qrcode

app = Flask(__name__)
app.secret_key = 'cx1228@'  # necessário para flash messages

# coloque seu access token (sandbox ou produção) no ambiente
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

    # POST → dados do formulário
    name = request.form.get("name")
    age = request.form.get("age")

    ticket_id = str(uuid.uuid4())
    tickets[ticket_id] = {"nome": name, "idade": age, "status": "aguardando"}

    if not sdk:
        flash("Erro: Mercado Pago não configurado.", "error")
        return redirect(url_for("buy"))

    # cria preferência
    preference_data = {
        "items": [
            {
                "title": "Ingresso",
                "quantity": 1,
                "unit_price": 5
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
    
@app.route("/notificacao", methods=["POST"])
def notificacao():
    data = request.get_json()
    print("Webhook recebido:", data)

    if "data" in data and "id" in data["data"]:
        payment_id = data["data"]["id"]
        payment = sdk.payment().get(payment_id)

        if payment and payment["response"]["status"] == "approved":
            # Atualiza ticket como pago
            # Aqui seria melhor associar com "external_reference"
            for t_id, info in tickets.items():
                if info["status"] == "aguardando":
                    tickets[t_id]["status"] = "pago"
                    print("Ingresso confirmado:", t_id)

    return jsonify({"status": "ok"})


@app.route("/success")
def success():
    return render_template(url_for("success", ticket_id=ticket_id))

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

@app.route("/validar/<ticket_id>")
def validar(ticket_id):
    if ticket_id in tickets:
        t = tickets[ticket_id]
        return f"""
        <h2>🎟️ Ingresso válido</h2>
        <p><b>Nome:</b> {t['nome']}</p>
        <p><b>Idade:</b> {t['idade']}</p>
        <p><b>Status:</b> {t['status']}</p>
        """
    return "Ingresso INVÁLIDO ❌", 404


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
