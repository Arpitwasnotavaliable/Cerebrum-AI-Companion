# app/app.py
import customtkinter as ctk
# ...
import sys # <-- ADD THIS
import os  # (already there)
# ...# app/app.py
import customtkinter as ctk
from tkinter import messagebox
import threading
import os
import re

# Import all our custom modules
from app.ui_frames import ChatFrame, HabitFrame, HelpFrame, SettingsFrame
from app.model_manager import ModelManager
import app.database as db

# --- Configuration ---
# This finds the *actual* name of the GGUF file in your model folder
# This makes it easy to swap models just by changing the file.
APP_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(APP_DIR, "..", "model")
MODEL_NAME = ""
MODEL_PATH = ""

try:
    # Find the first .gguf file in the model directory
    gguf_files = [f for f in os.listdir(MODEL_DIR) if f.endswith(".gguf")]
    if not gguf_files:
        raise FileNotFoundError("No .gguf file found in the 'model' directory.")
    
    MODEL_NAME = gguf_files[0]
    MODEL_PATH = os.path.join(MODEL_DIR, MODEL_NAME)
    print(f"Found model: {MODEL_PATH}")

except Exception as e:
    print(f"Fatal Error: {e}")
    messagebox.showerror("Fatal Error", str(e))
    # We will exit if the model isn't found
    exit()
# ---------------------


class CerebrumApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Cerebrum - Your Private AI Companion")
        self.geometry("800x600")
        
        # Set theme
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # --- Initialize Core Components ---
        # 1. The Model Manager (from model_manager.py)
        self.model_manager = ModelManager(model_path=MODEL_PATH)
        # 2. In-memory chat history (a simple list)
        self.chat_history = [] 

        # --- Configure Main Window Grid ---
        # 1x2 grid: Sidebar (col 0) | Main Content (col 1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- Create Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsw")
        self.sidebar_frame.grid_rowconfigure(5, weight=1) # Pushes status label to bottom

        self.sidebar_label = ctk.CTkLabel(self.sidebar_frame, text="Cerebrum", font=ctk.CTkFont(size=20, weight="bold"))
        self.sidebar_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # --- Sidebar Navigation Buttons ---
        self.chat_button = ctk.CTkButton(self.sidebar_frame, text="Chat", command=lambda: self.show_frame("chat"))
        self.chat_button.grid(row=1, column=0, padx=20, pady=10)

        self.habits_button = ctk.CTkButton(self.sidebar_frame, text="Habits", command=lambda: self.show_frame("habits"))
        self.habits_button.grid(row=2, column=0, padx=20, pady=10)

        self.help_button = ctk.CTkButton(self.sidebar_frame, text="Help", command=lambda: self.show_frame("help"))
        self.help_button.grid(row=3, column=0, padx=20, pady=10)
        
        self.settings_button = ctk.CTkButton(self.sidebar_frame, text="Settings", command=lambda: self.show_frame("settings"))
        self.settings_button.grid(row=4, column=0, padx=20, pady=10)

        self.model_status_label = ctk.CTkLabel(self.sidebar_frame, text="Model: Loading...", text_color="grey")
        self.model_status_label.grid(row=5, column=0, padx=20, pady=20, sticky="s")

        # --- Create Main Content Area ---
        # This frame will hold all our "pages" (frames)
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # --- Initialize All Frames (from ui_frames.py) ---
        self.frames = {}
        
        # 1. Chat Frame
        # We pass a "callback" function to the chat frame.
        # When the user clicks "Send", the frame will call self.start_chat_thread
        self.chat_frame = ChatFrame(self.main_frame, on_send_message_callback=self.start_chat_thread)
        self.frames["chat"] = self.chat_frame
        
        # 2. Habit Frame
        self.habit_frame = HabitFrame(self.main_frame)
        self.frames["habits"] = self.habit_frame
        
        # 3. Help Frame
        self.help_frame = HelpFrame(self.main_frame)
        self.frames["help"] = self.help_frame
        
        # 4. Settings Frame
        # We pass the model path (to display it) and the "clear data" callback
        self.settings_frame = SettingsFrame(self.main_frame, MODEL_PATH, self.on_clear_all_data)
        self.frames["settings"] = self.settings_frame
        
        # Place all frames in the grid, one on top of the other
        for frame in self.frames.values():
            frame.grid(row=0, column=0, sticky="nsew")

        # --- Start Up Sequence ---
        self.load_chat_history_from_db()
        self.start_model_load_thread()
        self.show_frame("chat") # Show chat frame by default

    def show_frame(self, frame_name):
        """Raises the requested frame to the top."""
        if frame_name == "habits":
            # Refresh habits every time the frame is shown
            self.habit_frame.load_habits()
            
        frame = self.frames[frame_name]
        frame.tkraise() # This is the tkinter function to bring a frame to the front

    def load_chat_history_from_db(self):
        """Loads old messages from DB into the UI and memory."""
        messages = db.get_messages()
        self.chat_frame.load_history(messages)
        self.chat_history = list(messages) # Load into our in-memory list

    # --- ⬇️ CRITICAL CONCURRENCY (THREADING) LOGIC ⬇️ ---
    # This is the most important part of the app.
    # It prevents the UI from freezing when the AI is thinking.
    
    

    def start_model_load_thread(self):
        """
        Loads the 5GB model in a *separate thread* so the UI
        doesn't freeze on startup.
        """
        self.chat_frame.set_input_state("disabled") # Disable chat
        # Create a new thread, tell it to run _model_load_task
        load_thread = threading.Thread(target=self._model_load_task, daemon=True)
        load_thread.start()

    def _model_load_task(self):
        """The actual work of loading the model (runs in the new thread)."""
        print("Model loading thread started...")
        self.model_manager.load_model()
        # When done, schedule the UI update (on_model_loaded) to run
        # back on the main UI thread.
        self.after(0, self.on_model_loaded)

    def on_model_loaded(self):
        """UI updates to perform after the model is loaded."""
        print("Model loading complete. Updating UI.")
        if self.model_manager.is_model_loaded():
            self.model_status_label.configure(text="Model: Ready", text_color="green")
            self.chat_frame.set_input_state("normal") # Enable chat
        else:
            self.model_status_label.configure(text="Model: Load Failed", text_color="red")
            messagebox.showerror("Model Error", "The AI model failed to load. The chat will not function.")

    def start_chat_thread(self, user_message):
        """
        Starts a new thread to get the AI's response.
        This keeps the UI responsive *while the AI is thinking*.
        """
        if not self.model_manager.is_model_loaded():
            messagebox.showwarning("Model Not Ready", "The AI model is still loading. Please wait.")
            return
            
        # 1. Add user message to in-memory history and save to DB
        self.chat_history.append({"role": "user", "content": user_message})
        db.save_message("user", user_message)
        
        # 2. Disable the chat input
        self.chat_frame.set_input_state("disabled")
        self.chat_frame.start_new_ai_message() # Create the empty "typing" bubble
        
        # 3. Start the inference thread
        inference_thread = threading.Thread(
            target=self._inference_task,
            args=(list(self.chat_history),), # Pass a *copy* of the history
            daemon=True
        )
        inference_thread.start()

    def _inference_task(self, history_snapshot):
        """The actual work of running inference (runs in the new thread)."""
        
        # This is the "callback" function we pass to the model manager.
        # It will be called *from this thread* for each new token.
        def on_token_callback(token):
            # 'self.after(0, ...)' is a thread-safe way to send a command
            # from our work thread back to the main UI thread.
            # It says: "Hey UI thread, at your next opportunity,
            # please run the 'append_token' function with this token."
            self.after(0, self.chat_frame.append_token_to_current_message, token)

        # This is a blocking call. It will run for 10-30 seconds.
        # It streams tokens by calling 'on_token_callback' repeatedly.
        full_response = self.model_manager.generate_response(
            chat_history=history_snapshot,
            on_token_callback=on_token_callback
        )
        
        # After streaming is complete, do post-processing
        if full_response:
            # 4. Save the *full* response to DB and memory
            db.save_message("assistant", full_response)
            self.chat_history.append({"role": "assistant", "content": full_response})
            
            # 5. Parse for habits (in this thread, it's fast)
            self.parse_and_save_habits(full_response)

        # 6. Schedule the UI re-enable to run on the main thread
        self.after(0, self.chat_frame.set_input_state, "normal")

    # --- ⬆️ END OF CRITICAL CONCURRENCY LOGIC ⬆️ ---

    
    # --- Data & Privacy Logic ---
    
    def parse_and_save_habits(self, ai_response_text):
        """Finds [HABIT: ...] tags in text and adds them to the database."""
        # Use regex to find all habits
        habits_found = re.findall(r"\[HABIT: (.*?)\]", ai_response_text)
        
        if habits_found:
            print(f"Found habits in response: {habits_found}")
            for habit_title in habits_found:
                db.add_habit(habit_title.strip(), "ai")
            
            # Show a subtle popup (scheduled on the main thread)
            self.after(0, lambda: messagebox.showinfo("Habit Added", f"A new habit was added to your tracker: '{habits_found[0]}'"))


    def on_clear_all_data(self):
        """Callback for the 'Clear All Data' button in SettingsFrame."""
        # This function is called by the SettingsFrame.
        db.clear_all_data()
        
        # Clear in-memory history
        self.chat_history.clear()
        
        # Reload/clear all UI frames
        self.load_chat_history_from_db() # Clears chat frame
        self.habit_frame.load_habits()   # Clears habit frame
        self.habit_frame.clear_selection()
        
        messagebox.showinfo("Data Cleared", "All chat history and habits have been deleted.")

# --- Main execution ---
# This line checks if the script is being run directly (not imported)
if __name__ == "__main__":
    app = CerebrumApp() # Create an instance of our app
    app.mainloop()      # Start the app's main event loop