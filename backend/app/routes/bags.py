from flask import Blueprint, request, jsonify
from app import db
from app.models import Bag, Store
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime

bags_bp = Blueprint('bags', __name__)

@bags_bp.route('/', methods=['GET'])
def get_bags():
    district = request.args.get('district')
    category = request.args.get('category')
    max_price = request.args.get('max_price', type=float)
    search = request.args.get('search')

    query = Bag.query.join(Store).filter(
        Bag.is_available == True,
        Store.is_active == True
    )

    if district:
        query = query.filter(Store.district == district)
    if category:
        query = query.filter(Store.category == category)
    if max_price:
        query = query.filter(Bag.price <= max_price)
    if search:
        query = query.filter(Bag.title.ilike(f'%{search}%'))

    bags = query.all()

    return jsonify([{
        'id': b.id,
        'title': b.title,
        'description': b.description,
        'price': b.price,
        'original_value': b.original_value,
        'quantity': b.quantity,
        'pickup_start': str(b.pickup_start),
        'pickup_end': str(b.pickup_end),
        'store': {
            'id': b.store.id,
            'name': b.store.name,
            'district': b.store.district,
            'category': b.store.category,
            'image_url': b.store.image_url
        }
    } for b in bags]), 200


@bags_bp.route('/', methods=['POST'])
@jwt_required()
def create_bag():
    identity = get_jwt_identity()
    claims = get_jwt()

    if claims['role'] != 'business':
        return jsonify({'error': 'Only business accounts can create bags'}), 403

    data = request.get_json()
    required = ['store_id', 'title', 'price', 'quantity', 'pickup_start', 'pickup_end']
    for field in required:
        if data.get(field) is None:
            return jsonify({'error': f'{field} is required'}), 400

    store = Store.query.get_or_404(data['store_id'])
    if store.owner_id != int(identity):
        return jsonify({'error': 'Unauthorized'}), 403

    bag = Bag(
        store_id=data['store_id'],
        title=data['title'],
        description=data.get('description', ''),
        price=data['price'],
        original_value=data.get('original_value'),
        quantity=data['quantity'],
        pickup_start=datetime.strptime(data['pickup_start'], '%H:%M').time(),
        pickup_end=datetime.strptime(data['pickup_end'], '%H:%M').time(),
    )
    db.session.add(bag)
    db.session.commit()

    return jsonify({'message': 'Bag created', 'bag_id': bag.id}), 201


@bags_bp.route('/<int:bag_id>', methods=['PUT'])
@jwt_required()
def update_bag(bag_id):
    identity = get_jwt_identity()
    bag = Bag.query.get_or_404(bag_id)

    if bag.store.owner_id != int(identity):
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    for field in ['title', 'description', 'price', 'original_value', 'quantity', 'is_available']:
        if data.get(field) is not None:
            setattr(bag, field, data[field])

    if data.get('pickup_start'):
        bag.pickup_start = datetime.strptime(data['pickup_start'], '%H:%M').time()
    if data.get('pickup_end'):
        bag.pickup_end = datetime.strptime(data['pickup_end'], '%H:%M').time()

    db.session.commit()
    return jsonify({'message': 'Bag updated'}), 200


@bags_bp.route('/<int:bag_id>', methods=['DELETE'])
@jwt_required()
def delete_bag(bag_id):
    identity = get_jwt_identity()
    bag = Bag.query.get_or_404(bag_id)

    if bag.store.owner_id != int(identity):
        return jsonify({'error': 'Unauthorized'}), 403

    db.session.delete(bag)
    db.session.commit()
    return jsonif