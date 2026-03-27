import streamlit as st
from supabase import create_client
import json
import os
from datetime import datetime

# ===== Supabase 配置 =====
SUPABASE_URL = "https://pujodijixpuaqkfvcmwv.supabase.co"
SUPABASE_KEY = "sb_publishable_dD3ckwu1w_dM8h9sT7mIlw_LaKz0IPl"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ===== 文件路径 =====
MENU_FILE = "menu.json"
ORDER_FILE = "orders.json"
USER_FILE = "users.json"
IMAGE_FOLDER = "images"
ADMIN_USER = "Monica"

# 创建图片文件夹
if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

# 数据读取和保存函数
def load_data(file, default):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_data(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 从数据库加载数据
menu = load_data(MENU_FILE, [])
orders = load_data(ORDER_FILE, [])
users = load_data(USER_FILE, [])

# ===== 用户管理 =====
if "user" not in st.session_state:
    st.session_state.user = None

# 登录状态
if st.session_state.user is None:
    st.title("🍳 泡泡小灶")
    st.subheader("欢迎回来")

    tab1, tab2, tab3 = st.tabs(["登录", "注册", "找回密码"])

    # 登录
    with tab1:
        login_user = st.text_input("用户名", key="login_user")
        login_pass = st.text_input("密码", type="password", key="login_pass")

        if st.button("登录"):
            res = supabase.table("users").select("*").eq("username", login_user).execute()
            if res.data and res.data[0]["password"] == login_pass:
                st.session_state.user = login_user
                st.success("登录成功 🍚")
                st.rerun()
            else:
                st.error("用户名或密码错误")

    # 注册
    with tab2:
        reg_user = st.text_input("用户名", key="reg_user")
        reg_pass = st.text_input("密码", type="password", key="reg_pass")
        reg_role = st.selectbox("角色", ["家庭主理人", "干饭人"])
        reg_family = st.text_input("家庭名称", key="reg_family")

        if st.button("注册"):
            if any(u["username"] == reg_user for u in users):
                st.warning("用户名已存在")
            elif reg_user and reg_pass and reg_family:
                users.append({
                    "username": reg_user,
                    "password": reg_pass,
                    "role": reg_role,
                    "family_name": reg_family
                })
                save_data(USER_FILE, users)
                st.success("注册成功，请登录")

    # 找回密码
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

# ===== 管理员和普通用户权限控制 =====
is_admin = st.session_state.user == ADMIN_USER
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

# ===== 页面选择 =====
if is_admin:
    page = st.sidebar.selectbox("选择页面", ["🍜 点菜", "🔧 菜单", "📊 数据分析"])
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

    # 假设 menu 的数据已经从数据库获取

# 菜品列表
for item in menu:
    col1, col2, col3 = st.columns([1, 3, 1])

    with col1:
        # 如果菜品有图片，才加载图片
        img_path = os.path.join(IMAGE_FOLDER, item.get("image", ""))
        if img_path and os.path.exists(img_path):
            st.image(img_path, use_container_width=True)
        else:
            st.text("没有图片")  # 如果没有图片，可以显示一个默认文本或者一个默认的占位图片

    with col2:
        # 显示菜品名称和价格
        st.write(f"**{item['name']}**")
        st.write(f"¥{item['price']}")

    with col3:
        # 点单按钮
        if st.button(f"点 {item['name']}", key=item["id"]):
            # 点菜逻辑，这里你可以处理点菜的数量和购物车的更新
            st.session_state.cart.append(item)

# 购物车部分
if st.session_state.cart:
    st.write("🛒 购物车")
    total = 0
    for item in st.session_state.cart:
        st.write(f"{item['name']} ¥{item['price']}")
        total += item['price']
    st.write(f"总价：¥{total}")

    if st.button("确认下单"):
        # 提交订单逻辑
        st.success("订单已提交")
        st.session_state.cart = []  # 清空购物车

# =========================
# 🔧 菜单管理
# =========================
if page == "🔧 菜单":
    st.title("🔧 菜单管理")

    # 只有管理员和家庭主理人可以编辑菜单
    user_info = supabase.table("users").select("*").eq("username", st.session_state.user).execute()
    if user_info.data[0]["role"] not in ["admin", "host"]:
        st.error("您没有权限编辑菜单")
        st.stop()

    name = st.text_input("菜名", key="dish_name")
    price = st.number_input("价格", min_value=0)
    category = st.selectbox("分类", ["大荤", "小荤", "素菜", "饮品", "汤品", "甜品", "主食"])
    image_file = st.file_uploader("上传图片", type=["jpg", "png"])

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
        col1, col2 = st.columns([3, 1])

        with col1:
            st.write(f"{item['category']} - {item['name']} ¥{item['price']}")

        with col2:
            if st.button("编辑", key=f"edit{i}"):
                new_name = st.text_input(f"修改 {item['name']} 的菜名", value=item['name'])
                new_price = st.number_input(f"修改 {item['name']} 的价格", value=item['price'], min_value=0)
                new_image_file = st.file_uploader(f"修改 {item['name']} 的图片", type=["jpg", "png"])

                if st.button(f"确认修改", key=f"confirm_edit_{i}"):
                    if new_name:
                        item['name'] = new_name
                        item['price'] = new_price
                        if new_image_file:
                            image_name = new_image_file.name
                            save_path = os.path.join(IMAGE_FOLDER, image_name)

                            with open(save_path, "wb") as f:
                                f.write(new_image_file.getbuffer())
                            item['image'] = image_name
                        save_data(MENU_FILE, menu)
                        st.success(f"菜品 {new_name} 修改成功！")

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
        st.write(f"👤 {order.get('user', '未知')} | 🕒 {order['time']}")
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
