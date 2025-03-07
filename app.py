# *-* coding:utf-8 *-*
import streamlit as st
import os
import importlib
from utils.user_manager import user_manager     # 确保这行导入存在
from config import LOGGER
from bot.bot_session_manager import BotSessionManager
from tools.tool_manager import ToolManager
import sys

# streamlit run app.py

# LOGGER.info(sys.executable)                   # 打印 Python 可执行文件的路径
# 设置Streamlit应用的页面配置
# page_title: 设置浏览器标签页的标题为"多Bot聊天"
# page_icon: 设置浏览器标签页的图标为一个机器人的emoji表情
# layout: 设置页面布局为"wide"，使得应用可以更宽地展示内容
st.set_page_config(page_title="多Bot聊天", page_icon="🤖", layout="wide")

# 动态地导入一个模块并获取该模块中与模块同名的类或函数。这在需要根据字符串名称加载不同页面或组件的场景中非常有用，例如在一个多页面的Streamlit应用中
def load_page(page_name):               # 定义一个函数，用于根据页面名称动态加载对应的页面模块
    # 使用importlib.import_module动态导入名为"custom_pages."加上page_name的模块
    module = importlib.import_module(f"custom_pages.{page_name}")
    return getattr(module, page_name)   # 使用getattr从导入的模块中获取与page_name同名的类或函数，并返回
# 例如，如果你有一个名为home.py的模块在custom_pages包中，并且 home.py 中有一个名为 home 的类或函数，你可以通过调用 load_page('home')来加载它

# 一个Streamlit应用的入口点，它负责处理用户会话、登录状态、页面导航以及应用的最终渲染
if __name__ == "__main__":
    bot_manager = None
    tool_manager = ToolManager()                    # 创建一个ToolManager工具管理器实例
    st.session_state.tool_manager = tool_manager    # 将工具管理器实例存储在会话状态中
    
    if not os.path.exists("user_config"):           # 如果user_config目录不存在，则创建该目录用于存储用户配置
        os.makedirs("user_config")
    
    # 初始化会话状态中的 logged_in 和 username 变量。
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = ''

    # 处理登录:
    query_params = st.query_params
    # 处理 URL 参数中的 token ，如果有token，则验证它。如果验证成功，更新会话状态以反映用户已登录，并初始化 BotSessionManager 实例
    if 'token' in query_params:
        token = query_params['token']
        if user_manager.verify_token(token):    # 如果验证成功，更新会话状态以反映用户已登录，并初始化 BotSessionManager 实例
            st.session_state['token'] = token   # 将token存储在会话状态中，以便在页面之间传递
            st.session_state.logged_in = True   # 更新会话状态以反映用户已登录
            st.session_state.username = user_manager.get_logged_in_username()   # 将用户名存储在会话状态中，以便在页面之间传递
            bot_manager = BotSessionManager(st.session_state.username)          # 创建一个BotSessionManager实例，用于管理用户的机器人会话
            st.session_state.bot_manager = bot_manager                          # 将 BotSessionManager 实例存储在会话状态中
            # 更新会话状态以包含用户的机器人列表、群组历史版本信息和当前群组历史版本索引
            st.session_state.bots = bot_manager.bots                            # 将机器人列表存储在会话状态中
            st.session_state.group_history_versions = bot_manager.group_history_versions
            st.session_state.current_group_history_version_idx = bot_manager.current_group_history_version_idx
            # 如果会话状态中没有页面信息，设置页面为用户上次访问的页面
            if 'page' not in st.session_state:
                st.session_state.page = bot_manager.get_last_visited_page()
            st.session_state.chat_config = bot_manager.get_chat_config()                                # 将聊天配置存储在会话状态中
            st.session_state.current_history_version_idx = bot_manager.current_history_version_idx      # 将当前历史版本索引存储在会话状态中
            LOGGER.info(f"使用token登录成功. Username: {st.session_state.username}")                     # 记录登录成功的日志
        else:
            LOGGER.warning("无效的token")
            st.session_state.logged_in = False
            st.session_state.username = ''
    # 如果token无效或不存在，确保会话状态反映用户未登录
    else:
        st.session_state['token'] = ''
        st.session_state.logged_in = False
        st.session_state.username = ''

    # 页面导航:
    if 'page' not in st.session_state:
        st.session_state.page = "login_page"

    # st.columns([1, 1, 1], gap="small") 创建了三列，每列的宽度比例为 1:1:1，即三列宽度相等。gap="small" 设置了列之间的间距为小间距。
    # 返回的 col_empty, col_center, col_empty 分别代表这三列，其中 col_center 是中间的一列，通常用于放置主要内容，而 col_empty 用于在两侧留白。
    col_empty, col_center, col_empty = st.columns([1, 1, 1], gap="small")
    if st.session_state.logged_in:
        if st.session_state.page == "change_password_page":
            change_password_page = load_page("change_password_page")
            with col_center:
                change_password_page()
        elif st.session_state.page == "group_page":
            group_page = load_page("group_page")
            group_page()
        elif st.session_state.page == "main_page":
            main_page = load_page("main_page")
            main_page()
        else:
            st.session_state.page = "group_page"
            group_page = load_page("group_page")
            group_page()
        
        # 更新最后访问的页面信息
        bot_manager.set_last_visited_page(st.session_state.page)

    # 如果用户未登录（st.session_state.logged_in为False），则检查会话状态中的page变量; 如果page是register_page，则加载注册页面。否则，默认加载登录页面
    else:
        if st.session_state.page == "register_page":
            register_page = load_page("register_page")
            with col_center:
                register_page()
        else:
            st.session_state.page = "login_page"
            login_page = load_page("login_page")
            with col_center:
                login_page()

    # 页脚: 底部版权信息
    st.markdown("""
                    <p style="text-align: center; color: gray; padding-top:5rem">
                        <a href="https://gitee.com/gptzm/multibot-chat" style="color: gray;">MultiBot-Chat by zm</a>
                    </p>
                """, unsafe_allow_html=True)

    # 保存会话状态: 如果用户已登录并且 bot_manager 存在，更新聊天配置并将数据保存到文件。
    if st.session_state.logged_in and bot_manager:
        bot_manager.update_chat_config(st.session_state.chat_config)
        bot_manager.save_data_to_file()
