import logging
import markdown
from bot.chat_router import ChatRouter
import streamlit.components.v1 as components
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
import html
import random
import streamlit as st
from bs4 import BeautifulSoup
import base64
from utils.chat_styles import get_chat_container_style

LOGGER = logging.getLogger(__name__)

class SVGProcessor(Preprocessor):
    def run(self, lines):
        new_lines = []
        in_block = False
        block_content = []
        block_type = ''
        
        for line in lines:
            if line.strip().startswith('```') and not in_block:
                block_type = line.strip()[3:].lower()
                if block_type in ['svg', 'xml', 'html']:
                    in_block = True
                    block_content = []
                else:
                    new_lines.append(line)
            elif line.strip() == '```' and in_block:
                in_block = False
                content_string = '\n'.join(block_content)
                try:
                    soup = BeautifulSoup(content_string, 'html.parser')
                    root = soup.find()
                    if root and root.name == 'svg':
                        svg_bytes = str(root).encode('utf-8')
                        base64_svg = base64.b64encode(svg_bytes).decode('utf-8')
                        new_lines.append(f'![SVG图片](data:image/svg+xml;base64,{base64_svg})')
                    else:
                        new_lines.extend([f'```{block_type}'] + block_content + ['```'])
                except Exception as e:
                    LOGGER.error(f"错误解析{block_type.upper()}内容: {e}")
                    new_lines.extend([f'```{block_type}'] + block_content + ['```'])
            elif in_block:
                block_content.append(line)
            else:
                new_lines.append(line)
        
        return new_lines
class SVGExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(SVGProcessor(md), 'svg_processor', 175)
class CodeProcessor(Preprocessor):
    def run(self, lines):
        new_lines = []
        in_block = False
        block_content = []
        block_type = ''
        
        for line in lines:
            if line.strip().startswith('```') and not in_block:
                block_type = line.strip()[3:].lower() or 'text'
                in_block = True
                block_content = []
                new_lines.append(f'<div class="code-block"><div class="code-header"><span class="code-language">{block_type}</span><button class="code-copy-btn" onclick="copyCode(this)"><span>复制</span></button></div>')
                new_lines.append(line)
            elif line.strip() == '```' and in_block:
                in_block = False
                new_lines.extend(block_content)
                new_lines.append(line)
                new_lines.append('</div>')
            elif in_block:
                block_content.append(line)
            else:
                new_lines.append(line)
        
        return new_lines

class CodeExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(CodeProcessor(md), 'code_processor', 175)

# 移除原有的 process_svg_content 函数
# 001 从一个聊天机器人获取响应
def get_response_from_bot(prompt, bot, history):
    # bot_manager 用来管理聊天机器人配置和状态的一个类实例
    bot_manager = st.session_state.bot_manager
    # 获取最新的聊天配置。这个配置可能包含了机器人的行为设置、回复模板等
    latest_chat_config = bot_manager.get_chat_config()
    # LOGGER.info(f"Latest chat_config: {latest_chat_config}")

    # 创建一个 ChatRouter 对象，它可能负责根据配置将消息路由到正确的处理逻辑
    chat_router = ChatRouter(bot, latest_chat_config)
    # 使用 ChatRouter 的 send_message 方法发送 prompt 消息，并附带对话历史 history，然后接收机器人的响应内容
    response_content = chat_router.send_message(prompt, history)
    # 日志记录
    # LOGGER.info(f"Single Response: {response_content}")
    return response_content

def get_response_from_bot_group(prompt, bot, group_history):
    bot_manager = st.session_state.bot_manager
    # 每次调用时获取最新的chat_config
    latest_chat_config = bot_manager.get_chat_config()
    # LOGGER.info(f"Latest chat_config for group chat: {latest_chat_config}")
    chat_router = ChatRouter(bot, latest_chat_config)
    response_content = chat_router.send_message_group(prompt, group_history)
    # 日志记录
    # LOGGER.info(f"Group Response: {response_content}")
    return response_content

