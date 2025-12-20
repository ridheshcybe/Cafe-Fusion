import re
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from functools import wraps

from flask import flash, redirect, request, session, url_for
from app import db
from models import User


# ============================================================================
# VALIDATION UTILITIES
# ============================================================================

def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """Sanitize string input by stripping and limiting length."""
    if not value:
        return ""
    
    sanitized = value.strip()
    
    # Remove potentially dangerous characters for certain fields
    if max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def validate_email(email: str) -> bool:
    """Validate email format."""
    if not email:
        return False
    
    email = email.strip().lower()
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """Validate phone number format (basic validation)."""
    if not phone:
        return False
    
    phone = phone.strip()
    # Allow digits, spaces, hyphens, plus, and parentheses
    pattern = r'^[\d\s\-\+\(\)]+$'
    return bool(re.match(pattern, phone)) and len(phone) >= 10


def validate_name(name: str) -> bool:
    """Validate name field."""
    if not name:
        return False
    
    name = name.strip()
    # Allow letters, spaces, hyphens, apostrophes, periods, but not digits
    pattern = r'^[a-zA-Z\u00C0-\uFFFF\s\-\.\']+$'
    return bool(re.match(pattern, name)) and len(name) >= 2


def validate_quantity(qty: str) -> Optional[int]:
    """Validate and convert quantity to integer."""
    try:
        qty_int = int(qty)
        return qty_int if qty_int > 0 else None
    except (ValueError, TypeError):
        return None


def validate_price(price: str) -> Optional[int]:
    """Validate and convert price to cents."""
    try:
        if not price:
            return None
            
        # Check for negative sign first
        if price.strip().startswith('-'):
            return None
            
        # Remove currency symbols and convert to float
        price_clean = re.sub(r'[^\d.]', '', price)
        if not price_clean:  # Empty after cleaning
            return None
            
        price_float = float(price_clean)
        if price_float >= 0:
            return int(price_float * 100)  # Convert to cents
    except (ValueError, TypeError):
        pass
    return None


def sanitize_form_data(form_data: Dict[str, Any], rules: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Sanitize and validate form data based on rules.
    
    Rules format:
    {
        'field_name': {
            'type': 'string'|'email'|'phone'|'name'|'quantity'|'price',
            'required': bool,
            'max_length': int,
            'default': any
        }
    }
    """
    sanitized = {}
    
    for field, rule in rules.items():
        raw_value = form_data.get(field, '')
        
        if raw_value is None:
            raw_value = ''
        
        # Handle string types
        if rule.get('type') in ['string', 'email', 'phone', 'name']:
            sanitized_value = sanitize_string(str(raw_value), rule.get('max_length'))
            
            # Check required field first
            if rule.get('required', False) and not sanitized_value:
                raise ValueError(f"Field {field} is required")
            
            # Apply specific validation
            if rule['type'] == 'email' and sanitized_value and not validate_email(sanitized_value):
                raise ValueError(f"Invalid email format for {field}")
            elif rule['type'] == 'phone' and sanitized_value and not validate_phone(sanitized_value):
                raise ValueError(f"Invalid phone format for {field}")
            elif rule['type'] == 'name' and sanitized_value and not validate_name(sanitized_value):
                raise ValueError(f"Invalid name format for {field}")
                
        elif rule['type'] == 'quantity':
            sanitized_value = validate_quantity(str(raw_value))
            if sanitized_value is None:
                if rule.get('required', False):
                    raise ValueError(f"Invalid quantity for {field}")
                sanitized_value = rule.get('default', 1)
                
        elif rule['type'] == 'price':
            sanitized_value = validate_price(str(raw_value))
            if sanitized_value is None:
                if rule.get('required', False):
                    raise ValueError(f"Invalid price for {field}")
                sanitized_value = rule.get('default', 0)
        
        sanitized[field] = sanitized_value
    
    return sanitized


# ============================================================================
# AUTHENTICATION UTILITIES
# ============================================================================

def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)


def login_required(role=None):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not session.get("user_id"):
                flash("Please log in to continue.", "warning")
                return redirect(url_for("auth.login", next=request.path))

            if role is not None:
                user_role = session.get("role")
                if user_role != role:
                    flash("You are not allowed to access that page.", "danger")
                    return redirect(url_for("menu.index"))

            return fn(*args, **kwargs)

        return wrapper

    return decorator


# ============================================================================
# CART UTILITIES
# ============================================================================

def get_cart() -> dict[str, int]:
    cart = session.get("cart")
    if not isinstance(cart, dict):
        cart = {}
    normalized = {}
    for k, v in cart.items():
        try:
            normalized[str(int(k))] = int(v)
        except Exception:
            continue
    session["cart"] = normalized
    return normalized


def set_cart(cart: dict[str, int]) -> None:
    session["cart"] = {str(int(k)): int(v) for k, v in cart.items()}


def clear_cart() -> None:
    session["cart"] = {}


def cart_count() -> int:
    cart = get_cart()
    return sum(int(qty) for qty in cart.values())


def parse_items_spec(spec: str) -> list[tuple[int, int]]:
    if not spec:
        return []

    parts = [p.strip() for p in spec.split(";") if p.strip()]
    items: list[tuple[int, int]] = []
    for p in parts:
        if ":" not in p:
            raise ValueError("Invalid format. Use item_id:qty;item_id:qty")
        item_id_s, qty_s = [x.strip() for x in p.split(":", 1)]
        item_id = int(item_id_s)
        qty = int(qty_s)
        if qty <= 0:
            raise ValueError("Quantity must be >= 1")
        items.append((item_id, qty))
    return items


# ============================================================================
# LOGGING UTILITIES
# ============================================================================

class StructuredLogger:
    def __init__(self, name: str = "cafe_fusion"):
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def log_order(self, order_id: int, action: str, user_id: Optional[int] = None, 
                  details: Optional[Dict[str, Any]] = None):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "order",
            "order_id": order_id,
            "action": action,
            "user_id": user_id
        }
        if details:
            log_data.update(details)
        
        self.logger.info(json.dumps(log_data))
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "error",
            "error_type": type(error).__name__,
            "error_message": str(error)
        }
        if context:
            log_data.update(context)
        
        self.logger.error(json.dumps(log_data))
    
    def log_auth(self, user_id: int, action: str, email: str, 
                 success: bool, details: Optional[Dict[str, Any]] = None):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "auth",
            "user_id": user_id,
            "action": action,
            "email": email,
            "success": success
        }
        if details:
            log_data.update(details)
        
        self.logger.info(json.dumps(log_data))


# Global logger instance
logger = StructuredLogger()
