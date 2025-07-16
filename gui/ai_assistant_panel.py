# file: gui/ai_assistant_panel.py

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import datetime
import json
import os
from typing import Dict, List, Any, Optional
import anthropic
import base64
import io
import numpy as np
from PIL import Image

class AIAssistantPanel:
    def __init__(self, parent_frame, main_window):
        """Initialize the AI Assistant Panel for Claude integration."""
        self.parent_frame = parent_frame
        self.main_window = main_window
        self.chat_history = []
        self.is_processing = False
        
        # Initialize Claude client
        self.claude_client = None
        self.api_key = None
        self.current_model = None  # Cache the working model
        self.current_analysis_summary = None
        self.current_plot_image = None
        self.auto_update_plot = True  # Auto-update plot view when analysis changes
        self._load_api_key()
        
        # Create UI components
        self.create_ui()
        
        # Welcome message with streaming and enhanced formatting
        welcome_msg = "**[ANALYSIS]**\n\nScientific Analysis Assistant Ready!\n\nHi! I'm your AI companion for photometry data analysis. I can help you:\n\n• Analyze signal patterns and correlations\n• Test statistical hypotheses\n• Generate custom plots and visualizations\n• Discover biomarkers and insights\n• Interpret your experimental results\n\n**[KEY POINTS]**\n\n• Share your data context for personalized insights\n• Ask me to explain specific analysis results\n• Request plot interpretations and recommendations\n• Get help with experimental design\n\nWhat would you like to explore in your data?"
        # Use a delay to show the welcome message with streaming after UI is ready
        self.main_window.root.after(500, lambda: self._start_streaming_message(welcome_msg, 'assistant'))
        
        # Add F1 key binding for quick help
        self.main_window.root.bind('<F1>', lambda e: self.show_quick_help())
    
    def _load_api_key(self):
        """Load Claude API key from environment or config file."""
        # Try environment variable first
        self.api_key = os.getenv('CLAUDE_API_KEY')
        
        # Try config file
        if not self.api_key:
            config_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'api_keys.json')
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                        self.api_key = config.get('claude_api_key')
                except Exception as e:
                    print(f"Error loading API key from config: {e}")
        
        # Initialize Claude client if API key is available
        if self.api_key:
            try:
                self.claude_client = anthropic.Anthropic(api_key=self.api_key)
                print("Claude API client initialized successfully")
            except Exception as e:
                print(f"Error initializing Claude client: {e}")
                self.claude_client = None
    
    def create_ui(self):
        """Create the chat interface UI components."""
        # Main container
        self.main_frame = ttk.Frame(self.parent_frame)
        self.main_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Title
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(fill='x', pady=(0, 10))
        
        title_label = ttk.Label(title_frame, text="AI Scientific Assistant", 
                               font=('Arial', 12, 'bold'))
        title_label.pack(side='left')
        
        # API Status indicator
        self.status_label = ttk.Label(title_frame, text="●", 
                                     foreground='green' if self.claude_client else 'red')
        self.status_label.pack(side='right')
        
        # Chat display area
        self.chat_frame = ttk.Frame(self.main_frame)
        self.chat_frame.pack(fill='both', expand=True)
        
        # Chat history with scrollbar
        self.chat_display = scrolledtext.ScrolledText(
            self.chat_frame,
            wrap=tk.WORD,
            width=50,
            height=20,
            font=('Arial', 10),
            state='disabled'
        )
        self.chat_display.pack(fill='both', expand=True)
        
        # Configure text tags for styling with improved appearance and better separation
        self.chat_display.tag_configure('user_label', foreground='#1f77b4', font=('Arial', 11, 'bold'), 
                                       spacing1=8, spacing3=4)
        self.chat_display.tag_configure('user_message', foreground='#2c3e50', font=('Arial', 10), 
                                       lmargin1=20, lmargin2=20, spacing3=8, 
                                       background='#f8f9fa', relief='flat', borderwidth=1)
        self.chat_display.tag_configure('assistant_label', foreground='#2d7d2d', font=('Arial', 11, 'bold'),
                                       spacing1=8, spacing3=4)
        self.chat_display.tag_configure('assistant_message', foreground='#2c3e50', font=('Arial', 10), 
                                       lmargin1=20, lmargin2=20, spacing3=8,
                                       background='#f0f8f0', relief='flat', borderwidth=1)
        self.chat_display.tag_configure('system_label', foreground='#8b4513', font=('Arial', 10, 'bold'),
                                       spacing1=4, spacing3=2)
        self.chat_display.tag_configure('system_message', foreground='#666666', font=('Arial', 9, 'italic'), 
                                       lmargin1=20, lmargin2=20, spacing3=6,
                                       background='#fff8dc', relief='flat', borderwidth=1)
        self.chat_display.tag_configure('timestamp', foreground='#999999', font=('Arial', 8), spacing3=2)
        self.chat_display.tag_configure('thinking', foreground='#666666', font=('Arial', 9, 'italic'), 
                                       background='#f5f5f5')
        
        # Enhanced formatting tags with better visual hierarchy
        self.chat_display.tag_configure('heading', foreground='#1f77b4', font=('Arial', 12, 'bold'), 
                                       spacing1=8, spacing3=4)
        self.chat_display.tag_configure('subheading', foreground='#2d7d2d', font=('Arial', 11, 'bold'), 
                                       spacing1=6, spacing3=3)
        self.chat_display.tag_configure('bullet', foreground='#2d7d2d', font=('Arial', 10), 
                                       lmargin1=25, lmargin2=25)
        self.chat_display.tag_configure('numbered', foreground='#2d7d2d', font=('Arial', 10), 
                                       lmargin1=25, lmargin2=25)
        self.chat_display.tag_configure('code', foreground='#d73027', font=('Courier', 9), 
                                       background='#f5f5f5', relief='solid', borderwidth=1)
        self.chat_display.tag_configure('code_block', foreground='#2c3e50', font=('Courier', 9), 
                                       background='#f8f8f8', relief='solid', borderwidth=1,
                                       lmargin1=20, lmargin2=20, spacing1=4, spacing3=4)
        self.chat_display.tag_configure('emphasis', foreground='#2c3e50', font=('Arial', 10, 'italic'))
        self.chat_display.tag_configure('strong', foreground='#2c3e50', font=('Arial', 10, 'bold'))
        self.chat_display.tag_configure('keypoint', foreground='#1f77b4', font=('Arial', 10, 'bold'), 
                                       background='#f0f8ff', spacing1=4, spacing3=4)
        self.chat_display.tag_configure('summary', foreground='#2d7d2d', font=('Arial', 10), 
                                       background='#f8fff8', spacing1=4, spacing3=4,
                                       lmargin1=15, lmargin2=15)
        self.chat_display.tag_configure('separator', foreground='#cccccc', font=('Arial', 8), 
                                       spacing1=4, spacing3=4, justify='center')
        self.chat_display.tag_configure('message_separator', foreground='#e0e0e0', font=('Arial', 6), 
                                       spacing1=6, spacing3=6, justify='center')
        self.chat_display.tag_configure('quote', foreground='#666666', font=('Arial', 10, 'italic'), 
                                       background='#f9f9f9', lmargin1=30, lmargin2=30,
                                       spacing1=4, spacing3=4)
        self.chat_display.tag_configure('highlight', foreground='#8b4513', font=('Arial', 10, 'bold'), 
                                       background='#fff8dc')
        
        # Animation state for streaming text
        self.is_streaming = False
        self.stream_buffer = ""
        self.stream_position = 0
        self.stream_speed = 25  # characters per second
        self.stream_timer = None
        self.current_message_start_index = None
        self.typing_indicator_active = False
        
        # Input area
        input_frame = ttk.Frame(self.main_frame)
        input_frame.pack(fill='x', pady=(10, 0))
        
        # Message input
        self.message_entry = tk.Text(input_frame, height=3, wrap=tk.WORD, font=('Arial', 10))
        self.message_entry.pack(fill='x', pady=(0, 5))
        
        # Button frame
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill='x')
        
        # Send button
        self.send_button = ttk.Button(button_frame, text="Send Message", 
                                     command=self.send_message)
        self.send_button.pack(side='left', padx=(0, 5))
        
        # Clear button
        clear_button = ttk.Button(button_frame, text="Clear Chat", 
                                 command=self.clear_chat)
        clear_button.pack(side='left', padx=(0, 5))
        
        # Data context button
        context_button = ttk.Button(button_frame, text="Share Data Context", 
                                   command=self.share_data_context)
        context_button.pack(side='left', padx=(0, 5))
        
        # Plot view button
        plot_button = ttk.Button(button_frame, text="Update Plot View", 
                                command=self.update_claude_with_current_view)
        plot_button.pack(side='left', padx=(0, 5))
        
        # Auto-update toggle
        self.auto_update_var = tk.BooleanVar(value=True)
        auto_update_check = ttk.Checkbutton(button_frame, text="Auto-update", 
                                           variable=self.auto_update_var,
                                           command=self._toggle_auto_update)
        auto_update_check.pack(side='left', padx=(0, 5))
        
        # Help button
        help_button = ttk.Button(button_frame, text="Help", 
                               command=self.show_help)
        help_button.pack(side='right', padx=(0, 5))
        
        # API settings button
        settings_button = ttk.Button(button_frame, text="API Settings", 
                                   command=self.show_api_settings)
        settings_button.pack(side='right')
        
        # Bind keyboard events for better interaction
        self.message_entry.bind('<Control-Return>', lambda e: self.send_message())
        self.message_entry.bind('<Return>', self._on_enter_key)
        self.message_entry.bind('<KeyPress>', self._on_key_press)
        
        # Set focus to message entry by default
        self.message_entry.focus_set()
        
        # Progress bar for processing
        self.progress_frame = ttk.Frame(self.main_frame)
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='indeterminate')
        self.processing_label = ttk.Label(self.progress_frame, text="Processing...")
    
    def add_message(self, message: str, sender: str, timestamp: bool = True):
        """Add a message to the chat display (non-streaming version)."""
        self.chat_display.config(state='normal')
        
        # Add visual separator before each message for better separation
        if sender != 'system':
            self.chat_display.insert(tk.END, "\n", 'message_separator')
        
        # Add timestamp if requested
        if timestamp:
            time_str = datetime.datetime.now().strftime("%H:%M:%S")
            self.chat_display.insert(tk.END, f"[{time_str}] ", 'timestamp')
        
        # Add sender with enhanced styling and icons
        if sender == 'user':
            self.chat_display.insert(tk.END, "You 💬", 'user_label')
            message_tag = 'user_message'
        elif sender == 'assistant':
            self.chat_display.insert(tk.END, "Claude ✨", 'assistant_label')
            message_tag = 'assistant_message'
        elif sender == 'system':
            self.chat_display.insert(tk.END, "System ⚙️", 'system_label')
            message_tag = 'system_message'
        else:
            message_tag = 'assistant_message'
        
        self.chat_display.insert(tk.END, "\n", 'timestamp')
        
        # Format and add message with rich text
        formatted_message = self._format_message_text(message)
        self._insert_formatted_text(formatted_message, message_tag)
        
        # Add message separator
        self.chat_display.insert(tk.END, "\n")
        if sender != 'system':
            self.chat_display.insert(tk.END, "─" * 50 + "\n", 'message_separator')
        
        # Scroll to bottom
        self.chat_display.see(tk.END)
        self.chat_display.config(state='disabled')
        
        # Update chat history
        self.chat_history.append({
            'timestamp': datetime.datetime.now().isoformat(),
            'sender': sender,
            'message': message
        })
    
    def add_assistant_message(self, message: str):
        """Add an assistant message with proper formatting."""
        self.add_message(message, 'assistant')
    
    def add_user_message(self, message: str):
        """Add a user message."""
        self.add_message(message, 'user')
    
    def add_system_message(self, message: str):
        """Add a system message."""
        self.add_message(message, 'system')
    
    def send_message(self):
        """Send user message to Claude API."""
        if self.is_processing:
            return
        
        # Get user message
        user_message = self.message_entry.get(1.0, tk.END).strip()
        if not user_message:
            return
        
        # Clear input
        self.message_entry.delete(1.0, tk.END)
        
        # Add user message to chat
        self.add_user_message(user_message)
        
        # Check if Claude client is available
        if not self.claude_client:
            self.add_system_message("WARNING: Claude API not available. Please check your API key in settings.")
            return
        
        # Start processing
        self.start_processing()
        
        # Send to Claude API in a separate thread
        thread = threading.Thread(target=self._process_message, args=(user_message,))
        thread.daemon = True
        thread.start()
    
    def _get_available_model(self):
        """Get the best available Claude model."""
        # Return cached model if available
        if self.current_model:
            return self.current_model
        
        # List of models to try in order of preference
        models_to_try = [
            "claude-3-5-sonnet-20241022",  # Latest Claude 3.5 Sonnet
            "claude-3-5-sonnet-20240620",  # Previous Claude 3.5 Sonnet  
            "claude-3-sonnet-20240229",    # Claude 3 Sonnet
            "claude-3-haiku-20240307"      # Claude 3 Haiku (fallback)
        ]
        
        for model in models_to_try:
            try:
                # Test the model with a simple message
                test_response = self.claude_client.messages.create(
                    model=model,
                    max_tokens=10,
                    messages=[{"role": "user", "content": "Hi"}]
                )
                print(f"Using Claude model: {model}")
                self.current_model = model  # Cache the working model
                return model
            except Exception as e:
                print(f"Model {model} not available: {e}")
                continue
        
        # If no model works, return the most likely to work
        self.current_model = "claude-3-5-sonnet-20241022"
        return self.current_model
    
    def _process_message(self, user_message: str):
        """Process message with Claude API in background thread."""
        try:
            # Get current data context
            data_context = self.get_current_data_context()
            
            # Create system prompt with data context and plot visualization
            system_prompt = self._create_system_prompt(data_context)
            
            # Add GUI control context
            gui_functions = self._get_gui_functions()
            if gui_functions:
                system_prompt += f"\n\nAvailable GUI Control Functions:\n{gui_functions}"
            
            # Add current plot analysis summary
            if hasattr(self, 'current_analysis_summary'):
                system_prompt += f"\n\nCurrent Plot Analysis:\n{json.dumps(self.current_analysis_summary, indent=2)}"
            
            # Get best available model
            model = self._get_available_model()
            
            # Prepare message content
            message_content = []
            
            # Add text content
            message_content.append({
                "type": "text",
                "text": user_message
            })
            
            # Add plot image if available
            if hasattr(self, 'current_plot_image') and self.current_plot_image:
                message_content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": self.current_plot_image
                    }
                })
            
            # Add analysis plots if available
            analysis_plots = self.capture_analysis_plots()
            for plot_type, plot_data in analysis_plots.items():
                if plot_data:
                    message_content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": plot_data
                        }
                    })
            
            # Send to Claude
            response = self.claude_client.messages.create(
                model=model,
                max_tokens=4000,
                temperature=0.1,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": message_content}
                ]
            )
            
            # Extract response text
            response_text = response.content[0].text
            
            # Add response to chat in main thread
            self.main_window.root.after(0, self._add_claude_response, response_text)
            
        except Exception as e:
            error_msg = f"Error communicating with Claude: {str(e)}"
            self.main_window.root.after(0, self.add_system_message, error_msg)
        
        finally:
            # Stop processing in main thread
            self.main_window.root.after(0, self.stop_processing)
    
    def _add_claude_response(self, response_text: str):
        """Add Claude's response to chat display with streaming animation."""
        # Check for GUI actions in the response
        action_results = []
        if "**ACTION:**" in response_text:
            # Extract and execute actions
            import re
            actions = re.findall(r'\*\*ACTION:\*\*\s*([^\n]+)', response_text)
            for action in actions:
                result = self._execute_gui_action(action)
                action_results.append(f"Action executed: {result}")
        
        # Enhance response with better formatting markers
        enhanced_response = self._enhance_response_formatting(response_text)
        
        # Use streaming display for Claude's response
        self._start_streaming_message(enhanced_response, 'assistant')
        
        # Add action results after streaming is complete
        if action_results:
            def add_action_results():
                for result in action_results:
                    self.add_system_message(result)
            # Schedule action results to be added after streaming completes
            self.main_window.root.after(len(enhanced_response) * 1000 // self.stream_speed + 500, add_action_results)
    
    def _create_system_prompt(self, data_context: Dict) -> str:
        """Create system prompt with current data context."""
        return f"""You are an expert neuroscience data analysis assistant specializing in photometry data analysis. 

You are integrated into a Python-based photometry analysis GUI and have access to the user's current data context.

Current Data Context:
{json.dumps(data_context, indent=2)}

Your capabilities:
1. Analyze signal patterns, correlations, and statistics
2. Test scientific hypotheses 
3. Generate insights about biological patterns
4. Suggest analysis approaches
5. Explain photometry concepts and methodology

Guidelines:
- Be scientifically accurate and precise
- Provide actionable insights
- Ask clarifying questions when needed
- Suggest specific analysis steps
- Use markdown formatting for clarity
- Keep responses concise but thorough

You can reference the user's current data, visible plots, and analysis results in your responses.

IMPORTANT: You can control the GUI directly using the available functions. When the user requests actions like:
- "Change the filter to 0.1-10 Hz" 
- "Remove noise from 10-20 seconds"
- "Set amplitude to 5"
- "Apply lowpass filter at 2 Hz"

Use the format: **ACTION:** function_name(parameter1=value1, parameter2=value2)

The system will execute these functions automatically.

VISUAL CAPABILITIES: You can see the actual plots and visualizations. When plot images are shared, analyze:
- Signal patterns and trends
- Noise levels and artifacts
- Peak/valley characteristics
- Time series behavior
- Amplitude ranges
- Filter effects
- Any visual anomalies or interesting features

ANALYSIS PLOTS: You can also see specialized analysis plots:
- PSTH (Peri-Stimulus Time Histogram): Shows averaged signal response around detected events
- Correlation Analysis: Shows signal correlations, cross-correlations, and causality analysis
- Peak-Valley Analysis: Shows detected peaks and valleys with their characteristics

When analyzing these plots, provide detailed interpretations of:
- PSTH patterns and their biological significance
- Correlation strength and timing relationships
- Event detection accuracy and parameters
- Statistical significance of results
- Experimental implications

Provide detailed visual analysis based on what you observe in all plots."""
    
    def get_current_data_context(self) -> Dict[str, Any]:
        """Get current data context from the main window."""
        try:
            # Get downsample factor safely
            downsample_factor = getattr(self.main_window, 'downsample_factor', 1)
            if hasattr(downsample_factor, 'get'):
                downsample_factor = downsample_factor.get()
            
            context = {
                "session_info": {
                    "has_primary_data": self.main_window.primary_data is not None,
                    "has_secondary_data": self.main_window.secondary_data is not None,
                    "downsample_factor": downsample_factor
                },
                "data_summary": {},
                "visible_signals": {},
                "current_analysis": {}
            }
            
            # Add primary data info
            if self.main_window.primary_data:
                primary = self.main_window.primary_data
                try:
                    # Get duration safely
                    duration = 0
                    if 'time_raw' in primary and len(primary['time_raw']) > 0:
                        duration = float(primary['time_raw'][-1])
                    
                    context["data_summary"]["primary"] = {
                        "duration_seconds": duration,
                        "sampling_rate": float(primary.get('fs', 1000)),
                        "num_samples": len(primary.get('time_raw', [])),
                        "signals_available": [str(key) for key in primary.keys()]
                    }
                except Exception as e:
                    print(f"Error processing primary data: {e}")
                    context["data_summary"]["primary"] = {"error": "Could not process primary data"}
            
            # Add secondary data info
            if self.main_window.secondary_data:
                secondary = self.main_window.secondary_data
                try:
                    # Get duration safely
                    duration = 0
                    if 'time_raw' in secondary and len(secondary['time_raw']) > 0:
                        duration = float(secondary['time_raw'][-1])
                    
                    context["data_summary"]["secondary"] = {
                        "duration_seconds": duration,
                        "sampling_rate": float(secondary.get('fs', 1000)),
                        "num_samples": len(secondary.get('time_raw', [])),
                        "signals_available": [str(key) for key in secondary.keys()]
                    }
                except Exception as e:
                    print(f"Error processing secondary data: {e}")
                    context["data_summary"]["secondary"] = {"error": "Could not process secondary data"}
            
            # Add visibility states - safely get values from tkinter variables
            context["visible_signals"] = {}
            try:
                if hasattr(self.main_window, 'primary_dff_var'):
                    context["visible_signals"]["primary_dff"] = self.main_window.primary_dff_var.get()
                if hasattr(self.main_window, 'primary_raw_var'):
                    context["visible_signals"]["primary_raw"] = self.main_window.primary_raw_var.get()
                if hasattr(self.main_window, 'primary_control_var'):
                    context["visible_signals"]["primary_control"] = self.main_window.primary_control_var.get()
                if hasattr(self.main_window, 'primary_ttl1_var'):
                    context["visible_signals"]["primary_ttl1"] = self.main_window.primary_ttl1_var.get()
                if hasattr(self.main_window, 'primary_ttl2_var'):
                    context["visible_signals"]["primary_ttl2"] = self.main_window.primary_ttl2_var.get()
                if hasattr(self.main_window, 'secondary_dff_var'):
                    context["visible_signals"]["secondary_dff"] = self.main_window.secondary_dff_var.get()
                if hasattr(self.main_window, 'secondary_raw_var'):
                    context["visible_signals"]["secondary_raw"] = self.main_window.secondary_raw_var.get()
                if hasattr(self.main_window, 'secondary_control_var'):
                    context["visible_signals"]["secondary_control"] = self.main_window.secondary_control_var.get()
                if hasattr(self.main_window, 'secondary_ttl1_var'):
                    context["visible_signals"]["secondary_ttl1"] = self.main_window.secondary_ttl1_var.get()
                if hasattr(self.main_window, 'secondary_ttl2_var'):
                    context["visible_signals"]["secondary_ttl2"] = self.main_window.secondary_ttl2_var.get()
            except Exception as e:
                print(f"Error getting visibility states: {e}")
                context["visible_signals"] = {"error": "Could not retrieve visibility states"}
            
            return context
            
        except Exception as e:
            print(f"Error getting data context: {e}")
            return {"error": f"Could not retrieve data context: {str(e)}"}
    
    def _get_gui_functions(self) -> str:
        """Get available GUI control functions."""
        functions = """
Available GUI Control Functions:

1. **set_filter_parameters(low_cutoff=0.001, high_cutoff=5.0, filter_type='Bandpass')**
   - Set filter parameters and apply
   - filter_type: 'Lowpass', 'Highpass', 'Bandpass', 'Bandstop'

2. **apply_blanking(start_time=10.0, end_time=20.0)**
   - Remove noise/artifacts from specified time range
   - Times in seconds

3. **set_peak_detection_params(prominence=5.0, width_s=0.5, distance_s=2.0)**
   - Configure peak detection parameters

4. **detect_peaks_valleys(mode='Peak')**
   - Run peak or valley detection
   - mode: 'Peak' or 'Valley'

5. **set_plot_visibility(signal_type='primary_dff', visible=True)**
   - Show/hide plot signals
   - signal_type: 'primary_dff', 'primary_raw', 'secondary_dff', etc.

6. **set_downsample_factor(factor=50)**
   - Set downsampling factor for performance

7. **apply_advanced_denoising(aggressive=True)**
   - Apply advanced denoising algorithms

8. **reset_plot_view()**
   - Reset plot zoom and view to show all data

Examples:
- "Apply lowpass filter at 2 Hz" → set_filter_parameters(high_cutoff=2.0, filter_type='Lowpass')
- "Remove noise from 10-20 seconds" → apply_blanking(start_time=10.0, end_time=20.0)
- "Detect peaks with prominence 3" → set_peak_detection_params(prominence=3.0)
        """
        return functions.strip()
    
    def _execute_gui_action(self, action_text: str):
        """Execute GUI action from AI response."""
        try:
            # Parse action format: function_name(param1=value1, param2=value2)
            import re
            match = re.match(r'(\w+)\((.*)\)', action_text.strip())
            if not match:
                return f"Invalid action format: {action_text}"
            
            function_name = match.group(1)
            params_str = match.group(2)
            
            # Parse parameters
            params = {}
            if params_str:
                for param in params_str.split(','):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Convert value to appropriate type
                        if value.startswith("'") and value.endswith("'"):
                            params[key] = value[1:-1]  # String
                        elif value.startswith('"') and value.endswith('"'):
                            params[key] = value[1:-1]  # String
                        elif value.lower() == 'true':
                            params[key] = True
                        elif value.lower() == 'false':
                            params[key] = False
                        else:
                            try:
                                params[key] = float(value)
                            except ValueError:
                                params[key] = value
            
            # Execute the function
            return self._call_gui_function(function_name, params)
            
        except Exception as e:
            return f"Error executing action: {str(e)}"
    
    def _call_gui_function(self, function_name: str, params: dict) -> str:
        """Call the actual GUI function."""
        try:
            if function_name == 'set_filter_parameters':
                # Set filter parameters
                if 'low_cutoff' in params:
                    self.main_window.low_cutoff.set(params['low_cutoff'])
                if 'high_cutoff' in params:
                    self.main_window.high_cutoff.set(params['high_cutoff'])
                if 'filter_type' in params:
                    self.main_window.filter_type.set(params['filter_type'])
                
                # Apply the filter
                self.main_window.root.after(0, self.main_window.update_filter)
                
                # Auto-update plot view after filter change
                if self.auto_update_plot:
                    self.main_window.root.after(1000, self.update_claude_with_current_view)
                
                return f"Filter applied: {params}"
            
            elif function_name == 'apply_blanking':
                # Apply blanking to remove noise
                start_time = params.get('start_time', 0)
                end_time = params.get('end_time', 0)
                
                # Add blanking region
                blanking_region = {'start': start_time, 'end': end_time}
                self.main_window.blanking_regions.append(blanking_region)
                
                # Apply blanking
                self.main_window.root.after(0, self.main_window.reapply_all_blanking)
                self.main_window.root.after(0, self.main_window.update_filter)
                
                # Auto-update plot view after blanking
                if self.auto_update_plot:
                    self.main_window.root.after(1000, self.update_claude_with_current_view)
                
                return f"Noise removed from {start_time}-{end_time} seconds"
            
            elif function_name == 'set_peak_detection_params':
                # Set peak detection parameters
                if 'prominence' in params:
                    self.main_window.peak_prominence.set(params['prominence'])
                if 'width_s' in params:
                    self.main_window.peak_width_s.set(params['width_s'])
                if 'distance_s' in params:
                    self.main_window.peak_distance_s.set(params['distance_s'])
                
                return f"Peak detection parameters set: {params}"
            
            elif function_name == 'detect_peaks_valleys':
                mode = params.get('mode', 'Peak')
                self.main_window.root.after(0, lambda: self.main_window.run_detection(mode))
                
                # Auto-update plot view after detection
                if self.auto_update_plot:
                    self.main_window.root.after(2000, self.update_claude_with_current_view)
                
                return f"{mode} detection started"
            
            elif function_name == 'set_plot_visibility':
                signal_type = params.get('signal_type', 'primary_dff')
                visible = params.get('visible', True)
                
                # Set visibility
                var_name = f"{signal_type}_var"
                if hasattr(self.main_window, var_name):
                    getattr(self.main_window, var_name).set(visible)
                    self.main_window.root.after(0, self.main_window.update_plot_visibility)
                    return f"Set {signal_type} visibility to {visible}"
                else:
                    return f"Signal type {signal_type} not found"
            
            elif function_name == 'set_downsample_factor':
                factor = params.get('factor', 50)
                self.main_window.downsample_factor.set(factor)
                return f"Downsample factor set to {factor}"
            
            elif function_name == 'apply_advanced_denoising':
                aggressive = params.get('aggressive', True)
                self.main_window.denoise_aggressive.set(aggressive)
                self.main_window.root.after(0, self.main_window.run_advanced_denoising)
                return f"Advanced denoising applied (aggressive={aggressive})"
            
            elif function_name == 'reset_plot_view':
                self.main_window.root.after(0, self.main_window.reset_view)
                return "Plot view reset"
            
            else:
                return f"Unknown function: {function_name}"
                
        except Exception as e:
            return f"Error calling {function_name}: {str(e)}"
    
    def capture_current_plot(self) -> Optional[str]:
        """Capture the current plot as a base64 image string."""
        try:
            if not hasattr(self.main_window, 'plot_manager') or not self.main_window.plot_manager:
                return None
                
            # Get the matplotlib figure
            fig = self.main_window.plot_manager.fig
            if not fig:
                return None
            
            # Save figure to memory buffer
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            
            # Convert to base64
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            buf.close()
            
            return img_base64
            
        except Exception as e:
            print(f"Error capturing plot: {e}")
            return None
    
    def capture_analysis_plots(self) -> Dict[str, Optional[str]]:
        """Capture all analysis plots (PSTH, correlation, etc.) as base64 image strings."""
        plots = {}
        
        try:
            # Capture PSTH plot
            if (hasattr(self.main_window, 'control_panel') and 
                hasattr(self.main_window.control_panel, 'psth_fig')):
                psth_fig = self.main_window.control_panel.psth_fig
                if psth_fig and len(psth_fig.get_axes()) > 0:
                    buf = io.BytesIO()
                    psth_fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
                    buf.seek(0)
                    plots['psth'] = base64.b64encode(buf.read()).decode('utf-8')
                    buf.close()
            
            # Capture correlation plot
            if (hasattr(self.main_window, 'control_panel') and 
                hasattr(self.main_window.control_panel, 'corr_fig')):
                corr_fig = self.main_window.control_panel.corr_fig
                if corr_fig and len(corr_fig.get_axes()) > 0:
                    buf = io.BytesIO()
                    corr_fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
                    buf.seek(0)
                    plots['correlation'] = base64.b64encode(buf.read()).decode('utf-8')
                    buf.close()
            
        except Exception as e:
            print(f"Error capturing analysis plots: {e}")
        
        return plots
    
    def get_plot_analysis_summary(self) -> Dict[str, Any]:
        """Get a summary of what's currently visible in the plot."""
        try:
            summary = {
                "visible_signals": [],
                "time_range": {"start": 0, "end": 0},
                "amplitude_range": {"min": 0, "max": 0},
                "detected_features": {},
                "applied_filters": {},
                "blanking_regions": []
            }
            
            # Get visible signals
            if hasattr(self.main_window, 'primary_data') and self.main_window.primary_data:
                primary = self.main_window.primary_data
                if hasattr(self.main_window, 'primary_dff_var') and self.main_window.primary_dff_var.get():
                    summary["visible_signals"].append({
                        "type": "primary_dff",
                        "label": "Primary ΔF/F",
                        "data_points": len(primary.get('dff', [])),
                        "time_range": [float(primary.get('time', [0])[0]), float(primary.get('time', [0])[-1])] if 'time' in primary else [0, 0]
                    })
                
                if hasattr(self.main_window, 'primary_raw_var') and self.main_window.primary_raw_var.get():
                    summary["visible_signals"].append({
                        "type": "primary_raw", 
                        "label": "Primary Raw",
                        "data_points": len(primary.get('raw1', [])),
                        "sampling_rate": primary.get('fs', 1000)
                    })
                
                # Get time range from primary data
                if 'time' in primary and len(primary['time']) > 0:
                    summary["time_range"]["start"] = float(primary['time'][0])
                    summary["time_range"]["end"] = float(primary['time'][-1])
                
                # Get amplitude range from dF/F
                if 'dff' in primary and len(primary['dff']) > 0:
                    summary["amplitude_range"]["min"] = float(np.min(primary['dff']))
                    summary["amplitude_range"]["max"] = float(np.max(primary['dff']))
                
                # Get detected features
                if 'peaks' in primary and len(primary['peaks'].get('times', [])) > 0:
                    summary["detected_features"]["peaks"] = {
                        "count": len(primary['peaks']['times']),
                        "times": [float(t) for t in primary['peaks']['times'][:5]],  # First 5 peaks
                        "avg_height": float(np.mean(primary['peaks']['heights'])) if len(primary['peaks']['heights']) > 0 else 0
                    }
                
                if 'valleys' in primary and len(primary['valleys'].get('times', [])) > 0:
                    summary["detected_features"]["valleys"] = {
                        "count": len(primary['valleys']['times']),
                        "times": [float(t) for t in primary['valleys']['times'][:5]],  # First 5 valleys
                        "avg_depth": float(np.mean(primary['valleys']['depths'])) if len(primary['valleys']['depths']) > 0 else 0
                    }
            
            # Get secondary data if available
            if hasattr(self.main_window, 'secondary_data') and self.main_window.secondary_data:
                secondary = self.main_window.secondary_data
                if hasattr(self.main_window, 'secondary_dff_var') and self.main_window.secondary_dff_var.get():
                    summary["visible_signals"].append({
                        "type": "secondary_dff",
                        "label": "Secondary ΔF/F",
                        "data_points": len(secondary.get('dff', [])),
                        "time_range": [float(secondary.get('time', [0])[0]), float(secondary.get('time', [0])[-1])] if 'time' in secondary else [0, 0]
                    })
            
            # Get current filter settings
            if hasattr(self.main_window, 'filter_type'):
                summary["applied_filters"] = {
                    "type": self.main_window.filter_type.get(),
                    "low_cutoff": self.main_window.low_cutoff.get(),
                    "high_cutoff": self.main_window.high_cutoff.get(),
                    "order": self.main_window.filter_order.get()
                }
            
            # Get blanking regions
            if hasattr(self.main_window, 'blanking_regions'):
                summary["blanking_regions"] = [
                    {"start": float(region.get('start', 0)), "end": float(region.get('end', 0))}
                    for region in self.main_window.blanking_regions
                ]
            
            return summary
            
        except Exception as e:
            print(f"Error getting plot analysis summary: {e}")
            return {"error": f"Could not get plot summary: {str(e)}"}
    
    def update_claude_with_current_view(self):
        """Update Claude with the current plot view and analysis state."""
        try:
            # Capture current plot
            plot_image = self.capture_current_plot()
            
            # Get analysis summary
            analysis_summary = self.get_plot_analysis_summary()
            
            # Create context message
            context_msg = "**Plot View Updated**\n\n"
            
            # Add visible signals info
            if analysis_summary.get("visible_signals"):
                context_msg += "**Visible Signals:**\n"
                for signal in analysis_summary["visible_signals"]:
                    context_msg += f"• {signal['label']}: {signal['data_points']} points\n"
                context_msg += "\n"
            
            # Add time range info
            time_range = analysis_summary.get("time_range", {})
            if time_range.get("end", 0) > 0:
                context_msg += f"**Time Range:** {time_range['start']:.1f} - {time_range['end']:.1f} seconds\n"
            
            # Add amplitude range info
            amp_range = analysis_summary.get("amplitude_range", {})
            if amp_range.get("max", 0) != 0:
                context_msg += f"**Amplitude Range:** {amp_range['min']:.2f} to {amp_range['max']:.2f}%\n"
            
            # Add detected features
            features = analysis_summary.get("detected_features", {})
            if features:
                context_msg += "\n**Detected Features:**\n"
                if "peaks" in features:
                    context_msg += f"• Peaks: {features['peaks']['count']} detected\n"
                if "valleys" in features:
                    context_msg += f"• Valleys: {features['valleys']['count']} detected\n"
            
            # Add filter info
            filters = analysis_summary.get("applied_filters", {})
            if filters.get("type"):
                context_msg += f"\n**Applied Filter:** {filters['type']}"
                if filters['type'] in ['Lowpass', 'Highpass']:
                    cutoff = filters['high_cutoff'] if filters['type'] == 'Lowpass' else filters['low_cutoff']
                    context_msg += f" at {cutoff} Hz"
                elif filters['type'] == 'Bandpass':
                    context_msg += f" {filters['low_cutoff']}-{filters['high_cutoff']} Hz"
                context_msg += "\n"
            
            # Add blanking regions
            blanking = analysis_summary.get("blanking_regions", [])
            if blanking:
                context_msg += f"\n**Blanked Regions:** {len(blanking)} regions removed\n"
            
            context_msg += "\nI can now see your current plot and analysis state!"
            
            # Add to chat
            self.add_assistant_message(context_msg)
            
            # Store the analysis summary for Claude to use
            self.current_analysis_summary = analysis_summary
            self.current_plot_image = plot_image
            
        except Exception as e:
            print(f"Error updating Claude with current view: {e}")
            self.add_system_message(f"Error updating plot view: {str(e)}")
    
    def share_data_context(self):
        """Share current data context with Claude."""
        context = self.get_current_data_context()
        
        # Format context for display
        context_msg = "**Current Data Context Shared**\n\n"
        
        if context.get("session_info", {}).get("has_primary_data"):
            primary_info = context["data_summary"]["primary"]
            context_msg += f"**Primary Data:**\n"
            context_msg += f"• Duration: {primary_info['duration_seconds']:.1f}s\n"
            context_msg += f"• Sample Rate: {primary_info['sampling_rate']:.1f} Hz\n"
            context_msg += f"• Samples: {primary_info['num_samples']:,}\n\n"
        
        if context.get("session_info", {}).get("has_secondary_data"):
            secondary_info = context["data_summary"]["secondary"]
            context_msg += f"**Secondary Data:**\n"
            context_msg += f"• Duration: {secondary_info['duration_seconds']:.1f}s\n"
            context_msg += f"• Sample Rate: {secondary_info['sampling_rate']:.1f} Hz\n"
            context_msg += f"• Samples: {secondary_info['num_samples']:,}\n\n"
        
        context_msg += "I now have access to your current data state and can help with analysis!"
        
        self.add_assistant_message(context_msg)
    
    def clear_chat(self):
        """Clear the chat history."""
        self.chat_display.config(state='normal')
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state='disabled')
        self.chat_history = []
        
        # Add welcome message back
        self.add_assistant_message("Chat cleared. Ready for new analysis!")
    
    def start_processing(self):
        """Show processing indicator."""
        self.is_processing = True
        self.send_button.config(state='disabled', text="Processing...")
        self.progress_frame.pack(fill='x', pady=(5, 0))
        self.progress_bar.pack(fill='x')
        self.processing_label.pack()
        self.progress_bar.start()
        
        # Add thinking message with better visual separation
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, "\n", 'message_separator')
        time_str = datetime.datetime.now().strftime("%H:%M:%S")
        self.chat_display.insert(tk.END, f"[{time_str}] ", 'timestamp')
        self.chat_display.insert(tk.END, "Claude ✨", 'assistant_label')
        self.chat_display.insert(tk.END, "\n", 'timestamp')
        self.chat_display.insert(tk.END, "Thinking...", 'thinking')
        self.chat_display.insert(tk.END, "\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state='disabled')
    
    def stop_processing(self):
        """Hide processing indicator."""
        self.is_processing = False
        self.send_button.config(state='normal', text="Send Message")
        self.progress_bar.stop()
        self.progress_frame.pack_forget()
        
        # Remove the "Thinking..." message
        self.chat_display.config(state='normal')
        # Find and remove the last "Thinking..." line
        content = self.chat_display.get(1.0, tk.END)
        lines = content.split('\n')
        if lines and "Thinking..." in lines[-2]:  # -2 because the last line is empty
            # Remove the thinking line
            last_line_start = self.chat_display.index("end-2l linestart")
            self.chat_display.delete(last_line_start, "end-1l")
        self.chat_display.config(state='disabled')
    
    def show_help(self):
        """Show comprehensive help documentation."""
        self._show_help_dialog()
    
    def show_api_settings(self):
        """Show API settings dialog."""
        self._show_api_key_dialog()
    
    def _show_api_key_dialog(self):
        """Show dialog to enter/update API key."""
        dialog = tk.Toplevel(self.main_window.root)
        dialog.title("Claude API Settings")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        
        # Center the dialog
        dialog.transient(self.main_window.root)
        dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Claude API Configuration", 
                               font=('Arial', 12, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # API Key input
        ttk.Label(main_frame, text="Claude API Key:").pack(anchor='w')
        api_key_entry = ttk.Entry(main_frame, width=50, show='*')
        api_key_entry.pack(fill='x', pady=(5, 10))
        
        # Set current key if available
        if self.api_key:
            api_key_entry.insert(0, self.api_key)
        
        # Instructions
        instructions = """
Instructions:
1. Get your Claude API key from https://console.anthropic.com/
2. Enter the key above
3. Click 'Save' to activate the AI assistant

The key will be stored securely for this session.
        """
        ttk.Label(main_frame, text=instructions.strip(), 
                 font=('Arial', 9), foreground='gray').pack(pady=(0, 20))
        
        # Status
        status_label = ttk.Label(main_frame, text="", foreground='green')
        status_label.pack(pady=(0, 10))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x')
        
        def save_key():
            new_key = api_key_entry.get().strip()
            if new_key:
                try:
                    # Test the key
                    test_client = anthropic.Anthropic(api_key=new_key)
                    
                    # Save the key
                    self.api_key = new_key
                    self.claude_client = test_client
                    self.current_model = None  # Reset cached model for new API key
                    
                    # Update status
                    self.status_label.config(text="●", foreground='green')
                    status_label.config(text="API key saved successfully!")
                    
                    # Close dialog after short delay
                    dialog.after(1500, dialog.destroy)
                    
                except Exception as e:
                    status_label.config(text=f"Error: {str(e)}", foreground='red')
            else:
                status_label.config(text="Please enter a valid API key", foreground='red')
        
        ttk.Button(button_frame, text="Save", command=save_key).pack(side='left')
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side='right')
        
        # Focus on entry
        api_key_entry.focus()
    
    def _on_enter_key(self, event):
        """Handle Enter key press in message input."""
        if event.state & 0x4:  # Ctrl+Enter
            self.send_message()
            return 'break'
        else:
            # Regular Enter - send message
            self.send_message()
            return 'break'
    
    def _on_key_press(self, event):
        """Handle key press events for better interaction."""
        # Enable Tab key for indentation
        if event.keysym == 'Tab':
            return None  # Allow normal tab behavior
        
        # Re-enable focus on the input field
        if not self.message_entry.focus_get():
            self.message_entry.focus_set()
        
        return None
    
    def _toggle_auto_update(self):
        """Toggle auto-update feature."""
        self.auto_update_plot = self.auto_update_var.get()
        status = "enabled" if self.auto_update_plot else "disabled"
        self.add_system_message(f"Auto-update plot view {status}")
    
    def _start_streaming_message(self, message: str, sender: str):
        """Start streaming a message character by character."""
        if self.is_streaming:
            self._stop_streaming()
        
        self.is_streaming = True
        self.stream_buffer = message
        self.stream_position = 0
        
        # Add timestamp and sender first
        self.chat_display.config(state='normal')
        
        # Add visual separator before each message for better separation
        if sender != 'system':
            self.chat_display.insert(tk.END, "\n", 'message_separator')
        
        # Add timestamp
        time_str = datetime.datetime.now().strftime("%H:%M:%S")
        self.chat_display.insert(tk.END, f"[{time_str}] ", 'timestamp')
        
        # Add sender with enhanced styling
        if sender == 'assistant':
            self.chat_display.insert(tk.END, "Claude ✨", 'assistant_label')
        elif sender == 'user':
            self.chat_display.insert(tk.END, "You 💬", 'user_label')
        elif sender == 'system':
            self.chat_display.insert(tk.END, "System ⚙️", 'system_label')
        
        self.chat_display.insert(tk.END, "\n", 'timestamp')
        
        # Store the position where the message will start
        self.current_message_start_index = self.chat_display.index(tk.END)
        
        # Start typing indicator
        self._show_typing_indicator()
        
        # Begin streaming animation
        self._stream_next_chunk()
    
    def _show_typing_indicator(self):
        """Show typing indicator while AI is 'thinking'."""
        if not self.is_streaming:
            return
        
        self.typing_indicator_active = True
        self.chat_display.insert(tk.END, "●", 'thinking')
        self.chat_display.see(tk.END)
        self.chat_display.config(state='disabled')
        
        # Schedule removal of typing indicator and start of actual streaming
        self.main_window.root.after(800, self._start_actual_streaming)
    
    def _start_actual_streaming(self):
        """Start the actual streaming of text after typing indicator."""
        if not self.is_streaming:
            return
        
        # Remove typing indicator
        self.chat_display.config(state='normal')
        if self.typing_indicator_active:
            # Remove the typing indicator
            self.chat_display.delete(f"{self.current_message_start_index}", tk.END)
            self.typing_indicator_active = False
        
        # Begin streaming the actual message
        self._stream_next_chunk()
    
    def _stream_next_chunk(self):
        """Stream the next chunk of text."""
        if not self.is_streaming or self.stream_position >= len(self.stream_buffer):
            self._finish_streaming()
            return
        
        # Calculate chunk size based on stream speed
        chunk_size = max(1, self.stream_speed // 10)  # About 10 updates per second
        
        # Get the next chunk of text
        chunk = self.stream_buffer[self.stream_position:self.stream_position + chunk_size]
        
        # Add chunk to display
        self.chat_display.config(state='normal')
        
        # Format and insert the chunk
        if self.stream_position == 0:
            # First chunk - apply formatting
            formatted_chunk = self._format_message_text(chunk)
            self._insert_formatted_text(formatted_chunk, 'assistant_message')
        else:
            # Subsequent chunks - insert as plain text
            self.chat_display.insert(tk.END, chunk, 'assistant_message')
        
        # Scroll to show new text
        self.chat_display.see(tk.END)
        self.chat_display.config(state='disabled')
        
        # Update position
        self.stream_position += chunk_size
        
        # Schedule next chunk
        delay = int(1000 / (self.stream_speed / chunk_size))  # Delay in milliseconds
        self.stream_timer = self.main_window.root.after(delay, self._stream_next_chunk)
    
    def _finish_streaming(self):
        """Finish streaming and clean up."""
        if not self.is_streaming:
            return
        
        # Add any remaining text
        if self.stream_position < len(self.stream_buffer):
            remaining = self.stream_buffer[self.stream_position:]
            self.chat_display.config(state='normal')
            self.chat_display.insert(tk.END, remaining, 'assistant_message')
            self.chat_display.config(state='disabled')
        
        # Add final newlines with visual separator
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, "\n")
        # Add subtle divider line for better message separation
        self.chat_display.insert(tk.END, "─" * 50 + "\n", 'message_separator')
        self.chat_display.see(tk.END)
        self.chat_display.config(state='disabled')
        
        # Update chat history
        self.chat_history.append({
            'timestamp': datetime.datetime.now().isoformat(),
            'sender': 'assistant',
            'message': self.stream_buffer
        })
        
        # Clean up
        self._stop_streaming()
    
    def _stop_streaming(self):
        """Stop streaming and clean up."""
        self.is_streaming = False
        self.typing_indicator_active = False
        self.stream_buffer = ""
        self.stream_position = 0
        self.current_message_start_index = None
        
        if self.stream_timer:
            self.main_window.root.after_cancel(self.stream_timer)
            self.stream_timer = None
    
    def _format_message_text(self, text: str) -> str:
        """Format message text with enhanced styling."""
        # Pre-process the text to handle special patterns
        
        # Convert markdown-style lists to bullet points
        text = text.replace('• ', '• ')  # Ensure bullet consistency
        
        # Handle special sections (case-insensitive)
        import re
        
        # Mark summary sections
        text = re.sub(r'(?i)^\s*\*\*\s*summary\s*\*\*\s*$', '**[SUMMARY]**', text, flags=re.MULTILINE)
        text = re.sub(r'(?i)^\s*\*\*\s*key\s*points?\s*\*\*\s*$', '**[KEY POINTS]**', text, flags=re.MULTILINE)
        text = re.sub(r'(?i)^\s*\*\*\s*analysis\s*\*\*\s*$', '**[ANALYSIS]**', text, flags=re.MULTILINE)
        text = re.sub(r'(?i)^\s*\*\*\s*conclusion\s*\*\*\s*$', '**[CONCLUSION]**', text, flags=re.MULTILINE)
        
        # Handle code blocks
        text = re.sub(r'```([^`]+)```', r'[CODE_BLOCK]\1[/CODE_BLOCK]', text)
        
        # Handle quotes
        text = re.sub(r'^>\s*(.+)$', r'[QUOTE]\1[/QUOTE]', text, flags=re.MULTILINE)
        
        return text
    
    def _insert_formatted_text(self, text: str, default_tag: str):
        """Insert formatted text with rich styling."""
        import re
        
        # Enhanced formatting patterns with special sections
        patterns = [
            (r'\*\*\[SUMMARY\]\*\*', 'keypoint'),      # **[SUMMARY]**
            (r'\*\*\[KEY POINTS\]\*\*', 'keypoint'),   # **[KEY POINTS]**
            (r'\*\*\[ANALYSIS\]\*\*', 'keypoint'),     # **[ANALYSIS]**
            (r'\*\*\[CONCLUSION\]\*\*', 'keypoint'),   # **[CONCLUSION]**
            (r'\[CODE_BLOCK\]([^\[]+)\[/CODE_BLOCK\]', 'code_block'),  # [CODE_BLOCK]...[/CODE_BLOCK]
            (r'\[QUOTE\]([^\[]+)\[/QUOTE\]', 'quote'),                 # [QUOTE]...[/QUOTE]
            (r'\*\*([^\*]+)\*\*', 'strong'),          # **bold**
            (r'\*([^\*]+)\*', 'emphasis'),             # *italic*
            (r'`([^`]+)`', 'code'),                   # `code`
            (r'^#{1,2}\s+(.+)$', 'heading'),          # # headings
            (r'^###\s+(.+)$', 'subheading'),          # ### subheadings
            (r'^•\s+(.+)$', 'bullet'),                # • bullets
            (r'^\d+\.\s+(.+)$', 'numbered'),         # 1. numbered lists
            (r'^-{3,}$', 'separator'),                # --- separators
            (r'\*\*\*(.+?)\*\*\*', 'highlight'),      # ***highlight***
        ]
        
        lines = text.split('\n')
        
        for line_idx, line in enumerate(lines):
            line_processed = False
            
            # Check for special section contexts
            in_summary_section = False
            if line_idx > 0:
                prev_lines = lines[max(0, line_idx-3):line_idx]
                for prev_line in prev_lines:
                    if any(marker in prev_line for marker in ['[SUMMARY]', '[KEY POINTS]', '[ANALYSIS]', '[CONCLUSION]']):
                        in_summary_section = True
                        break
            
            # Check line-level patterns first
            for pattern, tag in patterns:
                if tag in ['heading', 'subheading', 'bullet', 'numbered', 'separator', 'keypoint', 'code_block', 'quote']:
                    match = re.match(pattern, line)
                    if match:
                        if tag == 'separator':
                            self.chat_display.insert(tk.END, line, tag)
                        elif tag in ['code_block', 'quote']:
                            content = match.group(1) if match.groups() else line
                            self.chat_display.insert(tk.END, content, tag)
                        elif tag == 'keypoint':
                            # Special handling for key sections
                            content = match.group(0)
                            self.chat_display.insert(tk.END, content, tag)
                        else:
                            content = match.group(1) if match.groups() else line
                            
                            # Apply summary formatting if in summary section
                            if in_summary_section and tag in ['bullet', 'numbered']:
                                self.chat_display.insert(tk.END, content, 'summary')
                            else:
                                self.chat_display.insert(tk.END, content, tag)
                        line_processed = True
                        break
            
            if not line_processed:
                # Process inline patterns
                current_pos = 0
                while current_pos < len(line):
                    found_match = False
                    
                    # Look for the earliest inline pattern
                    earliest_match = None
                    earliest_pos = len(line)
                    
                    for pattern, tag in patterns:
                        if tag not in ['heading', 'subheading', 'bullet', 'numbered', 'separator', 'keypoint', 'code_block', 'quote']:
                            match = re.search(pattern, line[current_pos:])
                            if match and match.start() < earliest_pos:
                                earliest_match = (match, tag, current_pos + match.start())
                                earliest_pos = match.start()
                    
                    if earliest_match:
                        match, tag, abs_pos = earliest_match
                        
                        # Add text before the match
                        if abs_pos > current_pos:
                            text_before = line[current_pos:abs_pos]
                            tag_to_use = 'summary' if in_summary_section else default_tag
                            self.chat_display.insert(tk.END, text_before, tag_to_use)
                        
                        # Add the matched text with formatting
                        content = match.group(1) if match.groups() else match.group(0)
                        self.chat_display.insert(tk.END, content, tag)
                        
                        # Move past the match
                        current_pos = abs_pos + len(match.group(0))
                        found_match = True
                    else:
                        # No more matches, add rest of line
                        remaining_text = line[current_pos:]
                        tag_to_use = 'summary' if in_summary_section else default_tag
                        self.chat_display.insert(tk.END, remaining_text, tag_to_use)
                        break
            
            # Add newline if not the last line
            if line_idx < len(lines) - 1:
                self.chat_display.insert(tk.END, "\n", default_tag)
    
    def _enhance_response_formatting(self, response_text: str) -> str:
        """Enhance Claude's response with better formatting markers."""
        import re
        
        # Add visual enhancements to Claude's typical response patterns
        
        # Enhance section headers that Claude commonly uses
        response_text = re.sub(r'(?i)^## (.+)$', r'# \1', response_text, flags=re.MULTILINE)
        response_text = re.sub(r'(?i)^### (.+)$', r'## \1', response_text, flags=re.MULTILINE)
        
        # Enhance analysis sections
        response_text = re.sub(r'(?i)^\*\*Analysis\*\*:', '**[ANALYSIS]**', response_text, flags=re.MULTILINE)
        response_text = re.sub(r'(?i)^\*\*Summary\*\*:', '**[SUMMARY]**', response_text, flags=re.MULTILINE)
        response_text = re.sub(r'(?i)^\*\*Key Points\*\*:', '**[KEY POINTS]**', response_text, flags=re.MULTILINE)
        response_text = re.sub(r'(?i)^\*\*Key Findings\*\*:', '**[KEY POINTS]**', response_text, flags=re.MULTILINE)
        response_text = re.sub(r'(?i)^\*\*Conclusion\*\*:', '**[CONCLUSION]**', response_text, flags=re.MULTILINE)
        response_text = re.sub(r'(?i)^\*\*Results\*\*:', '**[ANALYSIS]**', response_text, flags=re.MULTILINE)
        response_text = re.sub(r'(?i)^\*\*Interpretation\*\*:', '**[ANALYSIS]**', response_text, flags=re.MULTILINE)
        
        # Enhance recommendations and next steps
        response_text = re.sub(r'(?i)^\*\*Recommendations\*\*:', '**[KEY POINTS]**', response_text, flags=re.MULTILINE)
        response_text = re.sub(r'(?i)^\*\*Next Steps\*\*:', '**[KEY POINTS]**', response_text, flags=re.MULTILINE)
        
        # Enhance important notes
        response_text = re.sub(r'(?i)^\*\*Important\*\*:', '***Important***:', response_text, flags=re.MULTILINE)
        response_text = re.sub(r'(?i)^\*\*Note\*\*:', '***Note***:', response_text, flags=re.MULTILINE)
        response_text = re.sub(r'(?i)^\*\*Warning\*\*:', '***Warning***:', response_text, flags=re.MULTILINE)
        
        # Convert numbered lists to a more consistent format
        response_text = re.sub(r'^(\d+)\. ', r'\1. ', response_text, flags=re.MULTILINE)
        
        # Enhance code suggestions
        response_text = re.sub(r'(?i)^\*\*Code\*\*:', '**[CODE]**', response_text, flags=re.MULTILINE)
        response_text = re.sub(r'(?i)^\*\*Example\*\*:', '**[CODE]**', response_text, flags=re.MULTILINE)
        
        return response_text
    
    def _create_scrollable_text(self, parent, content: str) -> tk.Text:
        """Create a scrollable text widget with content."""
        frame = ttk.Frame(parent)
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create text widget with scrollbar
        text_widget = tk.Text(frame, wrap=tk.WORD, font=('Arial', 10), 
                             state='normal', background='#f8f9fa')
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        scrollbar.pack(side='right', fill='y')
        text_widget.pack(side='left', fill='both', expand=True)
        
        # Insert content
        text_widget.insert(1.0, content)
        text_widget.config(state='disabled')
        
        return text_widget
    
    def _create_overview_tab(self, notebook):
        """Create overview help tab."""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="概述 Overview")
        
        from .ai_help_tabs import create_overview_tab_content
        content = create_overview_tab_content()
        self._create_scrollable_text(tab, content)
    
    def _create_features_tab(self, notebook):
        """Create features help tab."""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="功能详解 Features")
        
        from .ai_help_tabs import create_features_tab_content
        content = create_features_tab_content()
        self._create_scrollable_text(tab, content)
    
    def _create_commands_tab(self, notebook):
        """Create commands help tab."""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="命令参考 Commands")
        
        from .ai_help_tabs import create_commands_tab_content
        content = create_commands_tab_content()
        self._create_scrollable_text(tab, content)
    
    def _create_technical_tab(self, notebook):
        """Create technical specifications tab."""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="技术规格 Technical")
        
        from .ai_help_tabs import create_technical_tab_content
        content = create_technical_tab_content()
        self._create_scrollable_text(tab, content)
    
    def _create_troubleshooting_tab(self, notebook):
        """Create troubleshooting help tab."""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="故障排除 Troubleshooting")
        
        from .ai_help_tabs import create_troubleshooting_tab_content
        content = create_troubleshooting_tab_content()
        self._create_scrollable_text(tab, content)
    
    def _create_faq_tab(self, notebook):
        """Create FAQ help tab."""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="常见问题 FAQ")
        
        from .ai_help_tabs import create_faq_tab_content
        content = create_faq_tab_content()
        self._create_scrollable_text(tab, content)
    
    def _show_usage_examples(self):
        """Show usage examples in chat."""
        examples_msg = """**[KEY POINTS]** 使用示例 (Usage Examples)

### 🔬 数据分析示例 (Data Analysis Examples)

1. **信号质量评估**
   "请分析当前信号的质量，包括信噪比和基线稳定性"

2. **峰检测优化** 
   "当前峰检测参数是否合适？建议如何优化以获得更准确的结果"

3. **相关性分析**
   "分析两个通道间的相关性，特别关注延迟和强度"

4. **PSTH解释**
   "解释这个PSTH结果的生物学意义，响应模式说明了什么？"

### ⚙️ GUI控制示例 (GUI Control Examples)

1. **滤波操作**
   "应用2Hz低通滤波器去除高频噪声"
   
2. **噪声移除**
   "移除15-25秒时间段的运动伪影"

3. **显示控制**
   "隐藏原始信号，只显示ΔF/F和TTL"

4. **参数调整**
   "设置峰检测显著性为3，最小间距为1秒"

### 📊 统计分析示例 (Statistical Analysis Examples)

1. **假设检验**
   "比较刺激前后的信号变化是否具有统计学意义"

2. **效应量评估**
   "计算响应的效应量，评估生物学重要性"

3. **多重比较**
   "分析多个时间窗口的差异，需要多重比较校正吗？"

### 🎯 实验设计建议 (Experimental Design Suggestions)

1. **采样参数**
   "基于当前数据特征，建议未来实验的最优采样率"

2. **对照设计**
   "设计适当的对照实验来验证这些发现"

3. **样本量计算**
   "基于当前效应量，计算所需的样本量"

---

💡 **提示**: 尝试这些示例开始您的AI辅助分析之旅！"""
        
        self._start_streaming_message(examples_msg, 'assistant')
    
    def show_quick_help(self):
        """Show quick help message in chat."""
        quick_help = """**[KEY POINTS]** 快速帮助 (Quick Help)

### 🚀 快速开始 (Quick Start)
1. **配置API**: 点击 "API Settings" 设置Claude密钥
2. **共享数据**: 点击 "Share Data Context" 让AI了解您的数据
3. **开始对话**: 直接询问分析问题或请求操作

### 💬 对话技巧 (Chat Tips)
• **具体询问**: "分析前30秒的峰特征" 比 "分析信号" 更好
• **使用术语**: 使用 "ΔF/F", "PSTH", "相关性" 等专业术语
• **分步进行**: 复杂分析可以分解为多个步骤
• **图表同步**: 开启Auto-update保持AI与当前视图同步

### ⚙️ 快捷操作 (Quick Actions)
• **Ctrl+Enter**: 发送消息
• **Auto-update ☑**: 自动同步图表状态
• **Help按钮**: 查看完整技术文档
• **Clear Chat**: 清空对话记录

### 🎯 常用命令 (Common Commands)
• "应用2Hz低通滤波" → 自动设置滤波器
• "移除10-20秒噪声" → 自动添加空白区域
• "检测所有峰值" → 运行峰检测
• "解释PSTH结果" → 获得专业解读

需要更多帮助？点击 **Help** 按钮查看完整文档！"""
        
        self._start_streaming_message(quick_help, 'assistant')