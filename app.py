from flask import Flask, render_template, request, redirect, url_for
from models import db, Product, Cart
from config import Config
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    db.create_all()

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/')
def browse_products():
    products = Product.query.all()
    print(products)
    return render_template('Client/browse.html', products=products)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if request.method == 'POST':
        product_id = request.form['product_id']
        quantity = int(request.form['quantity'])
        existing_item = Cart.query.filter_by(product_id=product_id).first()
        if existing_item:
            existing_item.quantity += quantity
        else:
            cart_item = Cart(product_id=product_id, quantity=quantity)
            db.session.add(cart_item)
        db.session.commit()
        return redirect(url_for('cart'))
    cart_items = Cart.query.all()
    cart_details = [
        {
            "id": item.id,
            "product": Product.query.get(item.product_id),
            "quantity": item.quantity,
        }
        for item in cart_items
    ]
    return render_template('Client/cart.html', cart_items=cart_details)

@app.route('/update_cart/<int:cart_item_id>', methods=['POST'])
def update_cart(cart_item_id):
    cart_item = Cart.query.get_or_404(cart_item_id)
    new_quantity = int(request.form['quantity'])
    if new_quantity <= 0:
        db.session.delete(cart_item)
    else:
        cart_item.quantity = new_quantity
    db.session.commit()
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<int:cart_item_id>', methods=['POST'])
def remove_from_cart(cart_item_id):
    cart_item = Cart.query.get_or_404(cart_item_id)
    db.session.delete(cart_item)
    db.session.commit()
    return redirect(url_for('cart'))

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
