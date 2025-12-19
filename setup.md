# Prerequisites
- Python 3.11+ recommended
- Supabase project with tables: [menu](cci:1://file:///Users/ridhesh/Downloads/tmp/app/menu/router.py:11:0-35:108), `orders`, `inventory`, `coupons` and RPC `decrement_inventory`

# 1) Create and activate a virtual environment
- macOS/Linux:
  - python3 -m venv .venv
  - source .venv/bin/activate
- Windows (PowerShell):
  - python -m venv .venv
  - .\.venv\Scripts\Activate.ps1

# 2) Install dependencies
- pip install -r requirements.txt

# 3) Configure environment variables
Edit your .env at the repo root (you already have most of these):
- project_url=YOUR_SUPABASE_URL
- publishable_api_key=YOUR_SUPABASE_ANON_KEY
- staff_setup_code=YOUR_SECRET_SETUP_CODE
- SESSION_SECRET_KEY=some_random_long_secret
- SERVICE_ROLE_KEY=YOUR_SERVICE_ROLE_KEY (optional; for later server-only actions)

Notes:
- The app reads `project_url`, `publishable_api_key`, `staff_setup_code` for basic functionality.
- `SERVICE_ROLE_KEY` can be left unset initially; only needed if you later tighten RLS and run server-side privileged tasks. (please don't use this for now)
- Do NOT expose `SERVICE_ROLE_KEY` in client-facing code.

# 4) Ensure Supabase schema and RPC
Tables expected (aligned with your CLI):
- menu: item_id, name, category, price, available_online, available_offline, online_exclusive, offline_only
- orders: order_id, order_type, customer_name, customer_contact, items, total_amount, discount_amount, payment_mode, status, order_date
- inventory: item_id, current_stock, min_stock, last_restock
- coupons: coupon_code, discount_percent, max_discount, min_order, valid_till
RPC:
- decrement_inventory(p_item_id int, p_qty int)

If RLS is ON, ensure policies allow:
- menu: public SELECT
- coupons: public or server route SELECT (safe read)
- orders: public SELECT by order_id for tracking; staff full SELECT/UPDATE
- inventory: staff SELECT/UPDATE only

# 5) Run the development server
- uvicorn app.main:app --reload
- Default: http://localhost:8000

# 6) Try the app
- Home/Menu: http://localhost:8000/
- Order page: http://localhost:8000/order
  - Items input format: itemId:qty;itemId:qty (e.g., 1:2;5:1)
  - Optional coupon applies discount based on `coupons` table
- Order success: redirects to /orders/success/{order_id}
- Track an order: http://localhost:8000/orders/track (or directly /orders/{id})
- Auth:
  - Login: http://localhost:8000/login
  - Register: http://localhost:8000/register
  - Staff register: http://localhost:8000/staff/register (uses `staff_setup_code`)
- Staff dashboard: http://localhost:8000/staff
  - Pending online orders: /staff/orders (Confirm/Cancel)
  - Offline POS counter: /staff/counter (creates bill, decrements inventory, opens PDF)
  - Inventory: /staff/inventory (status and update stock)
  - Reports: /staff/reports (today summary + CSV at /staff/reports/today.csv)

# 7) PDF invoices
- Invoices are generated as PDFs using xhtml2pdf (pure Python).
- After an offline order, the app redirects to /staff/invoices/{order_id}.pdf.
- If fonts or rendering look off, adjust styles in app/services/invoice.py.

# 8) Common issues and fixes
- “Supabase not configured”: confirm .env keys and that uvicorn runs from the repo root so `load_dotenv()` can find .env.
- “No menu items found”: seed your menu table or switch mode `/menu?mode=all`.
- Coupon not applied: ensure `valid_till >= today` and `subtotal >= min_order`.
- RLS errors: relax policies while developing, then tighten. For staff routes, ensure registering staff sets `user_metadata.role='staff'`.

# 9) Production run (optional)
- Install a prod server:
  - pip install gunicorn
- Run (example):
  - gunicorn -k uvicorn.workers.UvicornWorker -w 2 app.main:app -b 0.0.0.0:8000
- Put behind Nginx or a PaaS (Railway, Fly.io, etc.). Set environment variables in your hosting dashboard. Never expose `SERVICE_ROLE_KEY`.