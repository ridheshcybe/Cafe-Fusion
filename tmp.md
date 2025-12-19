## Application Overview
The [/app](cci:7://file:///Users/ridhesh/Downloads/tmp/app:0:0-0:0) directory defines a FastAPI web application for a café called Café Fusion. It covers menu browsing, online/offline order placement, session-based cart, inventory and reports management, plus user authentication (customers and staff). Supabase is used for persistence (tables: [menu](cci:7://file:///Users/ridhesh/Downloads/tmp/app/menu:0:0-0:0), [orders](cci:7://file:///Users/ridhesh/Downloads/tmp/app/orders:0:0-0:0), [inventory](cci:7://file:///Users/ridhesh/Downloads/tmp/app/inventory:0:0-0:0), `coupons`).

## Key Modules & Responsibilities
- [main.py](cci:7://file:///Users/ridhesh/Downloads/tmp/app/main.py:0:0-0:0): Instantiates FastAPI app, configures CORS, session middleware, mounts [/static](cci:7://file:///Users/ridhesh/Downloads/tmp/app/static:0:0-0:0), and registers routers (auth, menu, orders, inventory, reports).
- [config.py](cci:7://file:///Users/ridhesh/Downloads/tmp/app/config.py:0:0-0:0): Loads `.env` and exposes Supabase credentials plus session secret/staff setup code.
- [deps.py](cci:7://file:///Users/ridhesh/Downloads/tmp/app/deps.py:0:0-0:0): Provides [get_supabase()](cci:1://file:///Users/ridhesh/Downloads/tmp/app/deps.py:5:0-9:57) (cached client), [get_session_user](cci:1://file:///Users/ridhesh/Downloads/tmp/app/deps.py:12:0-13:81), and [is_staff](cci:1://file:///Users/ridhesh/Downloads/tmp/app/deps.py:15:0-18:26).

### Authentication ([auth/router.py](cci:7://file:///Users/ridhesh/Downloads/tmp/app/auth/router.py:0:0-0:0))
- Routes: `/login`, `/register`, `/staff/register`, `/logout`.
- Uses Supabase auth for sign-in/up; staff registration requires valid `STAFF_SETUP_CODE`.
- On login, stores minimal user dictionary in session (id, email, user_metadata with role).
- Templates under [templates/auth/](cci:7://file:///Users/ridhesh/Downloads/tmp/app/templates/auth:0:0-0:0) display forms and error messages.

### Menu (`menu/router.py` + [templates/menu/index.html](cci:7://file:///Users/ridhesh/Downloads/tmp/app/templates/menu/index.html:0:0-0:0))
- Routes: `/` and [/menu](cci:7://file:///Users/ridhesh/Downloads/tmp/app/menu:0:0-0:0) (filters by `mode` query: online / offline / all).
- Menu items fetched from Supabase [menu](cci:7://file:///Users/ridhesh/Downloads/tmp/app/menu:0:0-0:0) table and grouped by category.
- Each item shows name, price, badges, and an `Order` button.
- Order button posts to `/cart/add` (session cart flow); default quantity 1.

### Orders ([orders/router.py](cci:7://file:///Users/ridhesh/Downloads/tmp/app/orders/router.py:0:0-0:0) + templates)
#### Customer flow
1. `/cart/add` (POST): adds item to session cart. 
2. `/cart` (GET): renders [orders/cart_confirm.html](cci:7://file:///Users/ridhesh/Downloads/tmp/app/templates/orders/cart_confirm.html:0:0-0:0) to review items (with qty, line totals, subtotal) and collect customer info plus optional coupon. Offers “Continue Shopping” and “Clear Cart”.
3. `/cart/confirm` (POST): validates cart, applies coupon using [validate_coupon](cci:1://file:///Users/ridhesh/Downloads/tmp/app/services/orders.py:48:0-69:18), creates online order via [insert_order](cci:1://file:///Users/ridhesh/Downloads/tmp/app/services/orders.py:72:0-90:65), clears cart, redirects to `/orders/success/{order_id}`.
4. `/orders/success/{order_id}`: success page referencing order ID.

Earlier legacy flow `/order` (manual items text input) and `/orders/online` still exist (text-form submission).

#### Tracking
- `/orders/track` + `/orders/{id}`: display order status by ID with emoji status indicator via [orders/track.html](cci:7://file:///Users/ridhesh/Downloads/tmp/app/templates/orders/track.html:0:0-0:0).
- Uses Supabase [orders](cci:7://file:///Users/ridhesh/Downloads/tmp/app/orders:0:0-0:0) table.

#### Staff tools
- `/staff/orders`: pending online orders list with confirm/cancel buttons (updates order status).
- `/staff/orders/{order_id}/confirm` / `cancel`: update status.
- `/staff/counter`: offline POS form (`orders/counter.html`).
- `/staff/orders/offline`: handles offline submission (accepts `items` text spec, discount, payment mode, marks order completed). On success, decrements inventory for each item.
- `/staff/invoices/{order_id}.pdf`: generates PDF invoice via `services.invoice.render_invoice_pdf` and [orders.str_to_items](cci:1://file:///Users/ridhesh/Downloads/tmp/tmp_minified.py:46:0-49:73).

### Inventory ([inventory/router.py](cci:7://file:///Users/ridhesh/Downloads/tmp/app/inventory/router.py:0:0-0:0))
- `/staff/inventory` (GET): staff-only inventory list with product names, stock status (OK/LOW/OUT). Template `inventory/index.html`.
- `/staff/inventory/update` (POST): updates stock value and sets `last_restock`.

### Reports ([reports/router.py](cci:7://file:///Users/ridhesh/Downloads/tmp/app/reports/router.py:0:0-0:0))
- `/staff/reports`: interacts with services/reports for summary data (file not seen yet).

### Services
- [services/orders.py](cci:7://file:///Users/ridhesh/Downloads/tmp/app/services/orders.py:0:0-0:0): parse items text, compute totals from menu prices, validate coupon (with constraints), insert order (async, awaits Supabase). **Note**: final return currently tries to treat insert result incorrectly (calls `await` but interprets result incorrectly – needs fix).
- [services/inventory.py](cci:7://file:///Users/ridhesh/Downloads/tmp/app/services/inventory.py:0:0-0:0): handles inventory operations (decrement via RPC fallback, update stock, fetch inventory with names & status).
- [services/invoice.py](cci:7://file:///Users/ridhesh/Downloads/tmp/app/services/invoice.py:0:0-0:0): renders invoice PDF (not inspected, but part of offline order flow).
- [services/utils.py](cci:7://file:///Users/ridhesh/Downloads/tmp/app/services/utils.py:0:0-0:0): likely conversions (items<->string) used by orders.

### Templates
- [layout.html](cci:7://file:///Users/ridhesh/Downloads/tmp/app/templates/layout.html:0:0-0:0): global UI (Tailwind + DaisyUI), responsive navbar with staff dropdown, login/register states, mobile menu, JS for toggling and scroll effect. Track order page includes “Back to Menu” button.
- Subdirectories for auth, menu, orders, inventory, reports, staff.

### Static
- [/static/styles.css](cci:7://file:///Users/ridhesh/Downloads/tmp/app/static/styles.css:0:0-0:0): presumably styling (currently removed by user, needs re-check).

## Required Setup
- `.env` with Supabase credentials (`project_url`, `publishable_api_key`, `SERVICE_ROLE_KEY`, optional `staff_setup_code`, `SESSION_SECRET_KEY`).
- Supabase tables: [menu](cci:7://file:///Users/ridhesh/Downloads/tmp/app/menu:0:0-0:0), [orders](cci:7://file:///Users/ridhesh/Downloads/tmp/app/orders:0:0-0:0), [inventory](cci:7://file:///Users/ridhesh/Downloads/tmp/app/inventory:0:0-0:0), `coupons` and optional RPC for decrement inventory.
- Session middleware secret.
- PDF invoice generation relies on from `services.invoice`.

## Feature Requirements for Full Replica
1. **Authentication**
   - Customer registration/login via Supabase.
   - Staff registration secured by setup code.
   - Session management for storing user data and role.
   - Logout clears session.

2. **Menu Browsing**
   - Fetch items with categories, price, availability flags.
   - Filtering by mode (online/offline/all).
   - Order button posting to session-based cart.

3. **Session Cart & Order Confirmation**
   - Session dict storing item_id → qty.
  - `/cart` view listing items with quantities and totals.
   - Customer info form (name, phone).
   - Optional coupon validation (discount percent, min order, max discount).
   - Placing online order writes to Supabase via [insert_order](cci:1://file:///Users/ridhesh/Downloads/tmp/app/services/orders.py:72:0-90:65) and clears cart.
   - Cart clearing endpoint.
   - Success page referencing order ID.

4. **Legacy Manual Online Order Form** (optional, but exists).
   - Form accepting items string `item_id:qty` pairs.
   - Handles validation and coupon.

5. **Order Tracking**
   - Search by order ID; shows status with emoji mapping; handles errors.
   - [orders](cci:7://file:///Users/ridhesh/Downloads/tmp/app/orders:0:0-0:0) table must store status values: pending, confirmed, etc.

6. **Staff Operations**
   - Access secured by session role check.
   - Pending online orders list with confirm/cancel actions updating status.
   - Offline POS page to create orders (with manual items text, discount, payment mode).
   - Invoice PDF generation for offline orders (ensures items string representation convertible by [str_to_items](cci:1://file:///Users/ridhesh/Downloads/tmp/tmp_minified.py:46:0-49:73)).
   - Inventory management (list / update) using [inventory](cci:7://file:///Users/ridhesh/Downloads/tmp/app/inventory:0:0-0:0) table.
   - Reports (requires reading [reports/router.py](cci:7://file:///Users/ridhesh/Downloads/tmp/app/reports/router.py:0:0-0:0) for specifics; likely uses orders data for summaries).

7. **Inventory Integration**
   - Decrement inventory when offline order placed (maybe also for online? currently only offline).
   - `decrement_inventory` RPC or fallback logic.

8. **UI/UX**
   - Modern responsive navbar (Tailwind + DaisyUI).
   - Track order page with “Back to Menu” button.
   - Confirm order page layout with table and forms.
   - Auth pages storing/ displaying error messages.
   - Styling via static CSS (confirm actual content of [styles.css](cci:7://file:///Users/ridhesh/Downloads/tmp/app/static/styles.css:0:0-0:0)).

9. **Session & Security**
   - Ensure session secret set.
   - Setup code for staff to prevent unauthorized access.
   - Input validation (quantities, names).

10. **Supabase Integration**
    - All DB interactions use Supabase client from [deps.get_supabase](cci:1://file:///Users/ridhesh/Downloads/tmp/app/deps.py:5:0-9:57).
    - Need proper Supabase configuration.

11. **Invoice Generation**
    - `services.invoice.render_invoice_pdf` uses a PDF library (need to inspect file for dependencies).
    - Offline orders redirect to generated PDF.

12. **Reports Module**
    - Understand [reports/router.py](cci:7://file:///Users/ridhesh/Downloads/tmp/app/reports/router.py:0:0-0:0) and templates to reproduce.

## Observed Issues / Gaps
- [services/orders.insert_order](cci:1://file:///Users/ridhesh/Downloads/tmp/app/services/orders.py:72:0-90:65) currently mis-parses Supabase response (tries to treat `result.data[0]["order_id"]` as data then use `.data`). Should likely just `return int(result.data[0]["order_id"])`.
- Navbar cart icon removed; optionally add cart badge to show item count.
- [styles.css](cci:7://file:///Users/ridhesh/Downloads/tmp/app/static/styles.css:0:0-0:0) may be empty after user deletion; ensure necessary styling is present.
- Confirm [reports/router.py](cci:7://file:///Users/ridhesh/Downloads/tmp/app/reports/router.py:0:0-0:0) and templates for completeness (not yet read).
- Build tests or confirm flows to ensure cart, coupon, etc. work.

## Recommend Next Steps
1. Fix [insert_order](cci:1://file:///Users/ridhesh/Downloads/tmp/app/services/orders.py:72:0-90:65) return logic.
2. Validate new cart flow end-to-end (cart count, required fields, multiple items).
3. Ensure [styles.css](cci:7://file:///Users/ridhesh/Downloads/tmp/app/static/styles.css:0:0-0:0) contains necessary styles.
4. Review [reports](cci:7://file:///Users/ridhesh/Downloads/tmp/app/reports:0:0-0:0) module to detail reporting features.
5. Document Supabase schema expectations (columns, types).
6. Add tests or manual QA scripts for major flows (login, menu, order, staff ops).

