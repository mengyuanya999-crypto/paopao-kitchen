from supabase import create_client
import streamlit as st
from datetime import datetime

# ===== Supabase =====
SUPABASE_URL = "https://pujodijixpuaqkfvcmwv.supabase.co"
SUPABASE_KEY = "sb_publishable_dD3ckwu1w_dM8h9sT7mIlw_LaKz0IPl"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

ADMIN_USER = "Monica"

# ===== 登录状态 =====
if "user" not in st.session_state:
    st.session_state.user = None

# ================= 登录 =================
if st.session_state.user is None:
    st.title("🍳 家庭点餐")

    u = st.text_input("用户名")
    p = st.text_input("密码", type="password")

    if st.button("登录"):
        res = supabase.table("users").select("*").eq("username", u).execute()
        if res.data and res.data[0]["password"] == p:
            st.session_state.user = u
            st.rerun()
        else:
            st.error("登录失败")

    st.stop()

# ================= 登录后 =================
is_admin = st.session_state.user == ADMIN_USER

st.sidebar.write(f"👤 {st.session_state.user}")

if st.sidebar.button("退出"):
    st.session_state.user = None
    st.rerun()

if is_admin:
    page = st.sidebar.selectbox("页面", ["点菜", "今日菜单", "后台"])
else:
    page = st.sidebar.selectbox("页面", ["点菜"])

# ===== 购物车 =====
if "cart" not in st.session_state:
    st.session_state.cart = {}

# ================= 点菜 =================
if page == "点菜":

    st.title("🍳 今天想吃什么")

    menu = supabase.table("menu").select("*").execute().data

    meal_time = st.selectbox("选择用餐时间", ["早餐", "午餐", "晚餐"])
    note = st.text_input("备注（可选）")

    for item in menu:
        col1, col2 = st.columns([4,1])

        with col1:
            st.write(f"{item['name']} ¥{item['price']}")
            if item.get("description"):
                st.caption(item["description"])

        with col2:
            if st.button("➕", key=item["id"]):
                if item["id"] in st.session_state.cart:
                    st.session_state.cart[item["id"]]["qty"] += 1
                else:
                    st.session_state.cart[item["id"]] = {
                        "name": item["name"],
                        "price": item["price"],
                        "qty": 1
                    }

    # ===== 购物车 =====
    st.subheader("🛒 我的选择")

    total = 0

    for k, v in list(st.session_state.cart.items()):
        col1, col2, col3 = st.columns([3,1,1])

        with col1:
            st.write(f"{v['name']} x{v['qty']}")

        with col2:
            if st.button("➕", key=f"add{k}"):
                v["qty"] += 1

        with col3:
            if st.button("➖", key=f"sub{k}"):
                v["qty"] -= 1
                if v["qty"] <= 0:
                    del st.session_state.cart[k]

        total += v["price"] * v["qty"]

    st.write(f"### 总价：¥{total}")

    if st.button("提交点单"):
        if st.session_state.cart:

            supabase.table("orders").insert({
                "user_name": st.session_state.user,
                "items": list(st.session_state.cart.values()),
                "total": total,
                "meal_time": meal_time,
                "note": note
            }).execute()

            st.success("已提交 👌")
            st.session_state.cart = {}

# ================= 今日菜单（核心） =================
if page == "今日菜单":

    st.title("🍳 今日做饭清单")

    orders = supabase.table("orders").select("*").execute().data

    today = datetime.now().strftime("%Y-%m-%d")

    today_orders = [
        o for o in orders
        if o["created_at"].startswith(today)
    ]

    if not today_orders:
        st.info("今天还没人点餐 😴")
    else:

        meals = {"早餐": [], "午餐": [], "晚餐": []}

        for o in today_orders:
            meals[o["meal_time"]].append(o)

        for meal, orders_list in meals.items():

            if orders_list:
                st.header(f"🍽 {meal}")

                summary = {}

                for o in orders_list:
                    for item in o["items"]:
                        name = item["name"]
                        qty = item["qty"]

                        summary[name] = summary.get(name, 0) + qty

                st.subheader("👉 要做这些菜：")
                for k, v in summary.items():
                    st.write(f"{k} × {v}")

                st.subheader("👨‍👩‍👧‍👦 点餐详情：")
                for o in orders_list:
                    st.write(f"👤 {o['user_name']}")

                    for item in o["items"]:
                        st.write(f"- {item['name']} x{item['qty']}")

                    if o.get("note"):
                        st.caption(f"备注：{o['note']}")

                    st.write("---")

# ================= 后台 =================
if page == "后台":

    st.title("🔧 菜单管理")

    name = st.text_input("菜名")
    price = st.number_input("价格")
    desc = st.text_area("描述（可选）")

    if st.button("添加"):
        supabase.table("menu").insert({
            "name": name,
            "price": price,
            "description": desc
        }).execute()
        st.success("添加成功")
