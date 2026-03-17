from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.models import Bag, Store, Order
from app import db
import google.generativeai as genai
import os

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.5-flash')

ai_bp = Blueprint('ai', __name__)


# ── AI Chatbot ────────────────────────────────────────
@ai_bp.route('/chat', methods=['POST'])
@jwt_required()
def chat():
    data = request.get_json()
    if not data.get('message'):
        return jsonify({'error': 'message is required'}), 400

    # Get available bags context
    bags = Bag.query.join(Store).filter(
        Bag.is_available == True,
        Store.is_active == True
    ).limit(20).all()

    bags_context = "\n".join([
        f"- {b.title} at {b.store.name} ({b.store.district}): {b.price} UZS, pickup {b.pickup_start}-{b.pickup_end}"
        for b in bags
    ])

    system_prompt = f"""You are Tejam Assistant, a helpful AI for the Tejam app — 
a food waste reduction platform in Uzbekistan (similar to Too Good To Go).
You help customers find surprise food bags from restaurants, bakeries and cafes in Tashkent.

Currently available bags:
{bags_context if bags_context else "No bags available right now."}

Districts in Tashkent we serve: Yunusabad, Chilonzor, Mirzo Ulugbek, Shaykhontohur, Uchtepa, Yakkasaroy.
Prices are in UZS (Uzbek Som). Be friendly, helpful and concise.
If asked in Uzbek or Russian, respond in the same language."""

    try:
        response = model.generate_content(f"{system_prompt}\n\nUser: {data['message']}")
        return jsonify({'reply': response.text}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Smart Recommendations ─────────────────────────────
@ai_bp.route('/recommendations', methods=['GET'])
@jwt_required()
def recommendations():
    identity = get_jwt_identity()

    # Get user's order history
    past_orders = Order.query.filter_by(
        customer_id=int(identity)
    ).order_by(Order.created_at.desc()).limit(10).all()

    # Get all available bags
    available_bags = Bag.query.join(Store).filter(
        Bag.is_available == True,
        Store.is_active == True
    ).all()

    if not available_bags:
        return jsonify({'recommendations': [], 'message': 'No bags available'}), 200

    # Build history context
    if past_orders:
        history = "\n".join([
            f"- {o.bag.title} from {o.bag.store.name} ({o.bag.store.category}) in {o.bag.store.district}"
            for o in past_orders
        ])
        history_prompt = f"User's past orders:\n{history}"
    else:
        history_prompt = "User has no past orders. Recommend popular and varied options."

    # Build available bags context
    bags_list = "\n".join([
        f"ID:{b.id} | {b.title} | {b.store.name} | {b.store.category} | {b.store.district} | {b.price} UZS"
        for b in available_bags
    ])

    prompt = f"""You are a recommendation engine for Tejam food app in Uzbekistan.
    
{history_prompt}

Available bags:
{bags_list}

Return ONLY a JSON array of up to 3 recommended bag IDs with reasons, like this:
[
  {{"bag_id": 1, "reason": "Matches your love for bakery items"}},
  {{"bag_id": 2, "reason": "Great value restaurant bag near you"}}
]
Return only valid JSON, no extra text."""

    try:
        response = model.generate_content(prompt)
        import json
        text = response.text.strip().replace('```json', '').replace('```', '').strip()
        recommendations_data = json.loads(text)

        # Enrich with full bag data
        result = []
        for rec in recommendations_data:
            bag = Bag.query.get(rec['bag_id'])
            if bag:
                result.append({
                    'bag_id': bag.id,
                    'title': bag.title,
                    'price': bag.price,
                    'original_value': bag.original_value,
                    'store': {
                        'name': bag.store.name,
                        'district': bag.store.district,
                        'category': bag.store.category
                    },
                    'pickup_start': str(bag.pickup_start),
                    'pickup_end': str(bag.pickup_end),
                    'reason': rec['reason']
                })

        return jsonify({'recommendations': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Food Waste Analytics (AI Summary) ────────────────
@ai_bp.route('/waste-summary', methods=['GET'])
@jwt_required()
def waste_summary():
    claims = get_jwt()

    # Get stats
    total_picked_up = Order.query.filter_by(status='picked_up').count()
    total_orders = Order.query.count()
    total_stores = Store.query.filter_by(is_active=True).count()

    from sqlalchemy import func
    total_revenue = db.session.query(func.sum(Order.total_price)).scalar() or 0

    food_saved_kg = total_picked_up * 0.5
    co2_saved_kg = food_saved_kg * 2.5  # 1kg food = ~2.5kg CO2

    prompt = f"""You are an environmental impact analyst for Tejam, a food waste app in Uzbekistan.

Platform stats:
- Total orders placed: {total_orders}
- Successfully picked up: {total_picked_up}
- Active stores: {total_stores}
- Estimated food saved: {food_saved_kg} kg
- Estimated CO2 saved: {co2_saved_kg} kg
- Total revenue: {total_revenue} UZS

Write a short, motivating 3-sentence summary of the environmental impact. 
Be specific with numbers. End with an encouraging message for users."""

    try:
        response = model.generate_content(prompt)
        return jsonify({
            'summary': response.text,
            'stats': {
                'total_orders': total_orders,
                'picked_up': total_picked_up,
                'food_saved_kg': food_saved_kg,
                'co2_saved_kg': co2_saved_kg,
                'total_revenue': total_revenue,
                'active_stores': total_stores
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500