# Restaurant POS Scaffold

A complete FastAPI + Supabase scaffold for online orders, staff POS, inventory, and reports with PDF invoices.

## Core Structure
```
app/
├── config.py          # Env vars & settings
├── main.py            # FastAPI app
├── deps.py            # Dependencies (auth, session)
├── static/            # CSS, JS, images
└── templates/         # HTML templates
requirements.txt       # + xhtml2pdf for PDFs
```

## Authentication Routes
- **`/login`** - Session-based login
- **`/register`** - Customer registration  
- **`/staff/register`** - Staff registration (requires `staff_setup_code`)
- **`/logout`** - Clear session

**Staff auth**: Checks `user_metadata.role == 'staff'` from signed cookie session.

## Menu & Ordering
```
GET /           # Menu (online/offline/all modes)
GET /order      # Order form
POST /order     # Process order (cart: "1:2;5:1", coupon)
GET /orders/success/{order_id}
GET /orders/{id}          # Order tracking
GET /orders/track         # Track page
```

**Features**: Coupon validation, cart subtotal, inserts to `orders` table.

## Staff Dashboard
```
GET /staff                    # Dashboard
GET /staff/orders             # Pending online orders list
POST /staff/orders/{id}/confirm
POST /staff/orders/{id}/cancel
```

## Staff POS (Offline Mode)
```
GET /staff/counter     # Bill creation form
POST /staff/counter    # Creates completed offline order
                        ↓ Decrements inventory via RPC
GET /staff/invoices/{id}.pdf  # PDF invoice
```

**Flow**: Item list (`1:2;5:1`) + discount + payment → offline order → stock decrement → PDF.

## Inventory Management
```
GET /staff/inventory      # Status: OK/LOW/OUT
POST /staff/inventory/update  # Bulk stock updates
```

## Reports
```
GET /staff/reports        # Daily summary + today's orders
GET /staff/reports/today.csv  # CSV export
```

## Quick Start

### 1. Install
```bash
pip install -r requirements.txt
```

### 2. Configure `.env`
```
project_url=your_supabase_url
publishable_api_key=your_anon_key
staff_setup_code=your_secret_code
SESSION_SECRET_KEY=random_secret_here
SERVICE_ROLE_KEY=your_service_role_key
```

### 3. Run
```bash
uvicorn app.main:app --reload
```

### 4. Visit
| Feature | URL |
|---------|-----|
| Menu | http://localhost:8000/ |
| Order | http://localhost:8000/order |
| Track | http://localhost:8000/orders/track |
| Login | http://localhost:8000/login |
| Staff | http://localhost:8000/staff |

## Feature Walkthrough

### 🛒 Online Order
1. `/order` → Enter `1:2;5:1` + coupon code
2. Success → `/orders/success/123` + trackable `/orders/123`

### 💳 Staff POS (Offline)
1. Staff login → `/staff/register` (uses `staff_setup_code`)
2. `/staff/counter` → Items + discount → **PDF invoice generated**
3. Inventory auto-decrements via RPC (with read-modify-write fallback)

### 📋 Staff Processing
- `/staff/orders` → Pending online orders
- Confirm/Cancel buttons update order status

### 📊 Inventory & Reports
- `/staff/inventory` → Color-coded stock levels + inline edits
- `/staff/reports` → Daily totals + CSV export

## Notes
- **Compatible** with your existing `menu`, `orders`, `inventory`, `coupons` tables
- **Items stored** as serialized string (`"1:2;5:1"`) - JSONB migration ready
- **RLS policies needed**:
  - `menu`: public read ✅
  - `orders`: public track by ID, staff full access
  - `inventory`: staff read/write
- **PDFs**: xhtml2pdf from HTML templates
- **Sessions**: Signed cookies, staff role from `user_metadata`