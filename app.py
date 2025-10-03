import io
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response
import mercadopago
import qrcode

app = Flask(__name__)
app.secret_key = 'cx1228@'  # necessário para flash messages

# Mercado Pago SDK
MERCADO_TOKEN = "APP_USR-4269419174287132-100118-d5000064cd6d942fc03f594ab2d77212-50261275"
sdk = mercadopago.SDK(MERCADO_TOKEN)

# Banco de ingressos em memória
tickets = {}


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

    if not name or not age:
        flash("Nome e idade são obrigatórios!", "error")
        return redirect(url_for("buy"))

    ticket_id = str(uuid.uuid4())
    tickets[ticket_id] = {"nome": name, "idade": age, "status": "aguardando"}

    # cria preferência Mercado Pago
    preference_data = {
    "items": [
        {"title": "Ingresso Baile Halloween 🎃", 
         "quantity": 1, 
         "unit_price": 5.0}],
        
    "payer": {"name": name},
        
    "external_reference": ticket_id,  # <<< adiciona aqui
        
    "back_urls": {
        "success": url_for("success", _external=True),
        "failure": url_for("failure", _external=True),
        "pending": url_for("pending", _external=True)
    },
    "auto_return": "approved"
}


    pref = sdk.preference().create(preference_data)
    init_point = pref["response"]["init_point"]

    return redirect(init_point)


# Webhook Mercado Pago
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("Webhook recebido:", data)

    if "data" in data and "id" in data["data"]:
        payment_id = data["data"]["id"]
        payment = sdk.payment().get(payment_id)

        if payment and payment["response"]["status"] == "approved":
            # Atualiza ingresso como pago
            for t_id, info in tickets.items():
                if info["status"] == "aguardando":
                    tickets[t_id]["status"] = "pago"
                    print("Ingresso confirmado:", t_id)

    return jsonify({"status": "ok"})

@app.route("/success")
def success():
    # Mercado Pago adiciona 'external_reference' na URL
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
