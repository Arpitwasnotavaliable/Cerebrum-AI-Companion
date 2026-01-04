# app/model_manager.py
import os
from llama_cpp import Llama

# --- Configuration ---
# This builds the correct path to the model file.
# It goes "up" one level from 'app' to 'CerebrumPy', then "down" into 'model'.
APP_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_NAME = "gemma-1.1-7b-it-Q4_K_M.gguf" # The file you downloaded
MODEL_PATH = os.path.join(APP_DIR, "..", "model", MODEL_NAME)
# ---------------------

# This is the "personality" we give our AI.
# It's the first thing the AI reads when it loads.
SYSTEM_PROMPT = """You are Cerebrum, a private, on-device AI assistant. 
Your personality is empathetic, non-judgmental, and supportive. 
Your goal is to listen to the user and help them reflect.
If you sense the user is struggling with focus, stress, or low mood, you can suggest a simple, actionable wellness habit.
When you suggest a habit, YOU MUST format it as [HABIT: The habit text].
For example: [HABIT: Try 5 minutes of mindful breathing] or [HABIT: Go for a short walk outside].
Never break character. Be a supportive companion.
If the user mentions suicide or severe self-harm, provide the helpline info from the app's 'Help' section and gently encourage them to use it."""

class ModelManager:
    def __init__(self, model_path=MODEL_PATH):
        """
        Initializes the ModelManager.
        """
        self.model_path = model_path
        self.model = None
        self.is_loaded = False
        
        # Check if the model file exists before we do anything
        if not os.path.exists(self.model_path):
            print(f"Error: Model file not found at {self.model_path}")
            # As a fallback, try to find *any* GGUF file in the model dir
            model_dir = os.path.dirname(self.model_path)
            gguf_files = [f for f in os.listdir(model_dir) if f.endswith(".gguf")]
            if gguf_files:
                self.model_path = os.path.join(model_dir, gguf_files[0])
                print(f"Warning: Using fallback model: {self.model_path}")
            else:
                raise FileNotFoundError(f"No GGUF model file found in {model_dir}")
        print(f"ModelManager initialized. Model path set to: {self.model_path}")

    def load_model(self):
        """
        Loads the GGUF model into memory.
        This is a heavy, blocking operation and should be run in a separate thread.
        """
        print("Loading model... This may take a few minutes.")
        try:
            self.model = Llama(
                model_path=self.model_path,
                n_ctx=2048,      # Context window size (how much text it can remember)
                n_gpu_layers=-1, # Offload all possible layers to GPU (if you have one)
                chat_format="gemma", # <-- CRITICAL: Tells it to use Gemma's chat template
                verbose=True
            )
            self.is_loaded = True
            print("Model loaded successfully.")
        except Exception as e:
            print(f"CRITICAL Error loading model: {e}")
            self.is_loaded = False

    def is_model_loaded(self):
        """Returns True if the model is loaded, False otherwise."""
        return self.is_loaded

    def unload_model(self):
        """Unloads the model from memory."""
        if self.model:
            # llama-cpp-python doesn't have an explicit 'unload',
            # so we delete the object and let Python's garbage collector free the memory.
            del self.model
            self.model = None
            self.is_loaded = False
            print("Model unloaded.")

    def generate_response(self, chat_history, on_token_callback):
        """
        Generates a streaming response from the model.
        
        :param chat_history: A list of message dicts (e.g., [{"role": "user", "content": "Hi"}])
        :param on_token_callback: A function to call with each new token (e.g., on_token_callback(token))
        :return: The full, complete response string.
        """
        if not self.is_loaded or not self.model:
            print("Error: Model is not loaded.")
            on_token_callback("\n[Error: Model is not loaded.]")
            return None

        # Combine our permanent system prompt with the user's chat history
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + chat_history

        try:
            # create_chat_completion with stream=True returns a generator
            stream = self.model.create_chat_completion(
                messages=messages,
                stream=True,
                temperature=0.7,
            )
            
            full_response = ""
            for chunk in stream:
                # 'delta' contains the *new* information in this chunk
                delta = chunk['choices'][0]['delta']
                
                # We are only interested in new 'content' (the text tokens)
                if 'content' in delta:
                    token = delta['content']
                    full_response += token
                    
                    # This is the "callback"
                    # It sends the single token back to the UI thread immediately
                    on_token_callback(token)
            
            return full_response # Return the complete string for saving to DB
            
        except Exception as e:
            print(f"Error during model inference: {e}")
            on_token_callback(f"\n[Error: {e}]")
            return None