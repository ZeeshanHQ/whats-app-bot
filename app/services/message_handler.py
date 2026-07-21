import logging
from app.models.webhook import WebhookPayload, Message
from app.client.whatsapp import whatsapp_client
from app.services.ai_brain import ai_service

logger = logging.getLogger("message_handler")


async def process_webhook_payload(payload: WebhookPayload) -> None:
    """
    Parses and processes incoming WhatsApp webhook payloads asynchronously.
    Filter out status receipts and handles incoming user messages.
    """
    if not payload.entry:
        logger.debug("Received payload with no entry items.")
        return

    for entry in payload.entry:
        for change in entry.changes:
            val = change.value

            # Ignore status receipts (sent, delivered, read)
            if val.statuses and not val.messages:
                for status in val.statuses:
                    logger.info(
                        f"Status update received: recipient_id={status.recipient_id}, "
                        f"status={status.status}, timestamp={status.timestamp}"
                    )
                continue

            # Process incoming messages
            if val.messages:
                for message in val.messages:
                    await handle_single_message(message)


async def handle_single_message(message: Message) -> None:
    """
    Handles an individual message item extracted from the webhook.
    Routes user text & interactive button/list selections to appropriate handlers.
    """
    wa_id = message.from_wa_id
    wamid = message.id
    msg_type = message.type

    logger.info(f"Processing message ID: {wamid} from wa_id: {wa_id} (type: {msg_type})")

    # Handle Interactive Quick Reply Buttons or List Selections
    if msg_type == "interactive" and message.interactive:
        interactive = message.interactive
        btn_id = ""
        btn_title = ""

        if interactive.type == "button_reply" and interactive.button_reply:
            btn_id = interactive.button_reply.id
            btn_title = interactive.button_reply.title
        elif interactive.type == "list_reply" and interactive.list_reply:
            btn_id = interactive.list_reply.id
            btn_title = interactive.list_reply.title

        logger.info(f"Interactive reply from {wa_id}: button_id='{btn_id}', title='{btn_title}'")

        if btn_id == "btn_pricing":
            prompt = "What are the Astraventa WhatsApp Automation pricing packages and costs?"
            ai_reply = await ai_service.process_user_query(wa_id=wa_id, prompt=prompt)
            
            # Follow up with interactive action buttons
            buttons = [
                {"id": "btn_book_call", "title": "Book a Call"},
                {"id": "btn_services", "title": "View Services"},
            ]
            await whatsapp_client.send_interactive_buttons(
                to=wa_id,
                body_text=ai_reply,
                buttons=buttons,
                header_text="Astraventa Pricing",
                footer_text="Astraventa AI Engine",
            )
            return

        elif btn_id == "btn_services":
            prompt = "What services and capabilities does Astraventa offer?"
            ai_reply = await ai_service.process_user_query(wa_id=wa_id, prompt=prompt)
            
            buttons = [
                {"id": "btn_pricing", "title": "View Pricing"},
                {"id": "btn_book_call", "title": "Book a Call"},
            ]
            await whatsapp_client.send_interactive_buttons(
                to=wa_id,
                body_text=ai_reply,
                buttons=buttons,
                header_text="Astraventa Services",
                footer_text="Astraventa AI Engine",
            )
            return

        elif btn_id == "btn_book_call":
            reply_text = (
                "📅 **Book a Consultation Call with Astraventa**\n\n"
                "We would love to discuss your AI Automation requirements!\n\n"
                "🔗 Schedule a 15-min call: https://astraventa.com/book\n"
                "📧 Email: contact@astraventa.com\n"
                "📞 Direct WhatsApp: +1 (555) 153-2305"
            )
            await whatsapp_client.send_text_message(to=wa_id, text=reply_text, reply_to_wamid=wamid)
            return

        else:
            # Custom interactive button fallback
            prompt = f"User selected option: {btn_title}"
            ai_reply = await ai_service.process_user_query(wa_id=wa_id, prompt=prompt)
            await whatsapp_client.send_text_message(to=wa_id, text=ai_reply, reply_to_wamid=wamid)
            return

    # Handle Standard Text Messages
    elif msg_type == "text" and message.text:
        user_text = message.text.body.strip()
        logger.info(f"Text message from {wa_id}: {user_text}")

        # Detect intent
        intent = await ai_service.detect_intent(user_text)

        if intent in ["show_options", "pricing", "services"]:
            ai_reply = await ai_service.process_user_query(wa_id=wa_id, prompt=user_text)
            
            buttons = [
                {"id": "btn_pricing", "title": "View Pricing"},
                {"id": "btn_services", "title": "View Services"},
                {"id": "btn_book_call", "title": "Book a Call"},
            ]
            try:
                res = await whatsapp_client.send_interactive_buttons(
                    to=wa_id,
                    body_text=ai_reply,
                    buttons=buttons,
                    header_text="Astraventa Assistant",
                    footer_text="Select an option below",
                )
                if res.get("error"):
                    # Fallback to plain text if interactive button failed
                    await whatsapp_client.send_text_message(to=wa_id, text=ai_reply, reply_to_wamid=wamid)
            except Exception as exc:
                logger.error(f"Failed to send interactive buttons: {exc}. Falling back to plain text.")
                await whatsapp_client.send_text_message(to=wa_id, text=ai_reply, reply_to_wamid=wamid)
            return

        # General text response
        ai_reply = await ai_service.process_user_query(wa_id=wa_id, prompt=user_text)
        await whatsapp_client.send_text_message(
            to=wa_id,
            text=ai_reply,
            reply_to_wamid=wamid,
        )

    else:
        # Handle media, location, sticker, or other message types
        prompt = f"[User sent a {msg_type} message]"
        ai_reply = await ai_service.process_user_query(wa_id=wa_id, prompt=prompt)
        await whatsapp_client.send_text_message(
            to=wa_id,
            text=ai_reply,
            reply_to_wamid=wamid,
        )
