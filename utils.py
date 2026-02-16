import re
from typing import Optional, Tuple, List, Dict
import random
from datetime import datetime

from models import ProfileInfo

# Test card numbers (Stripe test cards)
TEST_CARDS = {
    "stripe_visa": "4242 4242 4242 4242",
    "stripe_mastercard": "5555 5555 5555 4444",
    "stripe_amex": "3782 822463 10005",
    "stripe_discover": "6011 1111 1111 1117",
    "stripe_diners": "3056 9309 0259 04",
    "stripe_jcb": "3530 1113 3330 0000",
    "stripe_unionpay": "6200 0000 0000 0005",
}

# Masked placeholders
MASKED_CARDS = [
    "4242XXXXXXXX4242",
    "4000XXXXXXXX0002",
    "5555XXXXXXXX4444",
    "3782XXXXXXX10005",
    "6011XXXXXXX1117",
]

# Demo profile data by country
PROFILES: Dict[str, List[Dict]] = {
    "US": [
        {"name": "John Smith", "address": "123 Demo Street", "city": "Austin", "postcode": "78701", "state": "TX"},
        {"name": "Jane Doe", "address": "456 Oak Avenue", "city": "New York", "postcode": "10001", "state": "NY"},
        {"name": "Robert Johnson", "address": "789 Pine Road", "city": "Los Angeles", "postcode": "90001", "state": "CA"},
    ],
    "UK": [
        {"name": "Oliver Brown", "address": "77 Demo Ave", "city": "London", "postcode": "SW1A 1AA", "state": "Greater London"},
        {"name": "Emma Wilson", "address": "42 Baker Street", "city": "Manchester", "postcode": "M1 1AE", "state": "Greater Manchester"},
    ],
    "CA": [
        {"name": "Olivia Brown", "address": "77 Demo Ave", "city": "Toronto", "postcode": "M5V 2T6", "state": "ON"},
        {"name": "Liam Davis", "address": "456 Maple Street", "city": "Vancouver", "postcode": "V6B 1A1", "state": "BC"},
    ],
    "AU": [
        {"name": "William Taylor", "address": "123 Beach Road", "city": "Sydney", "postcode": "2000", "state": "NSW"},
        {"name": "Sophie Martin", "address": "456 Harbour St", "city": "Melbourne", "postcode": "3000", "state": "VIC"},
    ],
    "DE": [
        {"name": "Hans Mueller", "address": "Hauptstraße 123", "city": "Berlin", "postcode": "10115", "state": "Berlin"},
        {"name": "Anna Schmidt", "address": "Bergstraße 45", "city": "Munich", "postcode": "80331", "state": "Bavaria"},
    ],
    "FR": [
        {"name": "Jean Dupont", "address": "123 Rue de Rivoli", "city": "Paris", "postcode": "75001", "state": "Île-de-France"},
        {"name": "Marie Laurent", "address": "456 Avenue des Champs", "city": "Lyon", "postcode": "69001", "state": "Auvergne-Rhône-Alpes"},
    ],
    "JP": [
        {"name": "Takashi Yamamoto", "address": "1-2-3 Shibuya", "city": "Tokyo", "postcode": "150-0001", "state": "Tokyo"},
        {"name": "Yuki Tanaka", "address": "4-5-6 Osaka", "city": "Osaka", "postcode": "530-0001", "state": "Osaka"},
    ],
}

TOP_COUNTRIES = [
    ("🇺🇸 United States", "US"),
    ("🇬🇧 United Kingdom", "UK"),
    ("🇨🇦 Canada", "CA"),
    ("🇦🇺 Australia", "AU"),
    ("🇩🇪 Germany", "DE"),
    ("🇫🇷 France", "FR"),
    ("🇮🇹 Italy", "IT"),
    ("🇪🇸 Spain", "ES"),
    ("🇧🇷 Brazil", "BR"),
    ("🇮🇳 India", "IN"),
    ("🇧🇩 Bangladesh", "BD"),
    ("🇦🇪 UAE", "AE"),
    ("🇸🇦 Saudi Arabia", "SA"),
    ("🇹🇷 Turkey", "TR"),
    ("🇯🇵 Japan", "JP"),
    ("🇰🇷 South Korea", "KR"),
    ("🇸🇬 Singapore", "SG"),
    ("🇲🇾 Malaysia", "MY"),
]

GENDERS = [
    ("👨 Male", "male"),
    ("👩 Female", "female"),
    ("🎲 Any", "any"),
]

def is_bin_like_input(text: str) -> bool:
    """Check if input looks like BIN/prefix generation"""
    # Remove any separators
    cleaned = re.sub(r'[\s\-_|]', '', text)
    
    # Check if it's all digits and >= 6 digits
    if cleaned.isdigit() and len(cleaned) >= 6:
        return True
    
    # Check if it contains a pipe with digits
    if '|' in text:
        parts = text.split('|')
        if parts[0].replace(' ', '').isdigit() and len(parts[0].replace(' ', '')) >= 6:
            return True
    
    return False

def parse_template_input(text: str) -> Tuple[str, Optional[str], Optional[str]]:
    """Parse template input: key or key|MM|YYYY"""
    parts = text.split('|')
    key = parts[0].strip()
    
    if len(parts) >= 3:
        month = parts[1].strip().zfill(2)
        year = parts[2].strip()
        if len(year) == 2:
            year = f"20{year}"
        return key, month, year
    elif len(parts) == 2:
        # Assume MM|YYYY
        month = parts[0].strip().zfill(2)
        year = parts[1].strip()
        if len(year) == 2:
            year = f"20{year}"
        return key, month, year
    
    return key, None, None

