import json
import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
import threading
from chat_logic import ChatSession

class ChatbotUI:
    """User interface for the chatbot"""
    
    def __init__(self, config_path="config.json"):
        """Initialize the user interface
        
        Args:
            config_path: Path to the configuration file
        """
        # Load configuration
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # Create chat session
        self.chat_session = ChatSession(config_path)
        
        # Create main window
        self.root = tk.Tk()
        self.root.title(self.config['ui']['title'])
        self.root.geometry(f"{self.config['ui']['width']}x{self.config['ui']['height']}")
        
        # Set theme
        self.theme = self.config['ui']['theme']
        self.setup_theme()
        
        # Create UI components
        self.create_widgets()
        
        # Loading status
        self.is_model_loaded = False
        self.is_generating = False
    
    def setup_theme(self):
        """Set UI theme"""
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
        """Create UI components"""
        # Create main frame
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Chat history display area
        history_frame = tk.Frame(main_frame, bg=self.bg_color)
        history_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Chat history label
        history_label = tk.Label(history_frame, text="Chat History", bg=self.bg_color, fg=self.fg_color)
        history_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Chat history text area
        self.chat_history_text = scrolledtext.ScrolledText(
            history_frame, 
            wrap=tk.WORD, 
            bg=self.input_bg, 
            fg=self.input_fg,
            font=("TkDefaultFont", 10)
        )
        self.chat_history_text.pack(fill=tk.BOTH, expand=True)
        self.chat_history_text.config(state=tk.DISABLED)  # Set to read-only
        
        # Input area
        input_frame = tk.Frame(main_frame, bg=self.bg_color)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Input label
        input_label = tk.Label(input_frame, text="Enter Message", bg=self.bg_color, fg=self.fg_color)
        input_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Input text area
        self.input_text = scrolledtext.ScrolledText(
            input_frame, 
            wrap=tk.WORD, 
            height=4, 
            bg=self.input_bg, 
            fg=self.input_fg,
            font=("TkDefaultFont", 10),
            insertbackground=self.input_fg,  # Set cursor color to make it visible
            insertwidth=2  # Increase cursor width
        )
        self.input_text.pack(fill=tk.X)
        self.input_text.bind("<Return>", self.on_enter_key)
        
        # Ensure input box gets focus
        self.root.after(100, lambda: self.input_text.focus_set())
        
        # Button area
        button_frame = tk.Frame(main_frame, bg=self.bg_color, height=40)  # Increase height
        button_frame.pack(fill=tk.X, pady=5)  # Add vertical margin
        button_frame.pack_propagate(False)  # Prevent frame from being compressed by child components
        
        # Create button style
        button_style = {
            'bg': self.button_bg, 
            'fg': self.button_fg,
            'padx': 15,         # Increase horizontal padding
            'pady': 5,          # Add vertical padding
            'relief': tk.RAISED,  # Use RAISED style for a slight 3D effect
            'borderwidth': 1,   # Keep minimal border
            'highlightthickness': 0,  # Remove highlight border
            'font': ('TkDefaultFont', 10),  # Ensure appropriate font size
            'width': 8  # Fixed width to ensure button is fully displayed
        }
        
        # Send button
        self.send_button = tk.Button(
            button_frame, 
            text="Send", 
            command=self.send_message,
            **button_style
        )
        self.send_button.pack(side=tk.RIGHT, padx=(5, 0), pady=5)  # Add margin
        
        # Clear button
        clear_button_style = button_style.copy()
        clear_button_style['width'] = 10  # Increase width to fit "Clear History" text
        self.clear_button = tk.Button(
            button_frame, 
            text="Clear History", 
            command=self.clear_history,
            **clear_button_style
        )
        self.clear_button.pack(side=tk.RIGHT, padx=(5, 0), pady=5)  # Add margin
        
        # Load model button
        load_button_style = button_style.copy()
        load_button_style['width'] = 10  # Increase width to fit "Load Model" text
        self.load_button = tk.Button(
            button_frame, 
            text="Load Model", 
            command=self.load_model,
            **load_button_style
        )
        self.load_button.pack(side=tk.LEFT, padx=(0, 5), pady=5)  # Add margin
        
        # Status label
        self.status_label = tk.Label(
            main_frame, 
            text="Status: Model not loaded", 
            bg=self.bg_color, 
            fg=self.fg_color,
            anchor=tk.W
        )
        self.status_label.pack(fill=tk.X, pady=(5, 0))
    
    def load_model(self):
        """Load model"""
        if self.is_model_loaded:
            messagebox.showinfo("Notice", "Model already loaded")
            return
        
        self.status_label.config(text="Status: Loading model...")
        self.load_button.config(state=tk.DISABLED)
        
        # Load model in a new thread
        threading.Thread(target=self._load_model_thread, daemon=True).start()
    
    def _load_model_thread(self):
        """Load model in a new thread"""
        success = self.chat_session.initialize()
        
        # Update UI (in the main thread)
        self.root.after(0, self._update_ui_after_loading, success)
    
    def _update_ui_after_loading(self, success):
        """Update UI after model loading"""
        if success:
            self.is_model_loaded = True
            self.status_label.config(text="Status: Model loaded")
            self.load_button.config(text="Loaded", state=tk.DISABLED)
            self.append_to_history("System", "Model loading complete, you can start chatting now!")
        else:
            self.status_label.config(text="Status: Model loading failed")
            self.load_button.config(state=tk.NORMAL)
            messagebox.showerror("Error", "Model loading failed, please check configuration and model path")
    
    def on_enter_key(self, event):
        """Handle Enter key event"""
        # If Shift+Enter is pressed, insert a newline
        if event.state & 0x1:  # Shift key is pressed
            return
        
        # Otherwise send the message
        self.send_message()
        return "break"  # Prevent default Enter key behavior
    
    def send_message(self):
        """Send message"""
        if not self.is_model_loaded:
            messagebox.showinfo("Notice", "Please load the model first")
            return
        
        if self.is_generating:
            messagebox.showinfo("Notice", "Generating response, please wait")
            return
        
        # Get user input
        user_input = self.input_text.get("1.0", tk.END).strip()
        if not user_input:
            return
        
        # Clear input box
        self.input_text.delete("1.0", tk.END)
        
        # Display user input
        self.append_to_history("User", user_input)
        
        # Set generation status
        self.is_generating = True
        self.status_label.config(text="Status: Generating response...")
        self.send_button.config(state=tk.DISABLED)
        
        # Generate response in a new thread
        threading.Thread(target=self._generate_response_thread, args=(user_input,), daemon=True).start()
    
    def _generate_response_thread(self, user_input):
        """Generate response in a new thread"""
        try:
            response = self.chat_session.get_response(user_input)
            
            # Update UI (in the main thread)
            self.root.after(0, self._update_ui_after_response, response)
        except Exception as e:
            self.root.after(0, self._update_ui_after_error, str(e))
    
    def _update_ui_after_response(self, response):
        """Update UI after response generation"""
        # Display assistant response
        self.append_to_history("Assistant", response)
        
        # Reset generation status
        self.is_generating = False
        self.status_label.config(text="Status: Ready")
        self.send_button.config(state=tk.NORMAL)
    
    def _update_ui_after_error(self, error_msg):
        """Update UI after an error occurs"""
        messagebox.showerror("Error", f"Error generating response: {error_msg}")
        
        # Reset generation status
        self.is_generating = False
        self.status_label.config(text="Status: Error occurred")
        self.send_button.config(state=tk.NORMAL)
    
    def append_to_history(self, role, message):
        """Add message to chat history display area
        
        Args:
            role: Role name, such as "User", "Assistant"
            message: Message content
        """
        self.chat_history_text.config(state=tk.NORMAL)  # Temporarily set to editable
        
        # Add separator (if not the first message)
        if self.chat_history_text.get("1.0", tk.END).strip():
            self.chat_history_text.insert(tk.END, "\n\n")
        
        # Add role name
        if role == "User":
            self.chat_history_text.insert(tk.END, f"{role}: ", "user_tag")
            self.chat_history_text.tag_configure("user_tag", foreground="blue", font=("TkDefaultFont", 10, "bold"))
        elif role == "Assistant":
            self.chat_history_text.insert(tk.END, f"{role}: ", "assistant_tag")
            self.chat_history_text.tag_configure("assistant_tag", foreground="green", font=("TkDefaultFont", 10, "bold"))
        else:
            self.chat_history_text.insert(tk.END, f"{role}: ", "system_tag")
            self.chat_history_text.tag_configure("system_tag", foreground="gray", font=("TkDefaultFont", 10, "bold"))
        
        # Add message content
        self.chat_history_text.insert(tk.END, message)
        
        # Scroll to bottom
        self.chat_history_text.see(tk.END)
        
        self.chat_history_text.config(state=tk.DISABLED)  # Restore read-only state
    
    def clear_history(self):
        """Clear chat history"""
        if messagebox.askyesno("Confirm", "Are you sure you want to clear the chat history?"):
            # Clear display
            self.chat_history_text.config(state=tk.NORMAL)
            self.chat_history_text.delete("1.0", tk.END)
            self.chat_history_text.config(state=tk.DISABLED)
            
            # Clear session history
            self.chat_session.clear_history()
            
            # Add system message
            self.append_to_history("System", "Chat history cleared")
    
    def run(self):
        """Run the application"""
        self.root.mainloop()