# bot（包含机器人信息的字典）和 history（聊天历史的列表）
def display_chat(bot, history):
    if not bot:     
        return
    # 使用 f-string 初始化一个 HTML 字符串 bot_html，其中包含一些内联样式和一个带有特定 ID 的 div 容器
    bot_html = f"""
        {get_chat_container_style()}
        <div id='chat-container-{bot['id']}' class='chat-container' style='height: 660px;'>
    """
    # 遍历 history 列表中的每个聊天条目 entry
    for entry in history:
        # 获取聊天条目的内容，并使用 Markdown 扩展将其转换为 HTML
        content = entry.get('content', '')
        content_markdown = markdown.markdown(
            str(content),
            extensions=[
                SVGExtension(),
                "nl2br",
                "codehilite",
                "tables",
                "admonition",
                "sane_lists",
                "attr_list",
                "toc",
                "fenced_code",
                CodeExtension(),
            ]
        )
        
        content_markdown_repr = repr(entry['content'])
        # 生成一个随机 ID 用于复制按钮的 JavaScript 函数
        random_id = str(random.randint(100000000000, 999999999999))
        # 根据聊天条目的角色（用户或助手），生成不同的 HTML 结构和样式
        if entry['role'] == 'user':
            # 使用 flex 布局，使得其子元素（按钮和消息内容）可以在一行内排列，并且垂直对齐到底部
            # max-width: 80%; 限制了这个flex容器的最大宽度为父容器的80%，确保消息不会占据整个聊天窗口
            bot_html += f"""<div class='message message-user'>
                                <div style='display: flex; align-items: flex-end; max-width: 80%;'>
                                    <button onclick="copy_{random_id}(this)" class="copy-button">📃</button>
                                    <div class='message message-user-content'>
                                        {content_markdown}
                                    </div>
                                </div>
                                <div class='user-avatar'>🐵​</div>
                            </div>"""
            
        if entry['role'] == 'assistant':
            bot_html += f"""<div class='message message-assistant'>
                            <div class='bot-avatar'>{bot.get('avatar', '🤖')}</div>
                            <div style='display: flex; align-items: flex-end; max-width: 80%;'>
                                <div class='message-assistant-content'>
                                    {content_markdown}
                                </div>
                                <button onclick="copy_{random_id}(this)" ontouch="copy_{random_id}(this)" class="copy-button">📃</button>
                            </div>
                        </div>"""
        # 为每个聊天条目添加一个复制按钮的 JavaScript 函数
        bot_html += f"""<script>
                            function copy_{random_id}(element){{
                                navigator.clipboard.writeText({content_markdown_repr}).then(() => {{
                                    const lastInnerHTML = element.innerHTML;
                                    element.innerHTML = '✅';
                                    setTimeout(() => {{
                                        element.innerHTML = lastInnerHTML;
                                    }}, 300);
                                }});
                            }}
                        </script>"""
    # 关闭聊天容器 div，并添加 JavaScript 代码以自动滚动到最新的聊天条目
    bot_html += f"""
        </div>
        <script>
            var chatContainer = document.getElementById('chat-container-{bot['id']}');
            var lastAssistantMessage = chatContainer.querySelector('.message-assistant:last-of-type');
            if (lastAssistantMessage) {{
                chatContainer.scrollTop = Math.max(0, lastAssistantMessage.offsetTop - 100);
            }} else {{
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }}
            
        </script>
    """
    # 使用 components.html 函数将生成的 HTML 字符串渲染到页面上
    components.html(bot_html, height=700)   # 400->

