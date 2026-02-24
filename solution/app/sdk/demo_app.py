import uuid
import time
from sdk.client import LottyClient

client = LottyClient(api_url="http://localhost:8000/api")

def main():
    user_id = uuid.uuid4()
    print(f"--- Заходим на сайт под юзером: {user_id} ---")

    decisions = client.resolve(
        subject_id=user_id, 
        keys=["promo_button_color"],
        attributes={"platform": "web"}
    )

    decision = decisions.get("promo_button_color")
    
    button_color = decision.value if decision else "gray"
    print(f"Отрисовка кнопки. Цвет: {button_color}")

    if decision and decision.decision_id:
        print("Пользователь нажал на кнопку! Отправляем конверсию...")
        client.track(user_id, decision.decision_id, "purchase_click")
        print("Конверсия засчитана.")

if __name__ == "__main__":
    main()