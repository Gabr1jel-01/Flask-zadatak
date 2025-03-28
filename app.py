from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flasgger import Swagger

app = Flask(__name__)
swagger = Swagger(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
db = SQLAlchemy(app)


#region CLASSES
class Users(db.Model):
    id = db.Column(db.Integer, primary_key= True, autoincrement=True) #id je primary key jer sam postabvio true
    first_name = db.Column(db.String(80), unique = False, nullable = False) #unique flase zato sto mogu imati vise istih imena, nullable da nije nula
    last_name = db.Column(db.String(80), unique = False, nullable = False)
    age = db.Column(db.Integer)
    time_of_creation = db.Column(db.DateTime, default=datetime.now)
    account_balance = db.Column(db.Float, nullable=False, default=1000.0)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def __repr__(self): #sa selfom mogu u ovoj funkciji dohvatiti atribute objekta
        return f"Ime i prezime: {self.first_name} {self.last_name} \n Dob: {self.age} \n Sign-up napravljen: {self.time_of_creation}"

class Categories(db.Model):
    id = db.Column(db.Integer, primary_key= True) #id je primary key jer sam postabvio true
    type_of_category = db.Column(db.String(80), unique = False, nullable = False)
    time_of_creation = db.Column(db.DateTime, default=datetime.now())

    expenses = db.relationship("Expenses", backref="category", lazy=True,cascade="all, delete")

    def __repr__(self):
        return f"Tip kategorije: {self.type_of_category} \n Kategorija dodana: {self.time_of_creation}"

class Expenses(db.Model):
    id = db.Column(db.Integer, primary_key= True) #id je primary key jer sam postabvio true
    payed_with = db.Column(db.String(80), unique = False, nullable = False)
    time_of_creation = db.Column(db.DateTime, default=datetime.now)
    amount = db.Column(db.Integer, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)

    def __repr__(self):
        return f"Nacin placanja: {self.payed_with} \n Vrijeme placanja: {self.time_of_creation}"
#endregion

#region API ENDPOINT
@app.route("/")
def route():

    """
    Welcome endpoint
    ---
    tags:
      - System
    responses:
      200:
        description: Welcome message
    """

    return("<h1>Welcome to my simple REST API !!!</h1>")

# get all categories route
@app.route("/categories")
def get_all_categories():

    """
    Get all categories
    ---
    tags:
      - Categories
    responses:
      200:
        description: List of categories
    """

    categories = Categories.query.all()
    
    output_list=[]
    
    for category in categories:
        category_data = {"type of category": category.type_of_category}
        output_list.append(category_data)

    return {"Categories": output_list}

#get all expenses route
@app.route("/expenses")
def get_all_expenses():
    """
    Get all expenses
    ---
    tags:
      - Expenses
    responses:
      200:
        description: List of expenses
    """

    expenses = Expenses.query.all()
    
    output_list=[]
    
    for expense in expenses:
        expense_data = {"payed with": expense.payed_with,
                        "category_id": expense.category_id }
        output_list.append(expense_data)

    return {"Expenses": output_list}

#get all users route
@app.route("/users")
def get_all_users():

    """
    Get all users
    ---
    tags:
      - Users
    responses:
      200:
        description: List of users
    """

    users = Users.query.all()
    
    output_list=[]
    
    for user in users:
        users_data = {"first_name": user.first_name,
                        "last_name": user.last_name,
                        "age": user.age,
                        "account_balance": user.account_balance,
                        "email": user.email}
        output_list.append(users_data)

    return {"Users": output_list}

#add new category route
@app.route("/categories", methods=["POST"])
def add_category():
    """
    Add new category
    ---
    tags:
      - Categories
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            type_of_category:
              type: string
              example: Food
    responses:
      201:
        description: Category successfully added
    """
    
    with app.app_context():
        category = Categories(type_of_category=request.json["type_of_category"])
        db.session.add(category)
        db.session.commit()
        return ("Category succesfully added!")

#add new expense route
@app.route("/expenses", methods=["POST"])
def add_expense():


    """
    Add new expense
    ---
    tags:
      - Expenses
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            payed_with:
              type: string
              example: Card
            category:
              type: string
              example: Food
            amount:
              type: integer
              example: 100
    responses:
      201:
        description: Expense added successfully
      400:
        description: Missing required fields
    """
    
    data = request.get_json()

   
    if not data or "payed_with" not in data or "category" not in data or "amount" not in data:
        return jsonify({"error": "Missing 'payed_with' or 'category' or 'amount'"}), 400

    category = Categories.query.filter_by(type_of_category=data["category"]).first()

    if not category:
        return jsonify({"error": f"Category '{data['category']}' not found"}), 404
    
    new_expense = Expenses(
        payed_with=data["payed_with"],
        category_id=category.id,
        amount=data["amount"]
    )

    db.session.add(new_expense)
    db.session.commit()

    return jsonify({
        "message": "Expense added successfully",
        "expense": {
            "payed_with": new_expense.payed_with,
            "category": category.type_of_category,
            "amount": new_expense.amount
        }
    }), 201

#update a category route
@app.route("/categories/<id>", methods=["PATCH"])
def patch_category(id):
    """
    Update a category
    ---
    tags:
      - Categories
    parameters:
      - name: id
        in: path
        required: true
        type: integer
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            type_of_category:
              type: string
              example: Utilities
    responses:
      200:
        description: Category updated successfully
      404:
        description: Category not found
    """
    category = Categories.query.get_or_404(id)
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400
    if "type_of_category" in data:
        category.type_of_category = data["type_of_category"]

    db.session.commit()

    return jsonify({
        "message": "Category updated",
        "category": {
            "type_of_category": category.type_of_category,
        }
    }), 200

#update expense route
@app.route("/expenses/<id>", methods=["PATCH"])
def patch_expense(id):


    """
    Update an expense
    ---
    tags:
      - Expenses
    parameters:
      - name: id
        in: path
        required: true
        type: integer
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            payed_with:
              type: string
              example: Cash
            amount:
              type: integer
              example: 120
            category:
              type: string
              example: Food
    responses:
      200:
        description: Expense updated successfully
      400:
        description: Invalid input
      404:
        description: Expense or category not found
    """
    expense = Expenses.query.get_or_404(id)
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400
    if "payed_with" in data:
        expense.payed_with = data["payed_with"]
    if "amount" in data:
        expense.amount=data["amount"]
    db.session.commit()

    return jsonify({
        "message": "Expense updated",
        "Expense": {
            "payed_with": expense.payed_with,
            "amount": expense.amount
        }
    }), 200

#delete category route
@app.route("/categories/<id>", methods=["DELETE"])
def delete_category(id):
    """
    Delete a category
    ---
    tags:
      - Categories
    parameters:
      - name: id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Category successfully deleted
    """
    category = Categories.query.get(id)
    if category is None:
        return {"error": "category not found"}
    db.session.delete(category)
    db.session.commit()
    return {"message":"category successfully deleted"}

#delete expense route
@app.route("/expenses/<id>", methods=["DELETE"])
def delete_expense(id):
    """
    Delete an expense
    ---
    tags:
      - Expenses
    parameters:
      - name: id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Expense successfully deleted
    """
    expense = Categories.query.get(id)
    if expense is None:
        return {"error": "expense not found"}
    db.session.delete(expense)
    db.session.commit()
    return {"message":"expense successfully deleted"}

#get expenses by filters route
@app.route("/expenses/filter", methods=["GET"])
def filter_expenses():

    """
    Filter expenses by category, amount and date
    ---
    tags:
      - Expenses
    parameters:
      - name: category
        in: query
        type: string
      - name: amount_min
        in: query
        type: integer
      - name: amount_max
        in: query
        type: integer
      - name: date_from
        in: query
        type: string
        example: 01-01-2024
      - name: date_to
        in: query
        type: string
        example: 01-03-2024
    responses:
      200:
        description: Filtered expenses
    """
    query = Expenses.query

    category_name = request.args.get("category")
    amount_min = request.args.get("amount_min", type=int)
    amount_max = request.args.get("amount_max", type=int)
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")


    if category_name:
        category = Categories.query.filter_by(type_of_category=category_name).first()
        if category:
            query = query.filter(Expenses.category_id == category.id)
        else:
            return jsonify({"error": f"Category '{category_name}' not found"}), 404
        
    if amount_min is not None:
        query = query.filter(Expenses.amount >= amount_min)
    if amount_max is not None:
        query = query.filter(Expenses.amount <= amount_max)

    if date_from:
        try:
            date_from_parsed = datetime.strptime(date_from, "%d-%m-%Y")
            query = query.filter(Expenses.time_of_creation >= date_from_parsed)
        except ValueError:
            return jsonify({"error": "Invalid date_from format."}), 400

    if date_to:
        try:
            date_to_parsed = datetime.strptime(date_to, "%d-%m-%Y")
            query = query.filter(Expenses.time_of_creation <= date_to_parsed)
        except ValueError:
            return jsonify({"error": "Invalid date_to format."}), 400
        

    expenses = query.all()

    result = []
    for expense in expenses:
        result.append({
            "id": expense.id,
            "payed_with": expense.payed_with,
            "amount": expense.amount,
            "time_of_creation": expense.time_of_creation,
            "category": expense.category.type_of_category
        })

    return jsonify(result), 200

#get a sum of all expenses by categories route
@app.route("/expenses/category-totals", methods=["GET"])
def total_spent_by_category():
    """
    Total amount spent per category
    ---
    tags:
      - Expenses
    responses:
      200:
        description: Total expenses by category
    """
    results = db.session.query(
        Categories.type_of_category,
        func.sum(Expenses.amount)
    ).join(Categories.expenses).group_by(Categories.id).all()

    totals = {
        category: int(amount or 0) for category, amount in results
    }

    return jsonify(totals), 200

#register user route
@app.route("/register", methods=["POST"])
def register_user():
    """
    Register a new user
    ---
    tags:
      - Users
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            first_name:
              type: string
              example: Ivan
            last_name:
              type: string
              example: Ivić
            age:
              type: integer
              example: 25
            email:
              type: string
              example: ivan@example.com
            password:
              type: string
              example: tajna123
    responses:
      201:
        description: User registered successfully
      400:
        description: Email and Password are required or user already exists
    """


    data = request.get_json()
    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email and Password are required"}),400
    if Users.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "User already exists"})
    
    hashed_pwd = generate_password_hash(data["password"])

    new_user = Users(
        first_name=data.get("first_name", ""),
        last_name = data.get("last_name", ""),
        age= data.get("age", None),
        email= data["email"],
        password= hashed_pwd)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "Registration was successfull!"})

#login user route
@app.route("/login", methods=["POST"])
def login_user():

    """
    User login
    ---
    tags:
      - Users
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              example: ivan@example.com
            password:
              type: string
              example: tajna123
    responses:
      200:
        description: Successful login
      400:
        description: Missing email or password
      401:
        description: Wrong email or password
    """

    data = request.get_json()

    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email and Password are required"}),400

    user = Users.query.filter_by(email=data["email"]).first()

    if not user or not check_password_hash(user.password, data["password"]):
        return jsonify({"error": "Wrong email or password"})
    
    return jsonify({"message": f"Welcome {user.first_name}"})

#endregion