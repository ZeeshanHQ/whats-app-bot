import asyncio
from fastapi.testclient import TestClient
from main import app
from app.config import settings

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "ai_model" in data
    print("[OK] Root health check endpoint working.")


def test_webhook_verification_success():
    verify_token = settings.WEBHOOK_VERIFY_TOKEN
    challenge = "115820149"
    url = f"/webhook?hub.mode=subscribe&hub.verify_token={verify_token}&hub.challenge={challenge}"
    response = client.get(url)
    assert response.status_code == 200
    assert response.text == challenge
    print("[OK] GET /webhook verification test passed.")


def test_ai_chat_and_memory():
    wa_id = f"test_user_stress_{int(asyncio.get_event_loop().time()) if hasattr(asyncio, 'get_event_loop') else 9999}"
    # Multi-turn complex query test
    res1 = client.post("/api/ai/chat", json={"wa_id": wa_id, "message": "What are your enterprise AI services and can I get a quote?"})
    assert res1.status_code == 200
    data1 = res1.json()
    assert "ai_reply" in data1
    assert len(data1["ai_reply"]) > 0
    print(f"[OK] Complex Query AI Reply: {data1['ai_reply'][:100]}...")

    # Follow-up question
    res2 = client.post("/api/ai/chat", json={"wa_id": wa_id, "message": "How does the enterprise plan compare to starter?"})
    assert res2.status_code == 200
    data2 = res2.json()
    assert len(data2["history"]) >= 4
    print(f"[OK] Multi-turn Follow-up AI Reply: {data2['ai_reply'][:100]}...")


def test_interactive_endpoint():
    res_btn = client.post("/api/test/interactive", json={"to": "923055255838", "type": "button", "body_text": "Interactive Button Test"})
    assert res_btn.status_code == 200
    print("[OK] POST /api/test/interactive (button) endpoint test passed.")

    res_list = client.post("/api/test/interactive", json={"to": "923055255838", "type": "list", "body_text": "Interactive List Test"})
    assert res_list.status_code == 200
    print("[OK] POST /api/test/interactive (list) endpoint test passed.")


def test_webhook_interactive_button_reply():
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "1923128108402883",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "phone_number_id": "1260602290465050"
                            },
                            "messages": [
                                {
                                    "from": "923055255838",
                                    "id": "wamid.HBgMInteractiveTest123",
                                    "timestamp": "1720000000",
                                    "type": "interactive",
                                    "interactive": {
                                        "type": "button_reply",
                                        "button_reply": {
                                            "id": "btn_pricing",
                                            "title": "View Pricing"
                                        }
                                    }
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    print("[OK] POST /webhook interactive button reply test passed.")


if __name__ == "__main__":
    test_root()
    test_webhook_verification_success()
    test_ai_chat_and_memory()
    test_interactive_endpoint()
    test_webhook_interactive_button_reply()
    print("\nAll Interactive Message & Stress Tests passed successfully!")
