from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class Profile(BaseModel):
    name: Optional[str] = None


class Contact(BaseModel):
    profile: Optional[Profile] = None
    wa_id: str


class Metadata(BaseModel):
    display_phone_number: Optional[str] = None
    phone_number_id: Optional[str] = None


class TextMessage(BaseModel):
    body: str


class MediaMessage(BaseModel):
    id: Optional[str] = None
    mime_type: Optional[str] = None
    sha256: Optional[str] = None
    caption: Optional[str] = None
    filename: Optional[str] = None


class InteractiveReply(BaseModel):
    id: str
    title: str
    description: Optional[str] = None


class InteractiveMessage(BaseModel):
    type: str  # button_reply or list_reply
    button_reply: Optional[InteractiveReply] = None
    list_reply: Optional[InteractiveReply] = None


class ButtonMessage(BaseModel):
    payload: str
    text: str


class LocationMessage(BaseModel):
    latitude: float
    longitude: float
    name: Optional[str] = None
    address: Optional[str] = None


class Context(BaseModel):
    from_id: Optional[str] = Field(default=None, alias="from")
    id: Optional[str] = None


class Message(BaseModel):
    from_wa_id: str = Field(alias="from")
    id: str
    timestamp: str
    type: str  # text, image, audio, video, document, sticker, location, interactive, button
    text: Optional[TextMessage] = None
    image: Optional[MediaMessage] = None
    video: Optional[MediaMessage] = None
    audio: Optional[MediaMessage] = None
    document: Optional[MediaMessage] = None
    sticker: Optional[MediaMessage] = None
    interactive: Optional[InteractiveMessage] = None
    button: Optional[ButtonMessage] = None
    location: Optional[LocationMessage] = None
    context: Optional[Context] = None

    class Config:
        populate_by_name = True


class StatusRecipient(BaseModel):
    id: Optional[str] = None
    status: Optional[str] = None
    timestamp: Optional[str] = None
    recipient_id: Optional[str] = None


class WebhookValue(BaseModel):
    messaging_product: str = "whatsapp"
    metadata: Optional[Metadata] = None
    contacts: Optional[List[Contact]] = None
    messages: Optional[List[Message]] = None
    statuses: Optional[List[StatusRecipient]] = None


class WebhookChange(BaseModel):
    value: WebhookValue
    field: str = "messages"


class WebhookEntry(BaseModel):
    id: str
    changes: List[WebhookChange]


class WebhookPayload(BaseModel):
    object: str
    entry: Optional[List[WebhookEntry]] = None
