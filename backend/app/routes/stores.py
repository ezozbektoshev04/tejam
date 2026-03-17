from flask import Blueprint, request, jsonify
from app import db
from app.models import Store, Bag, Review
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

stores_bp = Blueprint('stores', __name__)

@stores_bp.route('/', methods=['GET'])
def get_stores():
    district = request.args.get('district')
    category = request.args.get('category')
    search = request.args.get('search')

    query = Store.query.filter_by(is_active=True)

    if district:
        query = query.filter_by(district=district)
    if category:
        query = query.filter_by(category=category)
    if search:
        query = query.filter(Store.name.ilike(f'%{search}%'))

    stores = query.all()

    return jsonify([{
        'id': s.id,
        'name': s.name,
        'address': s.address,
        'district': s.district,
        'category': s.category,
        'image_url': s.image_url,
    } for s in stores]), 200


@stores_bp.route('/<int:store_id>', methods=['GET'])
def get_store(store_id):
    store = Store.query.get_or_404(store_id)

    bags = [{
        'id': b.id,
        'title': b.title,
        'description': b.description,
        'price': b.price,
        'original_value': b.original_value,
        'quantity': b.quantity,
        'pickup_start': str(b.pickup_start),
        'pickup_end': str(b.pickup_end),
        'is_available': b.is_available
    } for b in store.bags if b.is_available]

    reviews = [{
        'id': r.id,
        'rating': r.rating,
        'comment': r.comment,
        'created_at': r.created_at.isoformat()
    } for r in store.reviews]

    avg_rating = round(sum(r.rating for r in store.reviews) / len(store.reviews), 1) if store.reviews else 0

    return jsonify({
        'id': store.id,
        'name': store.name,
        'address': store.address,
        'district': store.district,
        'category': store.category,
        'image_url': store.image_url,
        'bags': bags,
        'reviews': reviews,
        'avg_rating': avg_rating
    }), 200


@stores_bp.route('/', methods=['POST'])
@jwt_required()
def create_store():
    identity = get_jwt_identity()
    claims = get_jwt()

    if claims['role'] != 'business':
        return jsonify({'error': 'Only business accounts can create stores'}), 403

    data = request.get_json()
    required = ['name', 'address', 'district', 'category']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400

    store = Store(
        owner_id=int(identity),
        name=data['name'],
        address=data['address'],
        district=data['district'],
        category=data['category'],
        image_url=data.get('image_url')
    )
    db.session.add(store)
    db.session.commit()

    return jsonify({'message': 'Store created', 'store_id': store.id}), 201


@stores_bp.route('/<int:store_id>', methods=['PUT'])
@jwt_required()
def update_store(store_id):
    identity = get_jwt_identity()
    claims = get_jwt()
    store = Store.query.get_or_404(store_id)

    if store.owner_id != int(identity) and claims['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    for field in ['name', 'address', 'district', 'category', 'image_url']:
        if data.get(field):
            setattr(store, field, data[field])

    db.session.commit()
    return jsonify({'message': 'Store updated'}), 200


@stores_bp.route('/<int:store_id>', methods=['DELETE'])
@jwt_required()
def delete_store(store_id):
    identity = get_jwt_identity()
    claims = get_jwt()
    store = Store.query.get_or_404(store_id)

    if store.owner_id != int(identity) and claims['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    store.is_active = False
    db.session.commit()
    return jsonify({'message': 'Store deactivated'}), 200


@stores_bp.route('/<int:store_id>/reviews', methods=['POST'])
@jwt_required()
def add_review(store_id):
    identity = get_jwt_identity()
    claims = get_jwt()

    if claims['role'] != 'customer':
        return jsonify({'error': 'Only customers can leave reviews'}), 403

    data = request.get_json()
    if not data.get('rating') or not (1 <= data['rating'] <= 5):
        return jsonify({'error': 'Rating must be between 1 and 5'}), 400

    review = Review(
        customer_id=int(identity),
        store_id=store_id,
        rating=data['rating'],
        comment=data.get('comment', '')
    )
    db.session.add(review)
    db.session.commit()

    return jsonify({'message': 'Review added'}), 201