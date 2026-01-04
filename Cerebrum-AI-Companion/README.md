# Cerebrum: A Privacy-First, On-Device AI Mental Health Assistant

**Cerebrum** is a 100% private, on-device AI companion built for a B.Tech final year project. It provides an empathetic chatbot, habit tracking, and mental health resources, all while ensuring **no user data ever leaves your computer.**

The application is built with Python and utilizes a locally-run, 4-bit quantized GGUF model (Gemma 7B) to ensure 100% on-device processing.



## Core Principles

* **Privacy-by-Design:** All AI inference and data storage happens locally. The application is not capable of sending or receiving data from the internet.
* **User Control:** The user has full control over their data, including a one-button "Clear All App Data" function to instantly delete all local chat logs and habit history.

## 🚀 Core Features

* **On-Device AI Chatbot:** An empathetic, streaming chatbot powered by a `Gemma-7B-IT-Q4_K_M.gguf` model running via `llama-cpp-python`.
* **Automatic Habit Integration:** The AI can suggest habits (using a `[HABIT: ...] ` tag) which are automatically parsed and added to the user's habit tracker.
* **Full CRUD Habit Tracker:** A complete UI to create, read, update, and delete (CRUD) both AI-suggested and manually-entered habits.
* **Privacy & Settings:** A dedicated screen to view model information and use the "Clear All App Data" function for complete privacy.
* **Help Resources:** A static, read-only page displaying a list of emergency mental health helplines and resources.

## 🛠️ Technical Stack

* **Application (UI):** Python with `customtkinter` for a modern, themeable interface.
* **Database:** Python's built-in `sqlite3` for all local data storage.
* **AI Model:** `Gemma-7B-IT-Q4_K_M.gguf` (4-bit quantized GGUF).
* **On-Device Inference:** `llama-cpp-python` (Python bindings for the high-performance llama.cpp).
* **Concurrency:** Python's `threading` and `self.after()` (Tkinter) to run model inference in a separate thread, preventing UI freezing and enabling a real-time, streaming response.

## ⚙️ How to Run

1.  **Prerequisites:**
    * Python 3.10+
    * (Windows) Visual Studio 2022 Build Tools with the "Desktop development with C++" workload installed.

2.  **Clone the repository (or download the ZIP):**
    ```bash
    git clone https://your-repo-url/CerebrumPy.git
    cd CerebrumPy
    ```

3.  **Set up the Virtual Environment:**
    ```bash
    # Create the environment
    python -m venv venv
    
    # Activate the environment
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

4.  **Install Dependencies:**
    * **On Windows,** it is **CRITICAL** to use the **`x64 Native Tools Command Prompt for VS 2022`** for this step to build `llama-cpp-python` correctly.
    * Inside the activated x64 terminal:
    ```bash
    # This command forces a clean, 64-bit build from source.
    pip install --no-cache-dir --no-binary :all: llama-cpp-python
    
    # Now install the rest
    pip install -r app/requirements.txt
    ```

5.  **Run the Application:**
    Once all dependencies are installed, run the main app module:
    ```bash
    python -m app.app
    ```
    The app will take 30-60 seconds to load the 5.33GB model into RAM, after which the status will change to "Model: Ready".