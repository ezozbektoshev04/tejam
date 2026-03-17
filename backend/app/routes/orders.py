from flask import Blueprint, request, jsonify
from app import db
from app.models import Order, Bag, Notification, User
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.services.notifications import send_order_notification

orders_bp = Blueprint('orders', __name__)

# ── Place an order (customer only) ────────────────────
@orders_bp.route('/', methods=['POST'])
@jwt_required()
def place_order():
    identity = get_jwt_identity()
    claims = get_jwt()

    if claims['role'] != 'customer':
        return jsonify({'error': 'Only customers can place orders'}), 403

    data = request.get_json()
    if not data.get('bag_id'):
        return jsonify({'error': 'bag_id is required'}), 400

    bag = Bag.query.get_or_404(data['bag_id'])

    if not bag.is_available or bag.quantity < 1:
        return jsonify({'error': 'This bag is no longer available'}), 400

    # Reduce quantity
    bag.quantity -= 1
    if bag.quantity == 0:
        bag.is_available = False

    order = Order(
        customer_id=int(identity),
        bag_id=bag.id,
        total_price=bag.price,
        status='pending'
    )
    db.session.add(order)

    # Notify customer
    notif = Notification(
        user_id=int(identity),
        message=f'Your order for "{bag.title}" from {bag.store.name} is confirmed! Pickup: {bag.pickup_start} - {bag.pickup_end}'
    )
    db.session.add(notif)

    # Notify business owner
    owner_notif = Notification(
        user_id=bag.store.owner_id,
        message=f'New order received for "{bag.title}"!'
    )
    db.session.add(owner_notif)

    db.session.commit()

    # Send email notification
    customer = User.query.get(int(identity))
    send_order_notification(customer.email, bag.title, bag.store.name, str(bag.pickup_start), str(bag.pickup_end))

    return jsonify({
        'message': 'Order placed successfully',
        'order_id': order.id,
        'total_price': order.total_price,
        'status': order.status
    }), 201


# ── Get my orders (customer) ──────────────────────────
@orders_bp.route('/my', methods=['GET'])
@jwt_required()
def my_orders():
    identity = get_jwt_identity()

    orders = Order.query.filter_by(customer_id=int(identity)).order_by(Order.created_at.desc()).all()

    return jsonify([{
        'id': o.id,
        'status': o.status,
        'total_price': o.total_price,
        'created_at': o.created_at.isoformat(),
        'bag': {
            'id': o.bag.id,
            'title': o.bag.title,
            'pickup_start': str(o.bag.pickup_start),
            'pickup_end': str(o.bag.pickup_end),
            'store': {
                'name': o.bag.store.name,
                'address': o.bag.store.address,
                'district': o.bag.store.district
            }
        }
    } for o in orders]), 200


# ── Get store orders (business owner) ─────────────────
@orders_bp.route('/store/<int:store_id>', methods=['GET'])
@jwt_required()
def store_orders(store_id):
    identity = get_jwt_identity()
    claims = get_jwt()

    from app.models import Store
    store = Store.query.get_or_404(store_id)

    if store.owner_id != int(identity) and claims['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    orders = Order.query.join(Bag).filter(Bag.store_id == store_id).order_by(Order.created_at.desc()).all()

    return jsonify([{
        'id': o.id,
        'status': o.status,
        'total_price': o.total_price,
        'created_at': o.created_at.isoformat(),
        'customer': {
            'id': o.customer.id,
            'name': o.customer.name,
            'email': o.customer.email
        },
        'bag': {
            'id': o.bag.id,
            'title': o.bag.title
        }
    } for o in orders]), 200


# ── Update order status (business owner) ──────────────
@orders_bp.route('/<int:order_id>/status', methods=['PUT'])
@jwt_required()
def update_order_status(order_id):
    identity = get_jwt_identity()
    claims = get_jwt()

    order = Order.query.get_or_404(order_id)

    if order.bag.store.owner_id != int(identity) and claims['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    valid_statuses = ['pending', 'confirmed', 'picked_up', 'cancelled']
    if data.get('status') not in valid_statuses:
        return jsonify({'error': f'Status must be one of {valid_statuses}'}), 400

    order.status = data['status']

    # Notify customer of status change
    notif = Notification(
        user_id=order.customer_id,
        message=f'Your order #{order.id} status has been updated to: {order.status}'
    )
    db.session.add(notif)
    db.session.commit()

    return jsonify({'message': 'Order status updated', 'status': order.status}), 200


# ── Get my notifications ──────────────────────────────
@orders_bp.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    identity = get_jwt_identity()

    notifs = Notification.query.filter_by(
        user_id=int(identity)
    ).order_by(Notification.created_at.desc()).all()

    return jsonify([{
        'id': n.id,
        'message': n.message,
        'is_read': n.is_read,
        'created_at': n.created_at.isoformat()
    } for n in notifs]), 200


# ── Mark notification as read ─────────────────────────
@orders_bp.route('/notifications/<int:notif_id>/read', methods=['PUT'])
@jwt_required()
def mark_read(notif_id):
    identity = get_jwt_identity()
    notif = Notification.query.get_or_404(notif_id)

    if notif.user_id != int(identity):
        return jsonify({'error': 'Unauthorized'}), 403

    notif.is_read = True
    db.session.commit()
    return jsonify({'message': 'Notification marked as read'}), 200