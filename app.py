import streamlit as st
from supabase import create_client
from streamlit_cookies_manager import EncryptedCookieManager
from datetime import datetime
import os

# ===== 页面配置 =====
st.set_page_config(page_title="泡泡小灶", page_icon="🍳", layout="centered")

# ===== Supabase =====
SUPABASE_URL = "https://pujodijixpuaqkfvcmwv.supabase.co"
SUPABASE_KEY = "sb_publishable_dD3ckwu1w_dM8h9sT7mIlw_LaKz0IPl"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ===== Cookie（自动登录）=====
cookies = EncryptedCookieManager(prefix="paopao", password="abc123")

if not cookies.ready():
    st.stop()

# ===== 登录状态 =====
if "user" not in st.session_state:
    st.session_state.user = cookies.get("user")

# =========================
# 🔐 登录 / 注册
# =========================
if not st.session_state.user:

    st.title("🍳 泡泡小灶")

    tab1, tab2 = st.tabs(["登录", "注册"])

    # ===== 登录 =====
    with tab1:
        u = st.text_input("用户名")
        p = st.text_input("密码", type="password")

        if st.button("登录"):
            res = supabase.table("users").select("*").eq("username", u).execute()

            if res.data and res.data[0]["password"] == p:
                st.session_state.user = u
                cookies["user"] = u
                cookies.save()
                st.rerun()
            else:
                st.error("账号或密码错误")

    # ===== 注册 =====
    with tab2:
        u = st.text_input("用户名", key="reg_u")
        p = st.text_input("密码", type="password", key="reg_p")

        role = st.selectbox("角色", ["主理人", "干饭人"])
        family = st.text_input("家庭名称（必须一致）")

        if st.button("注册"):
            if u and p and family:
                supabase.table("users").insert({
                    "username": u,
                    "password": p,
                    "role": "owner" if role == "主理人" else "member",
                    "family": family
                }).execute()
                st.success("注册成功，请登录")
            else:
                st.warning("请填写完整信息")

    st.stop()

# =========================
# 登录后
# =========================
user = st.session_state.user

user_info = supabase.table("users").select("*").eq("username", user).execute().data[0]

role = user_info["role"]
family = user_info["family"]

# ===== Sidebar =====
st.sidebar.write(f"👤 {user}")
st.sidebar.write(f"🏠 家庭：{family}")
st.sidebar.write(f"🎭 角色：{role}")

if st.sidebar.button("退出登录"):
    cookies["user"] = ""
    cookies.save()
    st.session_state.user = None
    st.rerun()

# ===== 页面选择 =====
if role == "owner":
    page = st.sidebar.selectbox("页面", ["点菜", "购物车", "订单记录", "后台管理"])
else:
    page = st.sidebar.selectbox("页面", ["点菜", "购物车", "订单记录"])

# ===== 初始化购物车 =====
if "cart" not in st.session_state:
    st.session_state.cart = {}

# =========================
# 🍜 点菜
# =========================
if page == "点菜":

    st.title("🍳 今日菜单")

    menu = supabase.table("menu").select("*").eq("family", family).execute().data

    for item in menu:
        col1, col2, col3 = st.columns([1,3,1])

        with col1:
            if item.get("image"):
                st.image(item["image"], width=80)

        with col2:
            st.write(f"**{item['name']}**")
            st.write(f"¥{item['price']}")
            if item.get("description"):
                st.caption(item["description"])

        with col3:
            if st.button("➕", key=item["id"]):
                if item["id"] in st.session_state.cart:
                    st.session_state.cart[item["id"]]["qty"] += 1
                else:
                    st.session_state.cart[item["id"]] = {
                        "name": item["name"],
                        "price": item["price"],
                        "qty": 1
                    }

# =========================
# 🛒 购物车
# =========================
if page == "购物车":

    st.title("🛒 购物车")

    total = 0

    for item_id, item in list(st.session_state.cart.items()):
        col1, col2, col3, col4 = st.columns([3,1,1,1])

        with col1:
            st.write(item["name"])

        with col2:
            st.write(f"¥{item['price']}")

        with col3:
            qty = st.number_input("数量", min_value=1, value=item["qty"], key=item_id)
            st.session_state.cart[item_id]["qty"] = qty

        with col4:
            if st.button("删除", key=f"del{item_id}"):
                del st.session_state.cart[item_id]
                st.rerun()

        total += item["price"] * item["qty"]

    st.write(f"### 总价：¥{total}")

    if st.button("下单"):
        if st.session_state.cart:

            supabase.table("orders").insert({
                "user_name": user,
                "family": family,
                "items": st.session_state.cart,
                "total": total,
                "created_at": datetime.now().isoformat()
            }).execute()

            st.success("下单成功 🍚")
            st.session_state.cart = {}

# =========================
# 📊 订单记录
# =========================
if page == "订单记录":

    st.title("📊 历史订单")

    orders = supabase.table("orders").select("*").eq("family", family).order("created_at", desc=True).execute().data

    for o in orders:
        st.write(f"👤 {o['user_name']} | 🕒 {o['created_at']}")
        for item in o["items"].values():
            st.write(f"- {item['name']} x {item['qty']}")
        st.write(f"💰 ¥{o['total']}")
        st.write("---")

# =========================
# 🔧 后台（主理人）
# =========================
if page == "后台管理":

    st.title("🔧 菜单管理")

    name = st.text_input("菜名")
    price = st.number_input("价格", min_value=0)
    desc = st.text_input("描述（可选）")
    image = st.text_input("图片URL（可选）")

    if st.button("添加菜品"):
        if name:
            supabase.table("menu").insert({
                "name": name,
                "price": price,
                "description": desc,
                "image": image,
                "family": family
            }).execute()
            st.success("添加成功")

    st.subheader("当前菜单")

    menu = supabase.table("menu").select("*").eq("family", family).execute().data

    for item in menu:
        col1, col2 = st.columns([3,1])

        with col1:
            st.write(f"{item['name']} ¥{item['price']}")

        with col2:
            if st.button("删除", key=f"del_menu_{item['id']}"):
                supabase.table("menu").delete().eq("id", item["id"]).execute()
                st.rerun()
