st.markdown("""
<style>
/* 🔥 隐藏顶部工具栏 */
header {visibility: hidden;}
footer {visibility: hidden;}
#MainMenu {visibility: hidden;}

/* 🔥 隐藏右下角头像 */
.st-emotion-cache-1v0mbdj {
    display: none;
}

/* 🔥 页面居中 + 手机适配 */
.block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
    padding-left: 1rem;
    padding-right: 1rem;
    max-width: 600px;
    margin: auto;
}

/* 🔥 标题优化 */
h1 {
    text-align: center;
    font-size: 28px;
}

/* 🔥 按钮更大（手机友好） */
.stButton>button {
    width: 100%;
    height: 48px;
    font-size: 18px;
    border-radius: 12px;
}

/* 🔥 输入框优化 */
.stTextInput>div>div>input {
    height: 45px;
    font-size: 16px;
}

/* 🔥 卡片风格 */
.stContainer {
    border-radius: 12px;
    padding: 10px;
}
</style>
""", unsafe_allow_html=True)
import streamlit as st
import json
import os
from datetime import datetime
from collections import Counter

st.set_page_config(page_title="泡泡小灶", page_icon="🍳", layout="centered")

MENU_FILE = "menu.json"
ORDER_FILE = "orders.json"
USER_FILE = "users.json"
IMAGE_FOLDER = "images"
ADMIN_USER = "Monica"

if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

