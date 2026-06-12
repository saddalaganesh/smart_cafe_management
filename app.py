from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask import session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'smartcafe123'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafe.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    price = db.Column(db.Integer)
    description = db.Column(db.String(200))
    image = db.Column(db.String(500))

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    item_name = db.Column(db.String(100))

    price = db.Column(db.Integer)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100))

    items = db.Column(db.String(500))

    total_amount = db.Column(db.Integer)

    order_date = db.Column(db.DateTime, default=datetime.now)

    status = db.Column(db.String(20), default="pending")

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), unique=True)

    password = db.Column(db.String(200))

    role = db.Column(db.String(20))

@app.route("/home")
def home():
    
    if "user" not in session:
        return redirect("/login")
    items = MenuItem.query.all()
    return render_template("index.html", items=items)

@app.route("/add-item", methods=["GET", "POST"])
def add_item():

    if session.get("role") != "admin":
        return redirect("/")

    if request.method == "POST":

        item = MenuItem(
            name=request.form["name"],
            price=request.form["price"],
            description=request.form["description"],
            image=request.form["image"]
        )

        db.session.add(item)
        db.session.commit()

        return redirect("/")

    return render_template("add_item.html")
@app.route("/delete-item/<int:id>")
def delete_item(id):

    if session.get("role") != "admin":
        return redirect("/")

    item = MenuItem.query.get_or_404(id)

    db.session.delete(item)
    db.session.commit()

    return redirect("/")
@app.route("/edit-item/<int:id>", methods=["GET", "POST"])
def edit_item(id):

    if session.get("role") != "admin":
        return redirect("/")

    item = MenuItem.query.get_or_404(id)

    if request.method == "POST":

        item.name = request.form["name"]
        item.price = request.form["price"]
        item.description = request.form["description"]
        item.image = request.form["image"]

        db.session.commit()

        return redirect("/")

    return render_template("edit_item.html", item=item)
@app.route("/add-to-cart/<int:id>")
def add_to_cart(id):

    item = MenuItem.query.get_or_404(id)

    cart_item = CartItem(
        item_name=item.name,
        price=item.price
    )

    db.session.add(cart_item)
    db.session.commit()

    return redirect("/")
@app.route("/cart")
def cart():

    items = CartItem.query.all()

    total = sum(item.price for item in items)

    return render_template(
        "cart.html",
        items=items,
        total=total
    )
@app.route("/remove-from-cart/<int:id>")
def remove_from_cart(id):

    item = CartItem.query.get_or_404(id)

    db.session.delete(item)
    db.session.commit()

    return redirect("/cart")
@app.route("/place-order")
def place_order():

    cart_items = CartItem.query.all()

    total = sum(item.price for item in cart_items)

    item_names = ", ".join(
        item.item_name for item in cart_items
    )

    order = Order(
        username=session.get("user"),
        items=item_names,
        total_amount=total
    )

    db.session.add(order)

    for item in cart_items:
        db.session.delete(item)

    db.session.commit()

    return render_template(
        "order_success.html"
    )
@app.route("/dashboard")
def dashboard():

    if session.get("role") != "admin":
        return redirect("/")

    if "user" not in session:
        return redirect("/login")

    orders = Order.query.all()

    total_orders = len(orders)

    total_revenue = sum(order.total_amount for order in orders)

    total_items = MenuItem.query.count()

    total_customers = User.query.filter_by(role="customer").count()

    return render_template(
        "dashboard.html",
        orders=orders,
        total_orders=total_orders,
        total_revenue=total_revenue,
        total_items=total_items,
        total_customers=total_customers
    )
@app.route("/orders")
def orders():

    if session.get("role") == "admin":

        orders = Order.query.all()

    else:

        orders = Order.query.filter_by(
            username=session["user"]
        ).all()

    return render_template(
        "orders.html",
        orders=orders
    )
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]

        password = generate_password_hash(
            request.form["password"]
        )

        user = User(
            username=username,
            password=password,
            role="customer"
        )

        db.session.add(user)
        db.session.commit()

        return redirect("/login")

    return render_template("register.html")
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]

        password = request.form["password"]

        user = User.query.filter_by(
            username=username
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            session["user"] = username
            session["role"] = user.role

            return redirect("/home")

    return render_template("login.html")
@app.route("/logout")
def logout():

    session.pop("user", None)
    session.pop("role", None)

    return redirect("/")
@app.route("/")
def welcome():

    if "user" in session:
        return redirect("/home")

    return render_template("welcome.html")
@app.route("/update-status/<int:order_id>/<status>")
def update_status(order_id, status):

    if session.get("role") != "admin":
        return redirect("/")

    order = Order.query.get(order_id)

    if order:
        order.status = status
        db.session.commit()

    return redirect("/orders")
if __name__ == "__main__":
    app.run(debug=True)


