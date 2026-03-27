# ===== Supabase =====
from supabase import create_client
import streamlit as st
from datetime import datetime

SUPABASE_URL = "https://pujodijixpuaqkfvcmwv.supabase.co"
SUPABASE_KEY = "sb_publishable_dD3ckwu1w_dM8h9sT7mIlw_LaKz0IPl"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

ADMIN_USER = "admin"

if "user" not in st.session_state:
    st.session_state.user = None

# ================= 登录/注册 =================
if st.session_state.user is None:

    st.title("🍳 家庭点餐系统")

    tab1, tab2 = st.tabs(["登录", "注册"])

    # 登录
    with tab1:
        u = st.text_input("用户名")
        p = st.text_input("密码", type="password")

        if st.button("登录"):
            res = supabase.table("users").select("*").eq("username", u).execute()

            if res.data and res.data[0]["password"] == p:
                st.session_state.user = res.data[0]
                st.rerun()
            else:
                st.error("登录失败")

    # 注册
    with tab2:
        ru = st.text_input("用户名", key="reg_u")
        rp = st.text_input("密码", type="password", key="reg_p")
        role = st.selectbox("角色", ["家庭主理人", "干饭人"])
        family_name = st.text_input("家庭名称（主理人填写）")

        if st.button("注册"):

            # 主理人创建家庭
            if role == "家庭主理人":
                fam = supabase.table("families").insert({
                    "name": family_name
                }).execute()

                family_id = fam.data[0]["id"]

            else:
                # 加入已有家庭（简单版：输入名称）
                fam = supabase.table("families").select("*").eq("name", family_name).execute()
                if not fam.data:
                    st.error("家庭不存在")
                    st.stop()
                family_id = fam.data[0]["id"]

            supabase.table("users").insert({
                "username": ru,
                "password": rp,
                "role": "host" if role == "家庭主理人" else "member",
                "family_id": family_id
            }).execute()

            st.success("注册成功")

    st.stop()

# ================= 登录后 =================
user = st.session_state.user
role = user["role"]
family_id = user["family_id"]

st.sidebar.write(f"👤 {user['username']} ({role})")

if st.sidebar.button("退出"):
    st.session_state.user = None
    st.rerun()

# 页面权限
pages = ["点菜"]

if role == "host":
    pages += ["今日菜单", "菜单管理"]

if user["username"] == ADMIN_USER:
    pages += ["系统管理"]

page = st.sidebar.selectbox("页面", pages)

# ================= 点菜 =================
if page == "点菜":

    st.title("🍳 点菜")

    menu = supabase.table("menu").select("*").eq("family_id", family_id).execute().data

    if "cart" not in st.session_state:
        st.session_state.cart = {}

    meal_time = st.selectbox("用餐时间", ["早餐","午餐","晚餐"])
    note = st.text_input("备注")

    for item in menu:
        col1, col2 = st.columns([4,1])

        with col1:
            st.write(f"{item['name']} ¥{item['price']}")

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

    # 购物车
    st.subheader("🛒 购物车")

    total = 0

    for k,v in list(st.session_state.cart.items()):
        st.write(f"{v['name']} x{v['qty']}")
        total += v["price"] * v["qty"]

    if st.button("提交"):
        supabase.table("orders").insert({
            "family_id": family_id,
            "user_id": user["id"],
            "user_name": user["username"],
            "items": list(st.session_state.cart.values()),
            "total": total,
            "meal_time": meal_time,
            "note": note
        }).execute()

        st.success("已提交")
        st.session_state.cart = {}

# ================= 今日菜单 =================
if page == "今日菜单":

    st.title("🍳 今日做饭清单")

    orders = supabase.table("orders").select("*").eq("family_id", family_id).execute().data

    today = datetime.now().strftime("%Y-%m-%d")

    summary = {}

    for o in orders:
        if o["created_at"].startswith(today):
            for item in o["items"]:
                summary[item["name"]] = summary.get(item["name"],0)+item["qty"]

    for k,v in summary.items():
        st.write(f"{k} × {v}")

# ================= 菜单管理 =================
if page == "菜单管理":

    st.title("🔧 菜单管理")

    name = st.text_input("菜名")
    price = st.number_input("价格")
    desc = st.text_area("描述")

    if st.button("添加"):
        supabase.table("menu").insert({
            "family_id": family_id,
            "name": name,
            "price": price,
            "description": desc
        }).execute()

    menu = supabase.table("menu").select("*").eq("family_id", family_id).execute().data

    for item in menu:
        st.write(item["name"])
