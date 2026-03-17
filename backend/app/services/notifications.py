from app import mail
from flask_mail import Message
from flask import current_app

def send_order_notification(email, bag_title, store_name, pickup_start, pickup_end):
    try:
        msg = Message(
            subject='✅ Tejam — Order Confirmed!',
            sender=current_app.config['MAIL_USERNAME'],
            recipients=[email]
        )
        msg.body = f"""
Hello!

Your order has been confirmed. 🎉

🛍️  Bag: {bag_title}
🏪  Store: {store_name}
🕐  Pickup time: {pickup_start} - {pickup_end}

Thank you for using Tejam and helping reduce food waste in Uzbekistan!

— Tejam Team
        """
        mail.send(msg)
    except Exception as e:
        print(f"Email notification failed: {e}")