def format_expiry(month: str, year: str) -> str:
    """Format expiry as MM/YY"""
    if len(year) == 4:
        year = year[2:]
    return f"{month}/{year}"

def get_demo_profile(country_code: str, gender: str = "any") -> ProfileInfo:
    """Generate demo profile for given country"""
    if country_code not in PROFILES:
        country_code = "US"
    
    profiles = PROFILES[country_code]
    
    # Filter by gender if needed (simplified - just random selection)
    profile = random.choice(profiles)
    
    return ProfileInfo(
        country=country_code,
        name=profile["name"],
        address_line1=profile["address"],
        city=profile["city"],
        postcode=profile["postcode"],
        state=profile["state"]
    )

def generate_masked_cards(count: int = 10) -> List[str]:
    """Generate masked card lines"""
    cards = []
    for _ in range(count):
        card = random.choice(MASKED_CARDS)
        exp = f"{random.randint(1,12):02d}/{random.randint(25,30)}"
        cvv = f"{random.randint(100,999)}"
        cards.append(f"{card}|{exp}|{cvv}")
    return cards[:count]

def format_private_card_output(card_num: str, exp: str, cvv: str, profile: ProfileInfo) -> str:
    """Format card output for private chat"""
    country_names = {
        "US": "United States", "UK": "United Kingdom", "CA": "Canada", "AU": "Australia",
        "DE": "Germany", "FR": "France", "JP": "Japan", "IT": "Italy", "ES": "Spain",
        "BR": "Brazil", "IN": "India", "BD": "Bangladesh", "AE": "UAE", "SA": "Saudi Arabia",
        "TR": "Turkey", "KR": "South Korea", "SG": "Singapore", "MY": "Malaysia"
    }
    
    return f"""<pre>✨ CHECK AND SAVE YOUR TEST PAYMENT CARD ✨

💳 CARD NUMBER : {card_num} (TEST)
📅 MM/YY : {exp}
🔒 CVV : {cvv} (TEST ONLY)

🌍 COUNTRY : {country_names.get(profile.country, profile.country)}
👨‍💻 NAME : {profile.name} (FAKE)
🏠 ADDRESS LINE 1 : {profile.address_line1}
🏙️ TOWN / CITY : {profile.city}
📮 POSTCODE : {profile.postcode}
📍 STATE : {profile.state}

⚠️ DEMO ONLY — Not for real payments.</pre>"""

def format_group_card_output(template_name: str, cards: List[str]) -> str:
    """Format card output for group chat"""
    cards_text = "\n".join(cards)
    return f"""<pre>✨ 〘 CHECK AND SAVE YOUR {template_name} 〙 ✨

💳 CARD LIST
{cards_text}</pre>"""

def format_profile_output(profile: ProfileInfo) -> str:
    """Format profile info output"""
    country_names = {
        "US": "United States", "UK": "United Kingdom", "CA": "Canada", "AU": "Australia",
        "DE": "Germany", "FR": "France", "JP": "Japan", "IT": "Italy", "ES": "Spain",
        "BR": "Brazil", "IN": "India", "BD": "Bangladesh", "AE": "UAE", "SA": "Saudi Arabia",
        "TR": "Turkey", "KR": "South Korea", "SG": "Singapore", "MY": "Malaysia"
    }
    
    return f"""<pre>🌍 COUNTRY : {country_names.get(profile.country, profile.country)}
👨‍💻 NAME : {profile.name} (FAKE)
🏠 ADDRESS LINE 1 : {profile.address_line1}
🏙️ TOWN / CITY : {profile.city}
📮 POSTCODE : {profile.postcode}
📍 STATE : {profile.state}</pre>"""

class RateLimiter:
    def __init__(self, max_actions: int = 10, window_seconds: int = 60):
        self.max_actions = max_actions
        self.window_seconds = window_seconds
        self.user_actions: Dict[int, List[datetime]] = {}
    
    def check(self, user_id: int) -> bool:
        """Check if user is rate limited"""
        now = datetime.now()
        if user_id not in self.user_actions:
            self.user_actions[user_id] = []
        
        # Remove old actions
        self.user_actions[user_id] = [
            ts for ts in self.user_actions[user_id] 
            if (now - ts).total_seconds() < self.window_seconds
        ]
        
        if len(self.user_actions[user_id]) >= self.max_actions:
            return False
        
        self.user_actions[user_id].append(now)
        return True

rate_limiter = RateLimiter()

class NavigationStack:
    def __init__(self):
        self.stacks: Dict[int, list] = {}
    
    def push(self, user_id: int, screen: str):
        if user_id not in self.stacks:
            self.stacks[user_id] = []
        self.stacks[user_id].append(screen)
    
    def pop(self, user_id: int) -> str:
        if user_id in self.stacks and self.stacks[user_id]:
            return self.stacks[user_id].pop()
        return "MAIN_MENU"
    
    def current(self, user_id: int) -> str:
        if user_id in self.stacks and self.stacks[user_id]:
            return self.stacks[user_id][-1]
        return "MAIN_MENU"
    
    def clear(self, user_id: int):
        if user_id in self.stacks:
            self.stacks[user_id] = []
    
    def back(self, user_id: int) -> str:
        self.pop(user_id)
        return self.current(user_id)

nav_stack = NavigationStack()
