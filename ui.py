import json
import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
import threading
from chat_logic import ChatSession

class ChatbotUI:
    """聊天机器人的用户界面"""
    
    def __init__(self, config_path="config.json"):
        """初始化用户界面
        
        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # 创建聊天会话
        self.chat_session = ChatSession(config_path)
        
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title(self.config['ui']['title'])
        self.root.geometry(f"{self.config['ui']['width']}x{self.config['ui']['height']}")
        
        # 设置主题
        self.theme = self.config['ui']['theme']
        self.setup_theme()
        
        # 创建UI组件
        self.create_widgets()
        
        # 加载状态
        self.is_model_loaded = False
        self.is_generating = False
    
    def setup_theme(self):
        """设置UI主题"""
        if self.theme == "dark":
            self.bg_color = "#2d2d2d"
            self.fg_color = "#ffffff"
            self.input_bg = "#3d3d3d"
            self.input_fg = "#ffffff"
            self.button_bg = "#4d4d4d"
            self.button_fg = "#ffffff"
        else:  # light theme
            self.bg_color = "#f0f0f0"
            self.fg_color = "#000000"
            self.input_bg = "#ffffff"
            self.input_fg = "#000000"
            self.button_bg = "#e0e0e0"
            self.button_fg = "#000000"
        
        self.root.configure(bg=self.bg_color)
    
    def create_widgets(self):
        """创建UI组件"""
        # 创建主框架
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 聊天历史显示区域
        history_frame = tk.Frame(main_frame, bg=self.bg_color)
        history_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 聊天历史标签
        history_label = tk.Label(history_frame, text="聊天历史", bg=self.bg_color, fg=self.fg_color)
        history_label.pack(anchor=tk.W, pady=(0, 5))
        
        # 聊天历史文本区域
        self.chat_history_text = scrolledtext.ScrolledText(
            history_frame, 
            wrap=tk.WORD, 
            bg=self.input_bg, 
            fg=self.input_fg,
            font=("TkDefaultFont", 10)
        )
        self.chat_history_text.pack(fill=tk.BOTH, expand=True)
        self.chat_history_text.config(state=tk.DISABLED)  # 设为只读
        
        # 输入区域
        input_frame = tk.Frame(main_frame, bg=self.bg_color)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 输入标签
        input_label = tk.Label(input_frame, text="输入消息", bg=self.bg_color, fg=self.fg_color)
        input_label.pack(anchor=tk.W, pady=(0, 5))
        
        # 输入文本区域
        self.input_text = scrolledtext.ScrolledText(
            input_frame, 
            wrap=tk.WORD, 
            height=4, 
            bg=self.input_bg, 
            fg=self.input_fg,
            font=("TkDefaultFont", 10),
            insertbackground=self.input_fg,  # 设置光标颜色，使其可见
            insertwidth=2  # 增加光标宽度
        )
        self.input_text.pack(fill=tk.X)
        self.input_text.bind("<Return>", self.on_enter_key)
        
        # 确保输入框获得焦点
        self.root.after(100, lambda: self.input_text.focus_set())
        
        # 按钮区域
        button_frame = tk.Frame(main_frame, bg=self.bg_color, height=40)  # 增加高度
        button_frame.pack(fill=tk.X, pady=5)  # 添加垂直外边距
        button_frame.pack_propagate(False)  # 防止框架被子组件压缩
        
        # 创建按钮样式
        button_style = {
            'bg': self.button_bg, 
            'fg': self.button_fg,
            'padx': 15,         # 增加水平内边距
            'pady': 5,          # 添加垂直内边距
            'relief': tk.RAISED,  # 使用RAISED样式，有轻微的3D效果
            'borderwidth': 1,   # 保留最小边框
            'highlightthickness': 0,  # 移除高亮边框
            'font': ('TkDefaultFont', 10),  # 确保字体大小合适
            'width': 8  # 固定宽度，确保按钮完全显示
        }
        
        # 发送按钮
        self.send_button = tk.Button(
            button_frame, 
            text="发送", 
            command=self.send_message,
            **button_style
        )
        self.send_button.pack(side=tk.RIGHT, padx=(5, 0), pady=5)  # 添加外边距
        
        # 清除按钮
        clear_button_style = button_style.copy()
        clear_button_style['width'] = 10  # 增加宽度以适应"清除历史"文本
        self.clear_button = tk.Button(
            button_frame, 
            text="清除历史", 
            command=self.clear_history,
            **clear_button_style
        )
        self.clear_button.pack(side=tk.RIGHT, padx=(5, 0), pady=5)  # 添加外边距
        
        # 加载模型按钮
        load_button_style = button_style.copy()
        load_button_style['width'] = 10  # 增加宽度以适应"加载模型"文本
        self.load_button = tk.Button(
            button_frame, 
            text="加载模型", 
            command=self.load_model,
            **load_button_style
        )
        self.load_button.pack(side=tk.LEFT, padx=(0, 5), pady=5)  # 添加外边距
        
        # 状态标签
        self.status_label = tk.Label(
            main_frame, 
            text="状态: 未加载模型", 
            bg=self.bg_color, 
            fg=self.fg_color,
            anchor=tk.W
        )
        self.status_label.pack(fill=tk.X, pady=(5, 0))
    
    def load_model(self):
        """加载模型"""
        if self.is_model_loaded:
            messagebox.showinfo("提示", "模型已经加载")
            return
        
        self.status_label.config(text="状态: 正在加载模型...")
        self.load_button.config(state=tk.DISABLED)
        
        # 在新线程中加载模型
        threading.Thread(target=self._load_model_thread, daemon=True).start()
    
    def _load_model_thread(self):
        """在新线程中加载模型"""
        success = self.chat_session.initialize()
        
        # 更新UI（在主线程中）
        self.root.after(0, self._update_ui_after_loading, success)
    
    def _update_ui_after_loading(self, success):
        """模型加载后更新UI"""
        if success:
            self.is_model_loaded = True
            self.status_label.config(text="状态: 模型已加载")
            self.load_button.config(text="已加载", state=tk.DISABLED)
            self.append_to_history("系统", "模型已加载完成，可以开始聊天了！")
        else:
            self.status_label.config(text="状态: 模型加载失败")
            self.load_button.config(state=tk.NORMAL)
            messagebox.showerror("错误", "模型加载失败，请检查配置和模型路径")
    
    def on_enter_key(self, event):
        """处理回车键事件"""
        # 如果按下Shift+Enter，则插入换行符
        if event.state & 0x1:  # Shift键被按下
            return
        
        # 否则发送消息
        self.send_message()
        return "break"  # 阻止默认的Enter键行为
    
    def send_message(self):
        """发送消息"""
        if not self.is_model_loaded:
            messagebox.showinfo("提示", "请先加载模型")
            return
        
        if self.is_generating:
            messagebox.showinfo("提示", "正在生成回复，请稍候")
            return
        
        # 获取用户输入
        user_input = self.input_text.get("1.0", tk.END).strip()
        if not user_input:
            return
        
        # 清空输入框
        self.input_text.delete("1.0", tk.END)
        
        # 显示用户输入
        self.append_to_history("用户", user_input)
        
        # 设置生成状态
        self.is_generating = True
        self.status_label.config(text="状态: 正在生成回复...")
        self.send_button.config(state=tk.DISABLED)
        
        # 在新线程中生成回复
        threading.Thread(target=self._generate_response_thread, args=(user_input,), daemon=True).start()
    
    def _generate_response_thread(self, user_input):
        """在新线程中生成回复"""
        try:
            response = self.chat_session.get_response(user_input)
            
            # 更新UI（在主线程中）
            self.root.after(0, self._update_ui_after_response, response)
        except Exception as e:
            self.root.after(0, self._update_ui_after_error, str(e))
    
    def _update_ui_after_response(self, response):
        """回复生成后更新UI"""
        # 显示助手回复
        self.append_to_history("助手", response)
        
        # 重置生成状态
        self.is_generating = False
        self.status_label.config(text="状态: 已就绪")
        self.send_button.config(state=tk.NORMAL)
    
    def _update_ui_after_error(self, error_msg):
        """发生错误后更新UI"""
        messagebox.showerror("错误", f"生成回复时出错: {error_msg}")
        
        # 重置生成状态
        self.is_generating = False
        self.status_label.config(text="状态: 发生错误")
        self.send_button.config(state=tk.NORMAL)
    
    def append_to_history(self, role, message):
        """将消息添加到聊天历史显示区域
        
        Args:
            role: 角色名称，如"用户"、"助手"
            message: 消息内容
        """
        self.chat_history_text.config(state=tk.NORMAL)  # 临时设为可编辑
        
        # 添加分隔线（如果不是第一条消息）
        if self.chat_history_text.get("1.0", tk.END).strip():
            self.chat_history_text.insert(tk.END, "\n\n")
        
        # 添加角色名
        if role == "用户":
            self.chat_history_text.insert(tk.END, f"{role}: ", "user_tag")
            self.chat_history_text.tag_configure("user_tag", foreground="blue", font=("TkDefaultFont", 10, "bold"))
        elif role == "助手":
            self.chat_history_text.insert(tk.END, f"{role}: ", "assistant_tag")
            self.chat_history_text.tag_configure("assistant_tag", foreground="green", font=("TkDefaultFont", 10, "bold"))
        else:
            self.chat_history_text.insert(tk.END, f"{role}: ", "system_tag")
            self.chat_history_text.tag_configure("system_tag", foreground="gray", font=("TkDefaultFont", 10, "bold"))
        
        # 添加消息内容
        self.chat_history_text.insert(tk.END, message)
        
        # 滚动到底部
        self.chat_history_text.see(tk.END)
        
        self.chat_history_text.config(state=tk.DISABLED)  # 恢复只读状态
    
    def clear_history(self):
        """清除聊天历史"""
        if messagebox.askyesno("确认", "确定要清除聊天历史吗？"):
            # 清除显示
            self.chat_history_text.config(state=tk.NORMAL)
            self.chat_history_text.delete("1.0", tk.END)
            self.chat_history_text.config(state=tk.DISABLED)
            
            # 清除会话历史
            self.chat_session.clear_history()
            
            # 添加系统消息
            self.append_to_history("系统", "聊天历史已清除")
    
    def run(self):
        """运行应用程序"""
        self.root.mainloop()