# ===== 数据读写 =====
def load_data(file, default):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_data(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

menu = load_data(MENU_FILE, [])
orders = load_data(ORDER_FILE, [])
users = load_data(USER_FILE, [])

# ===== 自动创建管理员 =====
if not any(u["username"] == ADMIN_USER for u in users):
    users.append({
        "username": ADMIN_USER,
        "password": "Yz991022$",
        "email": "admin@test.com"
    })
    save_data(USER_FILE, users)

# ===== 登录状态 =====
if "user" not in st.session_state:
    st.session_state.user = None

# =========================
# 🔐 登录 / 注册 / 找回密码
# =========================
if st.session_state.user is None:

    st.title("🍳 泡泡小灶")
    st.subheader("欢迎回来")

    tab1, tab2, tab3 = st.tabs(["登录", "注册", "找回密码"])

    # ===== 登录 =====
    with tab1:
        login_user = st.text_input("用户名", key="login_user")
        login_pass = st.text_input("密码", type="password", key="login_pass")

        if st.button("登录"):
            for u in users:
                if u["username"] == login_user and u["password"] == login_pass:
                    st.session_state.user = login_user
                    st.success("登录成功 🍚")
                    st.rerun()
            st.error("用户名或密码错误")

    # ===== 注册 =====
    with tab2:
        reg_user = st.text_input("用户名", key="reg_user")
        reg_pass = st.text_input("密码", type="password", key="reg_pass")
        reg_email = st.text_input("邮箱", key="reg_email")

        if st.button("注册"):
            if any(u["username"] == reg_user for u in users):
                st.warning("用户名已存在")
            elif reg_user and reg_pass and reg_email:
                users.append({
                    "username": reg_user,
                    "password": reg_pass,
                    "email": reg_email
                })
                save_data(USER_FILE, users)
                st.success("注册成功，请登录")

    # ===== 找回密码 =====
    with tab3:
        fp_user = st.text_input("用户名", key="fp_user")
        fp_email = st.text_input("注册邮箱", key="fp_email")
        new_pass = st.text_input("新密码", type="password", key="fp_new_pass")

        if st.button("重置密码"):
            for u in users:
                if u["username"] == fp_user and u.get("email") == fp_email:
                    u["password"] = new_pass
                    save_data(USER_FILE, users)
                    st.success("密码已重置！")
                    break
            else:
                st.error("用户名或邮箱不匹配")

    st.stop()

# =========================
# 登录后
# =========================
is_admin = st.session_state.user == ADMIN_USER

# 显示用户
if is_admin:
    st.sidebar.markdown(f"👤 **{st.session_state.user}（主理人）**")
else:
    st.sidebar.markdown(f"👤 {st.session_state.user}")

# 修改密码
st.sidebar.markdown("---")
st.sidebar.subheader("🔑 修改密码")

old_pass = st.sidebar.text_input("旧密码", type="password", key="old_pass")
new_pass = st.sidebar.text_input("新密码", type="password", key="new_pass")

if st.sidebar.button("修改密码"):
    for u in users:
        if u["username"] == st.session_state.user:
            if u["password"] == old_pass:
                u["password"] = new_pass
                save_data(USER_FILE, users)
                st.sidebar.success("修改成功")
            else:
                st.sidebar.error("旧密码错误")

# 退出
if st.sidebar.button("退出登录"):
    st.session_state.user = None
    st.rerun()

# 权限控制
if is_admin:
    page = st.sidebar.selectbox("选择页面", ["🍜 点菜", "🔧 后台管理", "📊 数据分析"])
else:
    page = "🍜 点菜"

# ===== 购物车 =====
if "cart" not in st.session_state:
    st.session_state.cart = []

# =========================
# 🍜 点菜
# =========================
if page == "🍜 点菜":
    st.title("🍳 泡泡小灶")
    st.caption("今天吃什么，一起点一下")

    categories = list(set([item["category"] for item in menu])) if menu else []

    for cat in categories:
        st.header(f"🍽 {cat}")

        for item in menu:
            if item["category"] == cat:
                col1, col2, col3 = st.columns([1,3,1])

                with col1:
                    img_path = os.path.join(IMAGE_FOLDER, item.get("image",""))
                    if os.path.exists(img_path):
                        st.image(img_path, use_container_width=True)

                with col2:
                    st.write(f"**{item['name']}**")
                    st.write(f"¥{item['price']}")

                with col3:
                    if st.button("点", key=item["name"], use_container_width=True):
                        st.session_state.cart.append(item)

    # 购物车
    st.header("🛒 购物车")
    total = 0

    for item in st.session_state.cart:
        st.write(f"{item['name']} ¥{item['price']}")
        total += item["price"]

    st.write(f"### 总价：¥{total}")

    if st.button("✅ 下单"):
        if st.session_state.cart:
            order = {
                "user": st.session_state.user,
                "items": st.session_state.cart,
                "total": total,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            orders.append(order)
            save_data(ORDER_FILE, orders)

            st.success("开饭啦 🍚")
            st.session_state.cart = []

# =========================
# 🔧 后台
# =========================
if page == "🔧 后台管理":
    st.title("🔧 后台管理")

    name = st.text_input("菜名", key="dish_name")
    price = st.number_input("价格", min_value=0)
    category = st.selectbox("分类", ["主食", "荤菜", "素菜", "饮品"])

    image_file = st.file_uploader("上传图片", type=["jpg","png"])

    if st.button("添加菜品"):
        if name:
            image_name = ""

            if image_file:
                image_name = image_file.name
                save_path = os.path.join(IMAGE_FOLDER, image_name)

                with open(save_path, "wb") as f:
                    f.write(image_file.getbuffer())

            menu.append({
                "name": name,
                "price": price,
                "category": category,
                "image": image_name
            })

            save_data(MENU_FILE, menu)
            st.success("添加成功！")

    st.subheader("📋 当前菜单")

    for i, item in enumerate(menu):
        col1, col2 = st.columns([3,1])

        with col1:
            st.write(f"{item['category']} - {item['name']} ¥{item['price']}")

        with col2:
            if st.button("删除", key=f"del{i}"):
                menu.pop(i)
                save_data(MENU_FILE, menu)
                st.rerun()

# =========================
# 📊 数据分析
# =========================
if page == "📊 数据分析":
    st.title("📊 点餐分析")

    total_orders = len(orders)
    total_revenue = sum(o["total"] for o in orders)

    st.write(f"📦 总订单数：{total_orders}")
    st.write(f"💰 总收入：¥{total_revenue}")

    st.subheader("📊 订单记录")

    for order in orders[::-1]:
        st.write(f"👤 {order.get('user','未知')} | 🕒 {order['time']}")
        for item in order["items"]:
            st.write(f"- {item['name']}")
        st.write("---")

    all_items = []
    for order in orders:
        for item in order["items"]:
            all_items.append(item["name"])

    if all_items:
        counter = Counter(all_items)
        st.subheader("🏆 热门菜品")
        for name, count in counter.most_common(10):
            st.write(f"{name} - {count}次")
