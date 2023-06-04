import json
import jwt
from flask import Flask, request, jsonify

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
USERS_FILE = 'users.json'
CART_FILE = 'cart.json'
PRODUCTS_FILE = 'products.json'
COUPONS_FILE = 'coupons.json'

# Load user data from JSON file
def load_users():
    with open(USERS_FILE) as file:
        data = json.load(file)
    return data

# Load cart data from JSON file
def load_cart_data():
    with open(CART_FILE) as file:
        data = json.load(file)
    return data

# Update cart data in JSON file
def update_cart_data(cart_data):
    with open(CART_FILE, 'w') as file:
        json.dump(cart_data, file, indent=4)

# Load product data from JSON file
def load_product_data():
    with open(PRODUCTS_FILE) as file:
        data = json.load(file)
    return data

# Load coupon data from JSON file
def load_coupons():
    with open(COUPONS_FILE) as file:
        data = json.load(file)
    return data

# Validate user credentials
def authenticate(username, password):
    users = load_users()
    if username in users and password == users[username]['password']:
        return True
    return False

# JWT token required decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            user_id = data['user_id']
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(user_id, *args, **kwargs)
    return decorated

# Login route
@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    if authenticate(username, password):
        token = jwt.encode({'user_id': username}, app.config['SECRET_KEY'])
        return jsonify({'token': token.decode('utf-8')}), 200
    return jsonify({'message': 'Invalid username or password!'}), 401

# Create - Add a new product into the cart
@app.route('/cart/<user_id>/items', methods=['POST'])
@token_required
def create_item(user_id):
    cart_data = load_cart_data()
    product_id = request.json.get('product_id')
    quantity = request.json.get('quantity')

    products = load_product_data()
    if product_id in products:
        product = products[product_id]
        item = {
            'product_id': product_id,
            'image': product['image'],
            'name': product['name'],
            'price': product['price'],
            'quantity': quantity
        }
        cart_data.setdefault(user_id, []).append(item)
        update_cart_data(cart_data)
        return jsonify({'message': 'Item added to cart successfully'}), 201
    return jsonify({'message': 'Product not found'}), 404

# Update - Update quantity for the added product
@app.route('/cart/<user_id>/items/<product_id>', methods=['PUT'])
@token_required
def update_item(user_id, product_id):
    cart_data = load_cart_data()
    if user_id in cart_data and product_id in cart_data[user_id]:
        quantity = request.json.get('quantity')
        cart_data[user_id][product_id]['quantity'] = quantity
        update_cart_data(cart_data)
        return jsonify({'message': 'Item quantity updated successfully'}), 200
    return jsonify({'message': 'Item not found'}), 404

# Delete - Delete a product from the cart
@app.route('/cart/<user_id>/items/<product_id>', methods=['DELETE'])
@token_required
def delete_item(user_id, product_id):
    cart_data = load_cart_data()
    if user_id in cart_data and product_id in cart_data[user_id]:
        del cart_data[user_id][product_id]
        update_cart_data(cart_data)
        return jsonify({'message': 'Item deleted successfully'}), 200
    return jsonify({'message': 'Item not found'}), 404

# Read - Get the aggregated cart information with the list of added products
@app.route('/cart/<user_id>', methods=['GET'])
@token_required
def get_cart(user_id):
    cart_data = load_cart_data()
    if user_id in cart_data:
        cart_items = cart_data[user_id]
        total_price = 0
        total_quantity = 0
        products = load_product_data()
        for item in cart_items:
            item['image'] = None  # Exclude image buffer from response
            total_price += item['price'] * item['quantity']
            total_quantity += item['quantity']
        return jsonify({
            'items': cart_items,
            'total_price': total_price,
            'total_quantity': total_quantity
        }), 200
    return jsonify({'message': 'Cart not found'}), 404

# Bonus - Apply coupon code and calculate discounted price
@app.route('/cart/<user_id>/apply-coupon', methods=['POST'])
@token_required
def apply_coupon(user_id):
    cart_data = load_cart_data()
    if user_id in cart_data:
        coupon_code = request.json.get('coupon_code')
        coupons = load_coupons()
        if coupon_code in coupons:
            coupon = coupons[coupon_code]
            discount_percent = coupon['discount_percent']
            cart_items = cart_data[user_id]
            total_price = 0
            for item in cart_items:
                total_price += item['price'] * item['quantity']
            discounted_price = total_price - (total_price * discount_percent / 100)
            return jsonify({'discounted_price': discounted_price}), 200
        return jsonify({'message': 'Invalid coupon code'}), 404
    return jsonify({'message': 'Cart not found'}), 404

# Run the app
if __name__ == '__main__':
    app.run()
