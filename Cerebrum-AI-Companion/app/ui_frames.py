# app/ui_frames.py
import customtkinter as ctk
from tkinter import messagebox
import datetime
import os
import re

# Import our database functions
import app.database as db

# --- 1. The Chat Frame ---
# This is the main screen for chatting with the AI.
class ChatFrame(ctk.CTkFrame):
    def __init__(self, master, on_send_message_callback):
        super().__init__(master)
        self.on_send_message = on_send_message_callback
        
        # Configure the grid to make the chat history expandable
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Frame for scrollable chat history
        self.history_frame = ctk.CTkScrollableFrame(self)
        self.history_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)

        # Frame for the user input
        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.chat_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Type your message...")
        self.chat_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        # Bind the <Return> (Enter) key to the send message function
        self.chat_entry.bind("<Return>", self.on_send_pressed)

        self.send_button = ctk.CTkButton(self.input_frame, text="Send", width=70, command=self.on_send_pressed)
        self.send_button.grid(row=0, column=1, sticky="e")
        
        # This will hold a reference to the AI's "typing" label
        self.current_ai_message_label = None

    def on_send_pressed(self, event=None):
        """Called when the user hits 'Send' or presses Enter."""
        message = self.chat_entry.get()
        if message.strip():
            self.add_message_to_history("user", message)
            self.chat_entry.delete(0, 'end')
            # Call the main app's function to handle the AI inference
            self.on_send_message(message)

    def add_message_to_history(self, role, content):
        """Adds a complete message bubble to the chat history."""
        # 'user' messages are on the right, 'assistant' on the left
        anchor = "e" if role == "user" else "w"
        color = "blue" if role == "user" else "gray20"
        
        # We put the label inside a frame to give it padding and a background
        frame = ctk.CTkFrame(self.history_frame, fg_color=color)
        frame.pack(fill="x", padx=10, pady=5, anchor=anchor)
        
        label = ctk.CTkLabel(frame, text=content, wraplength=500, justify="left")
        label.pack(padx=10, pady=10)
        
        # Auto-scroll to the bottom
        self.history_frame._parent_canvas.yview_moveto(1.0)
        
    def start_new_ai_message(self):
        """Creates a new, empty message bubble for the AI to stream into."""
        frame = ctk.CTkFrame(self.history_frame, fg_color="gray20")
        frame.pack(fill="x", padx=10, pady=5, anchor="w")
        
        # Create the label with no text, and store a reference to it
        self.current_ai_message_label = ctk.CTkLabel(frame, text="", wraplength=500, justify="left")
        self.current_ai_message_label.pack(padx=10, pady=10)

    def append_token_to_current_message(self, token):
        """Appends a new token to the AI's streaming message."""
        if self.current_ai_message_label:
            current_text = self.current_ai_message_label.cget("text")
            self.current_ai_message_label.configure(text=current_text + token)
            # Keep scrolling to the bottom as text is added
            self.history_frame._parent_canvas.yview_moveto(1.0)

    def set_input_state(self, state):
        """Disables or enables the chat entry and send button."""
        self.chat_entry.configure(state=state)
        self.send_button.configure(state=state)

    def load_history(self, messages):
        """Clears the current chat and loads all messages from the DB."""
        # Clear all existing message widgets
        for widget in self.history_frame.winfo_children():
            widget.destroy()
        
        for message in messages:
            self.add_message_to_history(message['role'], message['content'])

