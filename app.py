from flask import Flask, render_template, request, redirect, url_for, jsonify
from models import db, Product, Cart
from config import Config
import os
from werkzeug.utils import secure_filename
from flask_cors import CORS

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Enable CORS for cross-origin requests (allows frontend to access backend)
CORS(app, resources={r"/*": {"origins": "*"}})

# Create the database if it doesn't already exist
with app.app_context():
    db.create_all()

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Helper function to check file validity
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

### API Endpoints ###

# Fetch all products (API for frontend)
@app.route('/api/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    product_list = [
        {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "image_url": product.image_url,
            "is_available": product.is_available,
        }
        for product in products
    ]
    return jsonify(product_list)

# Add a product to the cart (API for frontend)
@app.route('/api/cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    product_id = data['product_id']
    quantity = int(data['quantity'])
    
    # Check if the item is already in the cart
    existing_item = Cart.query.filter_by(product_id=product_id).first()
    if existing_item:
        existing_item.quantity += quantity
    else:
        new_cart_item = Cart(product_id=product_id, quantity=quantity)
        db.session.add(new_cart_item)
    db.session.commit()
    return jsonify({"message": "Product added to cart!"})

# Fetch all cart items (API for frontend)
@app.route('/api/cart', methods=['GET'])
def get_cart_items():
    cart_items = Cart.query.all()
    cart_details = [
        {
            "id": item.id,
            "product": {
                "id": item.product_id,
                "name": Product.query.get(item.product_id).name,
                "price": Product.query.get(item.product_id).price,
            },
            "quantity": item.quantity,
        }
        for item in cart_items
    ]
    return jsonify(cart_details)

# Update cart item quantity (API for frontend)
@app.route('/api/cart/<int:cart_item_id>', methods=['PUT'])
def update_cart_item(cart_item_id):
    data = request.get_json()
    new_quantity = int(data['quantity'])
    cart_item = Cart.query.get_or_404(cart_item_id)

    if new_quantity <= 0:
        db.session.delete(cart_item)
    else:
        cart_item.quantity = new_quantity
    db.session.commit()
    return jsonify({"message": "Cart updated!"})

# Remove a cart item (API for frontend)
@app.route('/api/cart/<int:cart_item_id>', methods=['DELETE'])
def remove_cart_item(cart_item_id):
    cart_item = Cart.query.get_or_404(cart_item_id)
    db.session.delete(cart_item)
    db.session.commit()
    return jsonify({"message": "Item removed from cart!"})

### Admin Views (for internal use) ###

@app.route('/admin/inventory')
def admin_inventory():
    products = Product.query.all()
    return render_template('admin/inventory.html', products=products)

@app.route('/admin/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        is_available = 'is_available' in request.form
        image_file = request.files['image']

        # Handle image upload
        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
            image_url = f'static/uploads/{filename}'
        else:
            image_url = ''

        new_product = Product(
            name=name,
            description=description,
            price=price,
            image_url=image_url,
            is_available=is_available
        )
        db.session.add(new_product)
        db.session.commit()
        return redirect(url_for('admin_inventory'))

    return render_template('admin/add_item.html')

@app.route('/admin/delete/<int:product_id>')
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('admin_inventory'))

@app.route('/admin/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        product.name = request.form['name']
        product.description = request.form['description']
        product.price = float(request.form['price'])
        product.is_available = 'is_available' in request.form
        image_file = request.files['image']

        # Handle image upload if provided
        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
            product.image_url = f'static/uploads/{filename}'
        
        db.session.commit()
        return redirect(url_for('admin_inventory'))

    return render_template('admin/edit_item.html', product=product)

if __name__ == '__main__':
    app.run()
