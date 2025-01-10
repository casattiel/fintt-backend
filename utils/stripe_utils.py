import os
import stripe

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def create_checkout_session(plan_id):
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price": plan_id,
                "quantity": 1,
            },
        ],
        mode="subscription",
        success_url=os.getenv("FRONTEND_SUCCESS_URL"),
        cancel_url=os.getenv("FRONTEND_CANCEL_URL"),
    )
    return session