# --- 2. The Habit Tracker Frame ---
class HabitFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.today = str(datetime.date.today())
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Left Side: Habit List ---
        self.list_frame = ctk.CTkFrame(self)
        self.list_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=10, pady=10)
        self.list_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(self.list_frame, text="Today's Habits", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=10, pady=10)
        
        self.habit_list_scrollframe = ctk.CTkScrollableFrame(self.list_frame, fg_color="transparent")
        self.habit_list_scrollframe.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # --- Right Side: Add/Edit ---
        self.entry_frame = ctk.CTkFrame(self)
        self.entry_frame.grid(row=0, column=1, sticky="new", padx=10, pady=10)
        self.entry_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self.entry_frame, text="Manage Habits", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=2, padx=10, pady=10)
        
        self.habit_entry = ctk.CTkEntry(self.entry_frame, placeholder_text="Enter new habit title...")
        self.habit_entry.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        
        self.add_button = ctk.CTkButton(self.entry_frame, text="Add Habit", command=self.add_new_habit)
        self.add_button.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        
        self.update_button = ctk.CTkButton(self.entry_frame, text="Update Selected", command=self.update_selected_habit, state="disabled")
        self.update_button.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
        
        self.delete_button = ctk.CTkButton(self.entry_frame, text="Delete Selected", command=self.delete_selected_habit, fg_color="red", hover_color="darkred", state="disabled")
        self.delete_button.grid(row=3, column=1, sticky="ew", padx=10, pady=5)
        
        self.clear_button = ctk.CTkButton(self.entry_frame, text="Clear Selection", command=self.clear_selection)
        self.clear_button.grid(row=4, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        
        self.selected_habit_id = None
        
        # --- Right Side: History (for selected habit) ---
        self.history_frame = ctk.CTkFrame(self)
        self.history_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        self.history_label = ctk.CTkLabel(self.history_frame, text="Habit History", font=ctk.CTkFont(size=16, weight="bold"))
        self.history_label.pack(padx=10, pady=10)
        
        self.history_textbox = ctk.CTkTextbox(self.history_frame, state="disabled")
        self.history_textbox.pack(fill="both", expand=True, padx=10, pady=10)

        self.load_habits() # Load habits when the frame is first created

    def load_habits(self):
        """Clears and re-loads all habits from the DB into the list."""
        # Clear existing checkboxes
        for widget in self.habit_list_scrollframe.winfo_children():
            widget.destroy()
        
        habits = db.get_habits_with_today_status(self.today)
        
        for habit in habits:
            habit_id = habit['id']
            title = habit['title']
            completed = habit['completed_today']
            
            # Create a frame for each habit (checkbox + edit button)
            frame = ctk.CTkFrame(self.habit_list_scrollframe, fg_color="transparent")
            frame.pack(fill="x", pady=2)
            
            # Checkbox state
            var = ctk.StringVar(value="on" if completed else "off")
            checkbox = ctk.CTkCheckBox(
                frame,
                text=title,
                variable=var,
                onvalue="on",
                offvalue="off",
                command=lambda hid=habit_id, v=var: self.on_checkbox_toggle(hid, v)
            )
            checkbox.pack(side="left", padx=5)
            
            # Button to select for editing
            select_button = ctk.CTkButton(
                frame,
                text="Edit",
                width=50,
                command=lambda hid=habit_id, t=title: self.select_habit_for_edit(hid, t)
            )
            select_button.pack(side="right", padx=5)

    def on_checkbox_toggle(self, habit_id, var):
        """Called when a habit's checkbox is clicked."""
        if var.get() == "on":
            db.log_habit(habit_id, self.today)
        else:
            db.unlog_habit(habit_id, self.today)
        
        # Update history view if this habit is selected
        if self.selected_habit_id == habit_id:
            self.show_habit_history(habit_id)

    def select_habit_for_edit(self, habit_id, title):
        """Populates the entry fields when an 'Edit' button is pressed."""
        self.habit_entry.delete(0, 'end')
        self.habit_entry.insert(0, title)
        
        self.selected_habit_id = habit_id
        
        # Enable the Update and Delete buttons
        self.update_button.configure(state="normal")
        self.delete_button.configure(state="normal")
        
        # Show this habit's history
        self.show_habit_history(habit_id)

    def show_habit_history(self, habit_id):
        """Fetches and displays the completion log for a habit."""
        entries = db.get_habit_entries(habit_id)
        self.history_label.configure(text=f"History for: '{self.habit_entry.get()}'")
        
        self.history_textbox.configure(state="normal") # Enable writing
        self.history_textbox.delete("1.0", "end")
        if entries:
            self.history_textbox.insert("1.0", "Completions:\n\n" + "\n".join(entries))
        else:
            self.history_textbox.insert("1.0", "No completions logged yet.")
        self.history_textbox.configure(state="disabled") # Make read-only

    def clear_selection(self):
        """Clears the entry fields and deselects any habit."""
        self.habit_entry.delete(0, 'end')
        self.selected_habit_id = None
        self.update_button.configure(state="disabled")
        self.delete_button.configure(state="disabled")
        
        # Clear the history view
        self.history_label.configure(text="Habit History")
        self.history_textbox.configure(state="normal")
        self.history_textbox.delete("1.0", "end")
        self.history_textbox.configure(state="disabled")

    def add_new_habit(self):
        """Adds a new habit from the entry box to the DB."""
        title = self.habit_entry.get()
        if title:
            db.add_habit(title, "user")
            self.clear_selection()
            self.load_habits() # Refresh the list

    def update_selected_habit(self):
        """Updates the selected habit's title in the DB."""
        new_title = self.habit_entry.get()
        if new_title and self.selected_habit_id is not None:
            db.update_habit(self.selected_habit_id, new_title)
            self.clear_selection()
            self.load_habits() # Refresh the list

    def delete_selected_habit(self):
        """Deletes the selected habit from the DB after confirmation."""
        if self.selected_habit_id is not None:
            # Show a confirmation popup
            if messagebox.askyesno("Delete Habit", "Are you sure you want to delete this habit and all its history?"):
                db.delete_habit(self.selected_habit_id)
                self.clear_selection()
                self.load_habits() # Refresh the list


# --- 3. The Help Frame ---
# A simple, static page with important text.
class HelpFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # A scrollable text box to hold the help info
        textbox = ctk.CTkTextbox(self, wrap="word")
        textbox.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        help_text = """
**You are not alone. Help is available.**

If you are in immediate danger, please call your local emergency services.

If you are in crisis or need someone to talk to, please reach out to one of these 24/7 confidential helplines:

**India:**
* **Vandrevala Foundation:** 9999 666 555 (24/7 Helpline)
* **KIRAN (Mental Health Rehabilitation Helpline):** 1800-599-0019 (24/7)
* **iCall (TISS):** 022-25521111 (Mon-Sat, 8am-10pm)

**Global Resources:**
* **Befrienders Worldwide:** https://www.befrienders.org/
    (Find a crisis center in your country)
* **Crisis Text Line:**
    * USA & Canada: Text HOME to 741741
    * UK: Text 85258
    * Ireland: Text 50808

This app is an AI companion and not a replacement for professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a mental health condition.
"""
        textbox.insert("1.0", help_text)
        textbox.configure(state="disabled", font=ctk.CTkFont(size=14)) # Make read-only


# --- 4. The Settings Frame ---
# This page will show model info and the "Clear Data" button.
class SettingsFrame(ctk.CTkFrame):
    def __init__(self, master, model_path, clear_data_callback):
        super().__init__(master)
        
        self.clear_data_callback = clear_data_callback
        
        self.pack_propagate(False) # Prevent frame from shrinking
        
        ctk.CTkLabel(self, text="Application Settings", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)
        
        # --- Model Info ---
        model_frame = ctk.CTkFrame(self)
        model_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(model_frame, text="AI Model Information", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Get just the file name from the full path
        model_name = os.path.basename(model_path)
        
        ctk.CTkLabel(model_frame, text=f"Model File: {model_name}").pack(padx=10, pady=2, anchor="w")
        ctk.CTkLabel(model_frame, text="Status: 100% On-Device").pack(padx=10, pady=2, anchor="w")
        ctk.CTkLabel(model_frame, text="Privacy: No data ever leaves your computer.").pack(padx=10, pady=(2, 10), anchor="w")

        # --- Privacy & Data ---
        privacy_frame = ctk.CTkFrame(self)
        privacy_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(privacy_frame, text="Data & Privacy", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        ctk.CTkLabel(privacy_frame, text="This will permanently delete all of your chat history, habits, and logs.", wraplength=400).pack(pady=10)
        
        clear_button = ctk.CTkButton(
            privacy_frame,
            text="Clear All App Data",
            fg_color="red",
            hover_color="darkred",
            command=self.on_clear_data_pressed # Calls the function below
        )
        clear_button.pack(pady=20, ipadx=10, ipady=10)

    def on_clear_data_pressed(self):
        """Shows a confirmation dialog before deleting data."""
        # Show a popup and only proceed if the user clicks "Yes"
        if messagebox.askyesno("Confirm Deletion", "Are you sure you want to permanently delete ALL app data? This cannot be undone."):
            print("User confirmed data deletion.")
            self.clear_data_callback() # Call the main app's function