def display_group_chat(bots, history):
    """
    显示群聊记录。

    参数:
    - bots: 包含所有机器人的列表，每个机器人是一个字典，包含'id', 'name', 和 'avatar' 等信息。
    - history: 聊天历史记录，是一个列表，每个元素是一个包含聊天信息的字典，包括'bot_id', 'role', 'content'等。

    此函数负责渲染群聊界面，根据聊天历史记录和机器人信息，生成HTML代码来显示聊天内容。
    """
    # 初始化聊天容器的HTML结构，并设置样式
    bot_html = f"""
        {get_chat_container_style()}
        <div id='group-chat-container' class='chat-container' style='height: 560px;'>
    """

    # 遍历聊天历史记录，构建聊天内容的HTML
    for entry in history:
        bot_id = entry.get('bot_id','')
        role = entry.get('role','')
        content = entry.get('content', '')
        content_markdown = markdown.markdown(
            str(content),
            extensions=[
                SVGExtension(),
                "nl2br",
                "codehilite",
                "tables",
                "admonition",
                "sane_lists",
                "attr_list",
                "toc",
                "fenced_code",
                CodeExtension(),
            ]
        )
        # 将聊天内容转换为Markdown格式
        content_markdown_repr = repr(entry['content'])
        random_id = str(random.randint(100000000000, 999999999999))
        # 根据消息类型（工具名称、用户、机器人）构建不同的HTML结构
        if 'tool_name' in entry:
            # 如果是工具消息
            bot_html += f"""<div class='message message-assistant'>
                            <div class='bot-avatar'>🛠️</div>
                            <div style='display: flex; flex-direction: column; max-width: 80%;'>
                                <div class='bot-name'>{html.escape(entry['tool_name'])}</div>
                                <div style='display: flex; align-items: flex-end;'>
                                    <div class='message-assistant-content'>
                                        {content_markdown}
                                    </div>
                                    <button onclick="copy_{random_id}(this)" ontouch="copy_{random_id}(this)" class="copy-button">📃</button>
                                </div>
                            </div>
                        </div>"""
        elif role == 'user':
            # 如果是用户消息
            bot_html += f"""<div class='message message-user'>
                                <div style='display: flex; align-items: flex-end; max-width: 80%;'>
                                    <button onclick="copy_{random_id}(this)" class="copy-button">📃</button>
                                    <div class='message-user-content'>
                                        {content_markdown}
                                    </div>
                                </div>
                                <div class='user-avatar'>🐵​</div>
                            </div>"""
        else:
            # 如果是机器人消息
            bot = next((b for b in bots if b['id'] == bot_id), None)
            if bot:
                avatar = bot.get('avatar', '🤖')
                bot_html += f"""<div class='message message-assistant'>
                                <div class='bot-avatar'>{avatar}</div>
                                <div style='display: flex; flex-direction: column; max-width: 80%;'>
                                    <div class='bot-name'>{html.escape(bot.get('name'))}</div>
                                    <div style='display: flex; align-items: flex-end;'>
                                        <div class='message-assistant-content'>
                                            {content_markdown}
                                        </div>
                                        <button onclick="copy_{random_id}(this)" ontouch="copy_{random_id}(this)" class="copy-button">📃</button>
                                    </div>
                                </div>
                            </div>"""
        # 添加复制功能的JavaScript代码
        bot_html += f"""<script>
                            function copy_{random_id}(element) {{
                                const textToCopy = {content_markdown_repr};

                                if (navigator.clipboard && navigator.clipboard.writeText) {{
                                    // 使用 Clipboard API 复制
                                    navigator.clipboard.writeText(textToCopy).then(() => {{
                                        showCopyTextSuccess(element);
                                        return;
                                    }});
                                }} else if(fallbackCopyText(textToCopy, element)) {{
                                    // 使用备用方法复制
                                    showCopyTextSuccess(element);
                                }}
                            }}
                        </script>"""
        
    # 获取聊天配置，并根据配置添加提示信息
    bot_manager = st.session_state.bot_manager
    chat_config = bot_manager.get_chat_config()
    group_user_prompt = chat_config.get('group_user_prompt', '').replace('\n', ' ').replace('\r', ' ')
    if len(group_user_prompt) > 20:
        group_user_prompt = group_user_prompt[:20] + '...'
    if group_user_prompt and history[-1].get('role') != 'user':
        bot_html += f'<div class="tips">Bot接力提示词：{html.escape(group_user_prompt)}</div>'

    # 完成聊天容器的HTML结构
    bot_html += """
        </div>
        <script>
            var chatContainer = document.getElementById('group-chat-container');
            chatContainer.scrollTop = chatContainer.scrollHeight;
        </script>
        <script>
            function fallbackCopyText(text, element) {
                const textarea = document.createElement('textarea');
                textarea.value = text;
                textarea.style.position = 'fixed';  // 避免影响页面布局
                document.body.appendChild(textarea);
                textarea.focus();
                textarea.select();
                try {
                    if (document.execCommand('copy')) {
                        document.body.removeChild(textarea);
                        return true;
                    } else {
                        console.error('execCommand 复制失败');
                        document.body.removeChild(textarea);
                        return false;
                    }
                } catch (err) {
                    console.error('execCommand 复制出错: ', err);
                    document.body.removeChild(textarea);
                    return false;
                }
            }

            function showCopyTextSuccess(element) {
                element.innerHTML = '✅';
                setTimeout(() => {
                    element.innerHTML = '📃';
                }, 500);
            }

            function showCopyCodeSuccess(element) {
                element.innerHTML = '已复制';
                setTimeout(() => {
                    element.innerHTML = '复制';
                }, 500);
            }
        </script>
        <script>
            function copyCode(button) {
                const codeBlock = button.closest('.code-block').querySelector('pre');
                const code = codeBlock.innerText;
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    // 使用 Clipboard API 复制
                    navigator.clipboard.writeText(code).then(() => {
                        showCopyCodeSuccess(button);
                        return;
                    });
                } else if(fallbackCopyText(code, button)) {
                    // 使用备用方法复制
                    showCopyCodeSuccess(button);
                }
            }
        </script>
    """
    # 使用Streamlit的components.html函数渲染HTML
    components.html(bot_html, height=600)