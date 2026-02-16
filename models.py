from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserSchema(BaseModel):
    id: int
    username: Optional[str] = None
    first_seen: datetime
    last_seen: datetime

class TemplateSchema(BaseModel):
    id: int
    name: str
    country: str
    label: str
    template_key: str
    display_card: str
    default_exp: str
    default_cvv: str
    
class ProfileInfo(BaseModel):
    country: str
    name: str
    address_line1: str
    city: str
    postcode: str
    state: str
    
class CardOutput(BaseModel):
    card_number: str
    expiry: str
    cvv: str
    profile: Optional[ProfileInfo] = None
