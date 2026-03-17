from flask import Blueprint, request, jsonify
from app import db
from app.models import User, Store, Order, Bag
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

admin_bp = Blueprint('admin', __name__)

def admin_required():
    claims = get_jwt()
    if claims['role'] != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    return None

# ── Get all users ─────────────────────────────────────
@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    error = admin_required()
    if error: return error

    users = User.query.all()
    return jsonify([{
        'id': u.id,
        'name': u.name,
        'email': u.email,
        'role': u.role,
        'created_at': u.created_at.isoformat()
    } for u in users]), 200


# ── Delete user ───────────────────────────────────────
@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    error = admin_required()
    if error: return error

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted'}), 200


# ── Get all stores ────────────────────────────────────
@admin_bp.route('/stores', methods=['GET'])
@jwt_required()
def get_all_stores():
    error = admin_required()
    if error: return error

    stores = Store.query.all()
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'district': s.district,
        'category': s.category,
        'is_active': s.is_active,
        'owner': {
            'id': s.owner.id,
            'name': s.owner.name,
            'email': s.owner.email
        }
    } for s in stores]), 200


# ── Toggle store active/inactive ──────────────────────
@admin_bp.route('/stores/<int:store_id>/toggle', methods=['PUT'])
@jwt_required()
def toggle_store(store_id):
    error = admin_required()
    if error: return error

    store = Store.query.get_or_404(store_id)
    store.is_active = not store.is_active
    db.session.commit()
    return jsonify({
        'message': f'Store {"activated" if store.is_active else "deactivated"}',
        'is_active': store.is_active
    }), 200


# ── Get all orders ────────────────────────────────────
@admin_bp.route('/orders', methods=['GET'])
@jwt_required()
def get_all_orders():
    error = admin_required()
    if error: return error

    orders = Order.query.order_by(Order.created_at.desc()).all()
    return jsonify([{
        'id': o.id,
        'status': o.status,
        'total_price': o.total_price,
        'created_at': o.created_at.isoformat(),
        'customer': {'id': o.customer.id, 'name': o.customer.name},
        'bag': {'id': o.bag.id, 'title': o.bag.title},
        'store': {'id': o.bag.store.id, 'name': o.bag.store.name}
    } for o in orders]), 200


# ── Dashboard summary metrics ─────────────────────────
@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    error = admin_required()
    if error: return error

    from sqlalchemy import func
    from datetime import datetime, timedelta

    total_users = User.query.count()
    total_stores = Store.query.filter_by(is_active=True).count()
    total_orders = Order.query.count()
    total_revenue = db.session.query(func.sum(Order.total_price)).scalar() or 0

    # Orders by status
    statuses = ['pending', 'confirmed', 'picked_up', 'cancelled']
    orders_by_status = {
        s: Order.query.filter_by(status=s).count() for s in statuses
    }

    # Orders last 7 days
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_orders = Order.query.filter(Order.created_at >= seven_days_ago).count()

    # Top stores by orders
    top_stores = db.session.query(
        Store.name,
        func.count(Order.id).label('order_count')
    ).join(Bag, Bag.store_id == Store.id)\
     .join(Order, Order.bag_id == Bag.id)\
     .group_by(Store.id)\
     .order_by(func.count(Order.id).desc())\
     .limit(5).all()

    # Food waste saved (each bag = 0.5kg saved)
    picked_up_orders = Order.query.filter_by(status='picked_up').count()
    food_waste_saved_kg = picked_up_orders * 0.5

    return jsonify({
        'total_users': total_users,
        'total_stores': total_stores,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'recent_orders_7days': recent_orders,
        'orders_by_status': orders_by_status,
        'food_waste_saved_kg': food_waste_saved_kg,
        'top_stores': [{'name': s.name, 'order_count': s.order_count} for s in top_stores]
    }), 200


# ── Promote user to admin ─────────────────────────────
@admin_bp.route('/users/<int:user_id>/promote', methods=['PUT'])
@jwt_required()
def promote_user(user_id):
    error = admin_required()
    if error: return error

    user = User.query.get_or_404(user_id)
    user.role = 'admin'
    db.session.commit()
    return jsonify({'message': f'{user.name} promoted to admin'}), 200