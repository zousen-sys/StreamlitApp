import streamlit as st
from utils.user_manager import user_manager  # 确保这行导入存在

def change_password_page():
    st.title("修改密码")
    # 检查用户是否已登录。st.session_state 是Streamlit的会话状态对象，用于存储跨请求的状态信息。
    # 如果用户未登录（'logged_in' 不在会话状态中或者 logged_in 的值为假），则显示警告信息，并将页面重定向到登录页面
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.warning("请先登录以修改密码")
        st.session_state.page = "login_page"
        st.rerun()

    # 如果用户已登录，则创建一个名为“修改密码表单”的表单。
    # 默认情况下，Streamlit会将每个UI组件放在一个新的块中，这些块在页面上垂直堆叠；st.form 是一个容器，它会将其内部的组件组织在一起
    else:
        with st.form("修改密码表单"):
            old_password = st.text_input("旧密码", type='password')
            new_password = st.text_input("新密码", type='password')
            confirm_password = st.text_input("确认新密码", type="password")
            submit_button = st.form_submit_button("修改密码", type='primary', use_container_width=True)
        
        if submit_button:
            if new_password != confirm_password:
                st.error("新密码和确认密码不匹配")
            elif user_manager.change_password(st.session_state.username, old_password, new_password):
                st.success("密码修改成功")
            else:
                st.warning("旧密码错误")
        # 如果用户点击“返回”按钮，则将页面重定向到主页。
        if st.button("返回", use_container_width=True): # use_container_width=True 按钮的宽度会自动适应其容器的宽度
            st.session_state.page = "main_page"
            st.rerun()
