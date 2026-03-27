import streamlit as st
from supabase import create_client
from streamlit_cookies_manager import EncryptedCookieManager
from datetime import datetime

# ===== 页面配置 =====
st.set_page_config(page_title="泡泡小灶", page_icon="🍳", layout="centered")

# ===== Supabase =====
SUPABASE_URL = "https://pujodijixpuaqkfvcmwv.supabase.co"
SUPABASE_KEY = "sb_publishable_dD3ckwu1w_dM8h9sT7mIlw_LaKz0IPl"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ===== Cookie =====
cookies = EncryptedCookieManager(prefix="paopao", password="abc123")
if not cookies.ready():
    st.stop()

if "user" not in st.session_state:
    st.session_state.user = cookies.get("user")

# =========================
# 🔐 登录 / 注册
# =========================
if not st.session_state.user:

    st.title("🍳 泡泡小灶")

    tab1, tab2 = st.tabs(["登录", "注册"])

    # 登录
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

    # 注册
    with tab2:
        u = st.text_input("用户名", key="reg_u")
        p = st.text_input("密码", type="password", key="reg_p")
        role = st.selectbox("角色", ["主理人", "干饭人"])
        family_name = st.text_input("家庭名称")

        if st.button("注册"):
            if u and p and family_name:

                fam = supabase.table("families").select("*").eq("name", family_name).execute()

                if fam.data:
                    family_id = fam.data[0]["id"]
                else:
                    new_fam = supabase.table("families").insert({"name": family_name}).execute()
                    family_id = new_fam.data[0]["id"]

                supabase.table("users").insert({
                    "username": u,
                    "password": p,
                    "role": "host" if role == "主理人" else "member",
                    "family_id": family_id
                }).execute()

                st.success("注册成功")
            else:
                st.warning("请填写完整信息")

    st.stop()

# =========================
# 登录后
# =========================
user = st.session_state.user
user_info = supabase.table("users").select("*").eq("username", user).execute().data[0]

role = user_info["role"]
family_id = user_info["family_id"]

family = supabase.table("families").select("*").eq("id", family_id).execute().data[0]["name"]

# ===== Sidebar =====
st.sidebar.write(f"👤 {user}")
st.sidebar.write(f"🏠 {family}")
st.sidebar.write(f"🎭 {role}")

if st.sidebar.button("退出登录"):
    cookies["user"] = ""
    cookies.save()
    st.session_state.user = None
    st.rerun()

# 注销
if st.sidebar.button("注销账号"):
    supabase.table("users").delete().eq("id", user_info["id"]).execute()
    cookies["user"] = ""
    cookies.save()
    st.session_state.user = None
    st.rerun()

# 页面
if role == "host":
    page = st.sidebar.selectbox("页面", ["菜单", "购物车", "订单记录"])
else:
    page = st.sidebar.selectbox("页面", ["菜单", "购物车", "订单记录"])

# ===== 购物车 =====
if "cart" not in st.session_state:
    st.session_state.cart = {}

# =========================
# 🍜 菜单
# =========================
if page == "菜单":

    today = datetime.now()
    st.title(f"🍳 今日菜单")
    st.caption(today.strftime("%Y-%m-%d %A"))

    menu = supabase.table("menu").select("*").eq("family_id", family_id).execute().data

    categories = ["大荤", "小荤", "纯素", "汤品", "甜品", "主食"]

    for cat in categories:
        st.subheader(cat)

        for item in menu:
            if item.get("category") == cat:

                col1, col2, col3 = st.columns([1,3,1])

                with col1:
                    if item.get("image"):
                        st.image(item["image"], width=80)

                with col2:
                    st.write(f"**{item['name']}** ¥{item['price']}")

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

                # 🔥 主理人编辑
                if role == "host":
                    with st.expander("编辑菜品"):

                        new_name = st.text_input("名称", value=item["name"], key=f"name{item['id']}")
                        new_price = st.number_input("价格", value=item["price"], key=f"price{item['id']}")
                        new_cat = st.selectbox("分类", categories, index=categories.index(item["category"]), key=f"cat{item['id']}")
                        new_img = st.text_input("图片URL", value=item.get("image",""), key=f"img{item['id']}")

                        if st.button("保存", key=f"save{item['id']}"):
                            supabase.table("menu").update({
                                "name": new_name,
                                "price": new_price,
                                "category": new_cat,
                                "image": new_img
                            }).eq("id", item["id"]).execute()
                            st.success("已更新")
                            st.rerun()

                        if st.button("删除", key=f"del{item['id']}"):
                            supabase.table("menu").delete().eq("id", item["id"]).execute()
                            st.rerun()

    # 添加菜
    if role == "host":
        st.markdown("---")
        st.subheader("➕ 添加菜品")

        n = st.text_input("名称")
        p = st.number_input("价格", min_value=0)
        c = st.selectbox("分类", categories)
        i = st.text_input("图片URL")

        if st.button("添加"):
            supabase.table("menu").insert({
                "name": n,
                "price": p,
                "category": c,
                "image": i,
                "family_id": family_id
            }).execute()
            st.rerun()

# =========================
# 🛒 购物车
# =========================
if page == "购物车":

    st.title("🛒 购物车")
    total = 0

    for k, v in list(st.session_state.cart.items()):
        col1, col2, col3 = st.columns([3,1,1])

        col1.write(v["name"])
        col2.write(f"x{v['qty']}")

        if col3.button("删除", key=f"c{k}"):
            del st.session_state.cart[k]
            st.rerun()

        total += v["price"] * v["qty"]

    st.write(f"### 总价 ¥{total}")

    if st.button("下单"):
        supabase.table("orders").insert({
            "family_id": family_id,
            "user_id": user_info["id"],
            "user_name": user,
            "items": st.session_state.cart,
            "total": total
        }).execute()

        st.success("已下单")
        st.session_state.cart = {}

# =========================
# 📊 订单
# =========================
if page == "订单记录":

    st.title("📊 历史订单")

    orders = supabase.table("orders").select("*").eq("family_id", family_id).order("created_at", desc=True).execute().data

    for o in orders:
        st.write(f"{o['user_name']} - {o['created_at']}")
        for i in o["items"].values():
            st.write(f"- {i['name']} x{i['qty']}")

        st.write(f"¥{o['total']}")
        st.write("---")
