# Cerebrum: Privacy-First, On-Device AI Mental Health Companion

Cerebrum is a secure, empathetic AI companion designed to provide mental health support while ensuring absolute data sovereignty. Unlike traditional AI wellness platforms that rely on cloud-based processing, Cerebrum performs all AI inference and data storage locally on the user's desktop.



## 🌟 Key Features
- **Total Privacy:** No data is transmitted to external servers. All conversations stay on your machine.
- **On-Device Inference:** Utilizes a 4-bit quantized Gemma-7B model for real-time, empathetic responses.
- **Habit Tracking:** Automatically extracts actionable wellness goals from your conversation using AI-driven structured tagging.
- **Data Sovereignty:** Built-in features to view, export, or permanently delete your local SQLite database.

## 🏗️ Technical Architecture
The application follows a modular "Edge AI" design:
- **Frontend:** CustomTkinter (Modern, lightweight desktop GUI).
- **Inference Engine:** `llama-cpp-python` (Optimized for CPU-based local execution).
- **Storage:** SQLite3 (Serverless relational database for chat history and habit logs).
- **Concurrency:** Multi-threaded execution to ensure a responsive UI during model inference.



## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.10+**
- **Hardware:** 8GB RAM (16GB recommended).
- **C++ Compiler:** Required for installing `llama-cpp-python`. On Windows, install [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/).

### 2. Installation
```powershell
# Clone the repository
git clone [https://github.com/Arpitwasnotavaliable/Cerebrum-AI-Companion.git](https://github.com/Arpitwasnotavaliable/Cerebrum-AI-Companion.git)
cd Cerebrum-AI-Companion

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
