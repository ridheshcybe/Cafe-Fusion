"""CAFE HYBRID MANAGEMENT SYSTEM - CBSE Class 12 | Supabase + File Handling"""
import csv, os
from datetime import datetime
from dotenv import load_dotenv
import getpass
from supabase import create_client, Client


_SB = None
def get_supabase():
    global _SB
    if _SB is not None:
        return _SB
    load_dotenv()
    url = os.getenv("project_url")
    key = os.getenv("publishable_api_key")
    if not url or not key:
        print("❌ Supabase not configured!")
        return None
    _SB = create_client(url, key)
    return _SB


def save_invoice(order_id, customer, items, total, discount, payment):
    filename = f"invoice_{order_id}.txt"
    try:
        with open(filename, 'w') as f:
            sep, line = "="*60, "-"*60
            f.write(f"{sep}\n{'CAFÉ FUSION':^60}\n{'HYBRID MANAGEMENT SYSTEM':^60}\n{sep}\n")
            f.write(f"Order ID: {order_id}\nDate: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"Customer: {customer}\nPayment: {payment}\n{line}\n")
            f.write(f"{'Item':<30} {'Qty':<10} {'Price':<10} {'Total':<10}\n{line}\n")
            for item in items:
                f.write(f"{item['name'][:29]:<30} {item['qty']:<10} ₹{item['price']:<9} ₹{item['price']*item['qty']:<9}\n")
            f.write(f"{line}\n")
            if discount > 0: f.write(f"Discount: ₹{discount:.2f}\n")
            f.write(f"TOTAL: ₹{total:.2f}\n{sep}\n{'Thank you! Visit again!':^60}\n{sep}\n")
        print(f"📄 Invoice saved: {filename}")
        return filename
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def items_to_str(items):
    return ";".join([f"{i['id']}:{i['name']}:{i['price']}:{i['qty']}" for i in items])

def str_to_items(s):
    if not s: return []
    return [{'id': int(p[0]), 'name': p[1], 'price': float(p[2]), 'qty': int(p[3])} 
            for p in [e.split(":") for e in s.split(";")] if len(p) == 4]

def auth_staff(staff_id, password):
    sb = get_supabase()
    if not sb: return False
    try:
        # Treat staff_id as email for Supabase Auth
        res = sb.auth.sign_in_with_password({
            "email": staff_id,
            "password": password
        })
        user = getattr(res, "user", None)
        if not user:
            return False
        meta = getattr(user, "user_metadata", {}) or {}
        return (meta.get("role") == "staff")
    except Exception:
        return False

def current_user():
    sb = get_supabase()
    if not sb: return None
    try:
        res = sb.auth.get_user()
        return getattr(res, "user", None)
    except Exception:
        return None

def login_user():
    sb = get_supabase()
    if not sb: return False
    email = input("Email: ").strip()
    password = getpass.getpass("Password: ")
    try:
        res = sb.auth.sign_in_with_password({"email": email, "password": password})
        user = getattr(res, "user", None)
        ok = user is not None
        print("✅ Logged in!" if ok else "❌ Login failed!")
        if ok:
            meta = getattr(user, "user_metadata", {}) or {}
            if meta.get("role") == "staff":
                print("ℹ️  Staff account logged in. Use Staff Mode for counter operations.")
        return ok
    except Exception:
        print("❌ Login error!")
        return False

def register_user():
    sb = get_supabase()
    if not sb: return False
    print("\n📝 Register New Account")
    email = input("Email: ").strip()
    password = getpass.getpass("Password (min 6 chars): ")
    name = input("Name: ").strip()
    phone = input("Phone: ").strip()
    try:
        res = sb.auth.sign_up({
            "email": email,
            "password": password,
            "options": {"data": {"role": "user", "name": name, "phone": phone}}
        })
        user = getattr(res, "user", None)
        if user:
            print("✅ Registered! Check email if confirmation is required.")
            return True
        print("❌ Registration failed!")
        return False
    except Exception:
        print("❌ Registration error!")
        return False

def logout_user():
    sb = get_supabase()
    if not sb: return
    try:
        sb.auth.sign_out()
        print("✅ Logged out")
    except Exception:
        print("❌ Logout error!")

def register_staff():
    sb = get_supabase()
    if not sb: return False
    print("\n🛠️  Staff Registration")
    setup_code = os.getenv("staff_setup_code")
    provided = getpass.getpass("Setup code: ")
    if not setup_code:
        print("❌ staff_setup_code not set in .env")
        return False
    if provided != setup_code:
        print("❌ Invalid setup code!")
        return False
    email = input("Staff Email: ").strip()
    password = getpass.getpass("Password (min 6 chars): ")
    name = input("Name: ").strip()
    try:
        res = sb.auth.sign_up({
            "email": email,
            "password": password,
            "options": {"data": {"role": "staff", "name": name}}
        })
        user = getattr(res, "user", None)
        if user:
            print("✅ Staff registered! Check email if confirmation is required.")
            return True
        print("❌ Registration failed!")
        return False
    except Exception:
        print("❌ Registration error!")
        return False

def display_menu(mode="all"):
    sb = get_supabase()
    items = []
    if not sb:
        return items
    try:
        q = sb.table("menu").select("*")
        if mode == "online":
            q = q.eq("available_online", True)
        elif mode == "offline":
            q = q.eq("available_offline", True)
        q = q.order("category").order("item_id")
        res = q.execute()
        records = getattr(res, "data", []) or []
        items = [(
            r.get("item_id"),
            r.get("name"),
            r.get("category"),
            float(r.get("price", 0)),
            bool(r.get("available_online", False)),
            bool(r.get("available_offline", False)),
            bool(r.get("online_exclusive", False)),
            bool(r.get("offline_only", False)),
        ) for r in records]
    except Exception:
        items = []
    
    print(f"\n{'='*70}\n{'MENU':^70}\n{'='*70}")
    cat = ""
    for item in items:
        if item[2] != cat:
            cat = item[2]
            print(f"\n{cat.upper():^70}\n{'-'*70}")
        tags = " [ONLINE ONLY]" if item[6] else " [OFFLINE ONLY]" if item[7] else ""
        print(f"{item[0]:3}. {item[1]:30} ₹{item[3]:7.2f}{tags}")
    print("="*70)
    return items

def create_bill():
    print(f"\n{'='*50}\nCREATE OFFLINE BILL\n{'='*50}")
    items = display_menu("offline")
    if not items: return print("No items available!")
    
    cart = []
    while True:
        try:
            item_id = int(input("\nItem ID (0 to finish): "))
            if item_id == 0: break
            selected = next((i for i in items if i[0] == item_id), None)
            if not selected: print("❌ Invalid ID!"); continue
            qty = int(input("Quantity: "))
            if qty <= 0: print("❌ Invalid quantity!"); continue
            cart.append({'id': selected[0], 'name': selected[1], 'price': float(selected[3]), 'qty': qty})
            print(f"✅ Added {selected[1]} x{qty}")
        except ValueError: print("❌ Invalid input!")
    
    if not cart: return print("Cart empty!")
    
    subtotal = sum(i['price'] * i['qty'] for i in cart)
    discount = 0
    if input(f"\nApply discount? (Total: ₹{subtotal:.2f}) (y/n): ").lower() == 'y':
        try:
            discount = float(input("Discount amount: ₹"))
            if discount > subtotal: print("❌ Invalid!"); discount = 0
        except ValueError: print("❌ Invalid!")
    
    total = subtotal - discount
    print("\n💳 PAYMENT: 1.Cash 2.Card 3.UPI")
    pm = ['cash', 'card', 'upi'][int(input("Select: "))-1] if input("Select: ") in ['1','2','3'] else 'cash'
    customer = input("\nCustomer name (Enter for 'Walk-in'): ").strip() or "Walk-in Customer"
    
    sb = get_supabase()
    if not sb: 
        print("❌ Supabase not configured.")
        return
    order_id = None
    try:
        ins = sb.table("orders").insert({
            "order_type": "offline",
            "customer_name": customer,
            "items": items_to_str(cart),
            "total_amount": float(total),
            "status": "completed",
            "payment_mode": pm,
            "discount_amount": float(discount),
        }).select("order_id").execute()
        data = getattr(ins, "data", []) or []
        order_id = data[0].get("order_id") if data else None
        for it in cart:
            try:
                sb.rpc("decrement_inventory", {"p_item_id": it['id'], "p_qty": it['qty']}).execute()
            except Exception:
                # Fallback: read-modify-write to avoid negatives
                try:
                    cur = sb.table("inventory").select("current_stock").eq("item_id", it['id']).limit(1).execute()
                    rows = getattr(cur, "data", []) or []
                    current = int((rows[0] or {}).get("current_stock", 0)) if rows else 0
                    new_stock = max(current - int(it['qty']), 0)
                    sb.table("inventory").update({"current_stock": new_stock}).eq("item_id", it['id']).execute()
                except Exception:
                    pass
    except Exception:
        print("❌ Failed to create order in Supabase.")
        return
    
    save_invoice(order_id, customer, cart, total, discount, pm)
    print(f"\n{'='*50}\n✅ BILL CREATED!\n{'='*50}\nOrder ID: {order_id}\nCustomer: {customer}\nTotal: ₹{total:.2f}\nPayment: {pm}\n{'='*50}")

def place_order():
    print(f"\n{'='*50}\nPLACE ONLINE ORDER\n{'='*50}")
    name = input("\n👤 Your name: ").strip()
    phone = input("Phone: ").strip()
    if not name or not phone: return print("❌ Name and phone required!")
    
    items = display_menu("online")
    if not items: return print("No items available!")
    
    cart = []
    while True:
        try:
            item_id = int(input("\nItem ID (0 to finish): "))
            if item_id == 0: break
            selected = next((i for i in items if i[0] == item_id), None)
            if not selected: print("❌ Invalid!"); continue
            qty = int(input("Quantity: "))
            if qty <= 0: print("❌ Invalid!"); continue
            cart.append({'id': selected[0], 'name': selected[1], 'price': float(selected[3]), 'qty': qty})
            print(f"✅ Added {selected[1]} x{qty}")
        except ValueError: print("❌ Invalid!")
    
    if not cart: return print("Cart empty!")
    
    subtotal = sum(i['price'] * i['qty'] for i in cart)
    discount = 0
    coupon = input("\n💳 Coupon code (Enter to skip): ").strip().upper()
    if coupon:
        sb = get_supabase()
        c = None
        if sb:
            try:
                today = datetime.now().strftime('%Y-%m-%d')
                res = sb.table("coupons").select("discount_percent,max_discount,min_order,valid_till").eq("coupon_code", coupon).gte("valid_till", today).limit(1).execute()
                rows = getattr(res, "data", []) or []
                if rows:
                    c = (rows[0].get("discount_percent"), rows[0].get("max_discount"), rows[0].get("min_order"))
            except Exception:
                c = None
        if c and subtotal >= c[2]:
            discount = min((subtotal * c[0]) / 100, c[1])
            print(f"✅ Discount: ₹{discount:.2f}")
        else: print("❌ Invalid coupon!")
    
    total = subtotal - discount
    print(f"\n{'-'*50}\nORDER SUMMARY\n{'-'*50}")
    for i in cart: print(f"{i['name']:30} x{i['qty']:3} ₹{i['price']*i['qty']:8.2f}")
    print(f"{'-'*50}")
    if discount > 0: print(f"Discount: ₹{discount:.2f}")
    print(f"TOTAL: ₹{total:.2f}\n{'-'*50}")
    
    if input("\nConfirm? (y/n): ").lower() != 'y': return print("Cancelled!")
    
    sb = get_supabase()
    if not sb:
        print("❌ Supabase not configured.")
        return
    order_id = None
    try:
        ins = sb.table("orders").insert({
            "order_type": "online",
            "customer_name": name,
            "customer_contact": phone,
            "items": items_to_str(cart),
            "total_amount": float(total),
            "status": "pending",
            "discount_amount": float(discount),
            "payment_mode": "online",
        }).select("order_id").execute()
        data = getattr(ins, "data", []) or []
        order_id = data[0].get("order_id") if data else None
    except Exception:
        print("❌ Failed to place order in Supabase.")
        return
    
    save_online_backup({'order_id': order_id, 'customer': name, 'phone': phone, 'items': cart, 'total': total, 'discount': discount, 'timestamp': str(datetime.now()), 'status': 'pending'})
    print(f"\n{'='*50}\n✅ ORDER PLACED!\n{'='*50}\nOrder ID: {order_id}\nCustomer: {name}\nPhone: {phone}\nTotal: ₹{total:.2f}\nStatus: Pending\n{'='*50}\n📱 Track using Order ID\n{'='*50}")

def track_order():
    print(f"\n{'='*50}\nTRACK ORDER\n{'='*50}")
    try: order_id = int(input("Order ID: "))
    except ValueError: return print("❌ Invalid ID!")
    
    sb = get_supabase()
    if not sb: return
    try:
        res = sb.table("orders").select("order_id, customer_name, order_date, total_amount, status, items").eq("order_id", order_id).eq("order_type", "online").limit(1).execute()
        rows = getattr(res, "data", []) or []
        if not rows: return print("❌ Not found!")
        o = rows[0]
        items = str_to_items(o.get("items"))
        print(f"\n{'='*50}\nORDER STATUS\n{'='*50}\nID: {o.get('order_id')}\nCustomer: {o.get('customer_name')}\nTime: {o.get('order_date')}\nTotal: ₹{float(o.get('total_amount') or 0):.2f}")
        if items:
            print("\nItems:")
            for i in items: print(f"  - {i['name']} x{i['qty']}")
        status = o.get('status') or ''
        status_emoji = {'pending': '⏳', 'confirmed': '✅', 'preparing': '👨‍🍳', 'ready': '📦', 'completed': '🎉', 'cancelled': '❌'}.get(status, '📝')
        print(f"\nStatus: {status_emoji} {status.upper()}\n{'='*50}")
    except Exception:
        print("❌ Failed to fetch order.")

def process_orders():
    print(f"\n{'='*50}\nPROCESS ONLINE ORDERS\n{'='*50}")
    sb = get_supabase()
    if not sb: return
    try:
        res = sb.table("orders").select("order_id, customer_name, customer_contact, items, total_amount").eq("order_type", "online").eq("status", "pending").order("order_date").execute()
        orders = getattr(res, "data", []) or []
        if not orders:
            print("No pending orders!")
            return
        print(f"\nFound {len(orders)} pending order(s):\n{'-'*50}")
        for o in orders:
            items = str_to_items(o.get("items"))
            print(f"\n📦 Order #{o.get('order_id')}\n   Customer: {o.get('customer_name')} ({o.get('customer_contact')})\n   Total: ₹{o.get('total_amount')}\n   Items:")
            for i in items: print(f"     - {i['name']} x{i['qty']}")
            action = input(f"\nProcess #{o.get('order_id')}? (c=confirm, s=skip, x=cancel): ").lower()
            if action == 'c':
                sb.table("orders").update({"status": "confirmed"}).eq("order_id", o.get('order_id')).execute()
                print(f"✅ Order #{o.get('order_id')} confirmed!")
            elif action == 'x':
                sb.table("orders").update({"status": "cancelled"}).eq("order_id", o.get('order_id')).execute()
                print(f"❌ Order #{o.get('order_id')} cancelled!")
            else: print(f"⏸️  Skipped")
        print("\n✅ Processing complete!")
    except Exception:
        print("❌ Failed to process orders.")
    print("\n✅ Processing complete!")

def view_orders():
    sb = get_supabase()
    if not sb: return
    try:
        start = datetime.now().strftime('%Y-%m-%d') + " 00:00:00"
        end = datetime.now().strftime('%Y-%m-%d') + " 23:59:59"
        res = sb.table("orders").select("order_id, order_type, customer_name, total_amount, payment_mode, status, order_date").gte("order_date", start).lte("order_date", end).order("order_date", desc=True).execute()
        orders = getattr(res, "data", []) or []
        if not orders: return print("No orders today!")
        sep = "="*80
        line = "-"*80
        print(f"\n{sep}\n{'TODAY ORDERS':^80}\n{sep}\n{'ID':<6} {'Type':<8} {'Customer':<20} {'Amount':<10} {'Payment':<8} {'Status':<12} {'Time':<10}\n{line}")
        total = 0
        for o in orders:
            print(f"{int(o.get('order_id')):<6} {o.get('order_type'):<8} {str(o.get('customer_name'))[:18]:<20} ₹{float(o.get('total_amount') or 0):<8.2f} {str(o.get('payment_mode') or ''):<8} {str(o.get('status') or ''):<12} {str(o.get('order_date') or '')[11:16]:<10}")
            total += float(o.get('total_amount') or 0)
        print(f"{line}\nTotal Orders: {len(orders)}\nTotal Revenue: ₹{total:.2f}\n{sep}")
    except Exception:
        print("❌ Failed to fetch today's orders.")

def check_inventory():
    sb = get_supabase()
    if not sb: return
    try:
        mres = sb.table("menu").select("item_id,name").execute()
        ires = sb.table("inventory").select("item_id,current_stock,min_stock").order("current_stock").execute()
        menu = {m.get('item_id'): m.get('name') for m in (getattr(mres, 'data', []) or [])}
        inv_rows = getattr(ires, 'data', []) or []
        print(f"\n{'='*70}\n{'INVENTORY STATUS':^70}\n{'='*70}\n{'ID':<4} {'Item':<30} {'Current':<10} {'Min':<10} {'Status':<15}\n{'-'*70}")
        low = []
        for r in inv_rows:
            item_id = r.get('item_id')
            name = str(menu.get(item_id, 'Unknown'))
            current = int(r.get('current_stock') or 0)
            minimum = int(r.get('min_stock') or 0)
            status = 'OUT' if current == 0 else ('LOW' if current <= minimum else 'OK')
            print(f"{item_id:<4} {name[:29]:<30} {current:<10} {minimum:<10} {status:<15}")
            if status in ['LOW','OUT']: low.append(name)
        print("="*70)
        if low: print("\n⚠️  ATTENTION:"); [print(f"   - {i}") for i in low]
        else: print("\n✅ All items stocked!")
    except Exception:
        print("❌ Failed to fetch inventory.")

def update_stock():
    print(f"\n{'='*50}\nUPDATE STOCK\n{'='*50}")
    check_inventory()
    try:
        item_id = int(input("\nItem ID: "))
        new_stock = int(input("New stock: "))
        sb = get_supabase()
        if not sb: return
        m = sb.table("menu").select("name").eq("item_id", item_id).limit(1).execute()
        rows = getattr(m, 'data', []) or []
        if not rows:
            print("❌ Not found!")
            return
        sb.table("inventory").update({"current_stock": new_stock, "last_restock": datetime.now().strftime('%Y-%m-%d')}).eq("item_id", item_id).execute()
        print(f"✅ Stock updated for {rows[0].get('name')}")
    except ValueError: print("❌ Invalid input!")

def export_csv():
    sb = get_supabase()
    if not sb: return
    today = datetime.now().strftime('%Y-%m-%d')
    start = today + " 00:00:00"
    end = today + " 23:59:59"
    try:
        res = sb.table("orders").select("order_id, order_type, customer_name, total_amount, payment_mode, order_date").gte("order_date", start).lte("order_date", end).order("order_date").execute()
        orders = getattr(res, 'data', []) or []
        if not orders: return print("No orders today!")
        filename = f"daily_report_{today}.csv"
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Order ID', 'Type', 'Customer', 'Amount', 'Payment', 'Time'])
            total = 0
            for o in orders:
                writer.writerow([o.get('order_id'), o.get('order_type'), o.get('customer_name'), o.get('total_amount'), o.get('payment_mode'), o.get('order_date')])
                total += float(o.get('total_amount') or 0)
            writer.writerow([])
            writer.writerow(['Total Orders:', len(orders), '', '', '', ''])
            writer.writerow(['Total Revenue:', f'₹{total:.2f}', '', '', '', ''])
        print(f"📊 Report exported: {filename}\n📈 Orders: {len(orders)}\n💰 Revenue: ₹{total:.2f}")
    except Exception as e:
        print(f"❌ Error: {e}")

def save_online_backup(order_data):
    try:
        with open("online_orders_backup.txt", 'a') as f:
            f.write(f"{'='*50}\nOrder ID: {order_data['order_id']}\nCustomer: {order_data['customer']}\nPhone: {order_data['phone']}\nTotal: ₹{order_data['total']:.2f}\nTime: {order_data['timestamp']}\nStatus: {order_data['status']}\nItems:\n")
            for i in order_data['items']:
                f.write(f"  - {i['name']} x{i['qty']} @ ₹{i['price']}\n")
            f.write(f"{'='*50}\n\n")
        print(f"💾 Backed up to online_orders_backup.txt")
    except Exception as e:
        print(f"❌ Error: {e}")

def daily_report():
    sb = get_supabase()
    if not sb: return
    today = datetime.now().strftime('%Y-%m-%d')
    start = today + " 00:00:00"
    end = today + " 23:59:59"
    try:
        res = sb.table("orders").select("order_id, order_type, total_amount").gte("order_date", start).lte("order_date", end).execute()
        orders = getattr(res, 'data', []) or []
        if not orders: return print("No orders today!")
        total_orders = len(orders)
        revenue = sum(float(o.get('total_amount') or 0) for o in orders)
        online = sum(1 for o in orders if o.get('order_type') == 'online')
        offline = sum(1 for o in orders if o.get('order_type') == 'offline')
        avg = (revenue / total_orders) if total_orders else 0
        print(f"\n{'='*50}\nDAILY SUMMARY\n{'='*50}\nDate: {today}\nTotal Orders: {total_orders}\nOnline: {online}\nOffline: {offline}\nRevenue: ₹{revenue:.2f}\nAvg Order: ₹{avg:.2f}\n{'='*50}")
        export_csv()
    except Exception:
        print("❌ Failed to generate report.")

def offline_mode():
    print(f"\n{'='*70}\n{'OFFLINE COUNTER MODE':^70}\n{'='*70}")
    while True:
        print("\n1. 🔐 Staff Login\n2. 👤 Register Staff\n3. 🏠 Back")
        c = input("\nSelect (1-3): ")
        if c == '2':
            register_staff()
            continue
        elif c == '3':
            return
        elif c != '1':
            print("❌ Invalid!")
            continue
        staff_id = input("Staff Email: ")
        password = getpass.getpass("Password: ")
        if not auth_staff(staff_id, password):
            print("❌ Auth failed!")
            continue
        print(f"\n✅ Welcome, {staff_id}!")
        while True:
            print(f"\n{'-'*50}\nOFFLINE MENU\n{'-'*50}\n1. 🧾 New Bill\n2. 📋 Today's Orders\n3. 📦 Inventory\n4. 🔄 Update Stock\n5. 📊 Daily Report\n6. 📱 Process Online Orders\n7. 🚪 Logout to Staff Menu")
            choice = input("\nChoice (1-7): ")
            if choice == '1': create_bill()
            elif choice == '2': view_orders()
            elif choice == '3': check_inventory()
            elif choice == '4': update_stock()
            elif choice == '5': daily_report()
            elif choice == '6': process_orders()
            elif choice == '7': break
            else: print("❌ Invalid!")

def online_mode():
    print(f"\n{'='*70}\n{'ONLINE ORDERING PORTAL':^70}\n{'='*70}")
    while True:
        u = current_user()
        status = f"Logged in as: {getattr(u, 'email', '')}" if u else "Not logged in"
        print(f"\n{status}")
        print("\n1. 🆕 New Order\n2. 🔍 Track Order\n3. 📋 View Menu\n4. 🔑 Login\n5. 📝 Register\n6. 🚪 Logout\n7. 🏠 Back")
        choice = input("\nChoice (1-7): ")
        if choice == '1':
            if not current_user():
                print("❌ Please login first.")
            else:
                place_order()
        elif choice == '2':
            track_order()
        elif choice == '3':
            display_menu("online"); input("\nPress Enter...")
        elif choice == '4':
            login_user()
        elif choice == '5':
            register_user()
        elif choice == '6':
            logout_user()
        elif choice == '7':
            break
        else:
            print("❌ Invalid!")

def main_menu():
    while True:
        print(f"\n{'='*70}\n{'CAFÉ FUSION - HYBRID SYSTEM':^70}\n{'='*70}\n\n1. 🔒 STAFF MODE (Offline Counter)\n2. 🛒 CUSTOMER MODE (Online Ordering)\n3. 📊 SYSTEM REPORTS\n4. ❌ EXIT\n{'='*70}")
        choice = input("\nSelect (1-4): ")
        if choice == '1': offline_mode()
        elif choice == '2': online_mode()
        elif choice == '3':
            while True:
                print(f"\n{'='*50}\nREPORTS\n{'='*50}\n1. 📈 Today's Orders\n2. 📦 Inventory\n3. 💰 Revenue\n4. 🏠 Back")
                c = input("\nChoice (1-4): ")
                if c == '1': view_orders()
                elif c == '2': check_inventory()
                elif c == '3': daily_report()
                elif c == '4': break
                else: print("❌ Invalid!")
        elif choice == '4':
            print(f"\n{'='*70}\nThank you for using Café Fusion!\nCBSE Class 12 Computer Science Project\n{'='*70}")
            break
        else: print("❌ Invalid!")

def main():
    print(f"\n{'='*80}\n{'WELCOME TO CAFÉ FUSION':^80}\n{'Hybrid Management System v1.0':^80}\n{'='*80}\nCBSE Class 12 | Python + Supabase + File Handling\n{'='*80}")
    print("\n🔧 Initializing...")
    if not get_supabase(): return print("❌ Supabase not configured!")
    print("✅ Connected to Supabase!")
    main_menu()

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: print("\n⚠️  Interrupted!")
    except Exception as e: print(f"\n❌ Error: {e}")
    finally: print("\nThank you for using Café Fusion! Goodbye! 👋")
