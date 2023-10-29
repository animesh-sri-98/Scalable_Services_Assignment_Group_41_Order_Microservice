from flask import Flask, request, jsonify, render_template
import random
from pymongo import MongoClient
import requests
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG) 
print("connecting to mongodb server")
client = MongoClient("mongodb://mongodb-service:27017/")
db = client["orders_db"]
collection = db["orders"]

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    user_id = data.get('user_id')
    product_id = data.get('product_id')  # Added product_id from request data
    # Generate a random 3-digit order_id
    order_id = random.randint(100, 999)
    order_data = {
        "order_id": order_id,
        "user_id": user_id,
        "product_id": product_id,  # Added product_id to order_data
        "status": "created"
    }
    collection.insert_one(order_data)

    response = {
        "message": "Order created successfully",
        "order_id": order_id
    }
    return jsonify(response), 201

@app.route('/orders', methods=['GET'])
def get_all_orders():
    orders = list(collection.find())
    response = []
    for order in orders:
        response.append({
            "order_id": order["order_id"],
            "user_id": order["user_id"],
            "product_id": order["product_id"],
            "status": order["status"]
        })
    return jsonify(response), 200

from flask import jsonify

@app.route('/orders/<int:order_id>', methods=['GET'])
def get_order_by_order_id(order_id):
    # Retrieve orders based on order_id from MongoDB
    order = collection.find_one({"order_id": order_id})

    if order:
        response = {
            "order_id": order["order_id"],
            "user_id": order["user_id"],
            "product_id": order["product_id"],  # Assuming product_id is a key in your MongoDB document
            "status": order["status"]
        }
        return jsonify(response), 200
    else:
        # Orders not found, return 404 response
        return jsonify({"message": "Order not found"}), 404




@app.route('/orders/<int:user_id>', methods=['GET'])
def get_order(user_id):
    # Retrieve orders based on user_id from MongoDB
    orders = list(collection.find({"user_id": user_id}))

    if orders:
        response = []
        for order in orders:
            response.append({
                "order_id": order["order_id"],
                "user_id": order["user_id"],
                "product_id": order["product_id"],  # Added product_id to the response
                "status": order["status"]
            })
        return jsonify(response), 200
    else:
        # Orders not found, return 404 response
        return jsonify({"message": "Orders not found"}), 404
    
@app.route('/orders/<int:order_id>/status', methods=['GET'])
def get_order_status(order_id):
    order = collection.find_one({"order_id": order_id})
    if order:
        return jsonify({"status": order["status"]}), 200
    else:
        return jsonify({"message": "Order not found"}), 404

    
@app.route('/orders/<int:order_id>', methods=['PUT'])
def update_order_status(order_id):
    data = request.get_json()
    new_status = data.get('status')
    result = collection.update_one({"order_id": order_id}, {"$set": {"status": new_status}})
    
    if result.modified_count > 0:
        return jsonify({"message": "Order status updated successfully"}), 200
    else:
        return jsonify({"message": "Order not found"}), 404



@app.route('/orders/<int:user_id>', methods=['DELETE'])
def delete_order(user_id):
    # Delete orders based on user_id from MongoDB
    result = collection.delete_many({"user_id": user_id})

    if result.deleted_count > 0:
        return jsonify({"message": "Orders deleted successfully"}), 200
    else:
        # Orders not found, return 404 response
        return jsonify({"message": "Orders not found"}), 404


@app.route('/orders/<int:order_id>/products', methods=['GET'])
def get_product_details_from_order(order_id):
    order = collection.find_one({"order_id": order_id})

    if order:
        product_id = order["product_id"]
        product_url = f'http://product-microservice:80/products/{product_id}'

        try:
            product_response = requests.get(product_url, timeout=5)
            product_response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
            return jsonify(product_response.json()), 200
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching product from {product_url}: {e}")
            return jsonify({"message": "Error fetching product"}), 500
    else:
        return jsonify({"message": "Order not found"}), 404
    
@app.route('/orders/<int:order_id>/users', methods=['GET'])
def get_user_details_from_order(order_id):
    order = collection.find_one({"order_id": order_id})

    if order:
        user_id = order["user_id"]
        user_url = f'http://user-microservice:80/users/{user_id}'

        try:
            user_response = requests.get(user_url, timeout=5)
            user_response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
            return jsonify(user_response.json()), 200
        except requests.exceptions.RequestException as e:
            return jsonify({"message": "Error fetching user details"}), 500
    else:
        return jsonify({"message": "No user found"}), 404
    
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9997)
