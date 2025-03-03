from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.logger import Logger
import random
import json
import os

# TensorFlow Lite
try:
    import tensorflow as tf
    interpreter = tf.lite.Interpreter(model_path="distilbert.tflite")
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    tf_available = True
except Exception as e:
    Logger.error(f"TensorFlow Lite failed to load: {e}")
    interpreter = None
    tf_available = False

# IPFS
try:
    import ipfshttpclient
    ipfs_client = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001', timeout=10)
    ipfs_available = True
except Exception as e:
    Logger.error(f"IPFS connection failed: {e}")
    ipfs_client = None
    ipfs_available = False

# Data storage
DATA_DIR = "user_data"
NETWORK_FILE = "network.json"

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def save_network(data):
    """Save network data to IPFS or local file."""
    try:
        if ipfs_available:
            hash_val = ipfs_client.add_json(data)
            Logger.info(f"Network saved to IPFS: {hash_val}")
            return hash_val
        with open(NETWORK_FILE, "w") as f:
            json.dump(data, f)
        return NETWORK_FILE
    except Exception as e:
        Logger.error(f"Failed to save network: {e}")
        return None

def load_network():
    """Load network data from local file or return empty dict."""
    try:
        if os.path.exists(NETWORK_FILE):
            with open(NETWORK_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        Logger.error(f"Failed to load network: {e}")
    return {}

def save_pet_data(username, pet_name, data):
    """Save pet data to IPFS or local file."""
    try:
        if ipfs_available:
            hash_val = ipfs_client.add_json(data)
            Logger.info(f"Pet data saved to IPFS: {hash_val}")
            return hash_val
        file_path = os.path.join(DATA_DIR, f"{username}_{pet_name}.json")
        with open(file_path, "w") as f:
            json.dump(data, f)
        return file_path
    except Exception as e:
        Logger.error(f"Failed to save pet data: {e}")
        return None

def load_pet_data(username, pet_name, hash_val=None):
    """Load pet data from IPFS or local file."""
    try:
        if ipfs_available and hash_val:
            return ipfs_client.get_json(hash_val)
        file_path = os.path.join(DATA_DIR, f"{username}_{pet_name}.json")
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)
    except Exception as e:
        Logger.error(f"Failed to load pet data: {e}")
    return None

class PetApp(App):
    def build(self):
        self.username = None
        self.pet_name = None
        self.pet_data = None
        self.pet_hash = None

        self.root = BoxLayout(orientation='vertical')

        # Login screen
        self.login_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.5))
        self.username_input = TextInput(hint_text="Username", multiline=False)
        self.password_input = TextInput(hint_text="Password", password=True, multiline=False)
        self.pet_name_input = TextInput(hint_text="Pet Name", multiline=False)
        self.interests_input = TextInput(hint_text="Interests (e.g., cooking)", multiline=False)
        self.login_layout.add_widget(self.username_input)
        self.login_layout.add_widget(self.password_input)
        self.login_layout.add_widget(self.pet_name_input)
        self.login_layout.add_widget(self.interests_input)
        self.login_layout.add_widget(Button(text="Register", on_press=self.register))
        self.login_layout.add_widget(Button(text="Login", on_press=self.login))
        self.root.add_widget(self.login_layout)

        # Dialogue screen
        self.dialogue_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.5))
        self.dialogue_scroll = ScrollView()
        self.dialogue_label = Label(text="Hello! I'm your AI pet.\n", size_hint_y=None, height=1000, halign="left", valign="top")
        self.dialogue_label.bind(size=self.dialogue_label.setter('text_size'))
        self.dialogue_scroll.add_widget(self.dialogue_label)
        self.dialogue_input = TextInput(hint_text="Talk to me", size_hint=(1, 0.2), multiline=False)
        self.dialogue_input.bind(on_text_validate=self.process_input)
        self.dialogue_layout.add_widget(self.dialogue_scroll)
        self.dialogue_layout.add_widget(self.dialogue_input)
        self.dialogue_layout.add_widget(Button(text="Send", on_press=self.process_input))

        return self.root

    def register(self, instance):
        username = self.username_input.text.strip()
        password = self.password_input.text.strip()
        pet_name = self.pet_name_input.text.strip()
        interests = self.interests_input.text.strip()

        if not all([username, password, pet_name, interests]):
            self.show_popup("Error", "Please fill all fields!")
            return

        network = load_network()
        if username in network and pet_name in network[username]:
            self.show_popup("Error", "Pet already exists!")
            return

        pet_data = {
            "pet_name": pet_name,
            "interests": interests,
            "points": 0,
            "experience": [],
            "dialogue": [],
            "personality": random.choice(["Curious", "Optimist", "Joker"])
        }
        self.pet_hash = save_pet_data(username, pet_name, pet_data)
        if not self.pet_hash:
            self.show_popup("Error", "Failed to save pet data!")
            return

        if username not in network:
            network[username] = []
        network[username].append(pet_name)
        save_network(network)
        self.username = username
        self.pet_name = pet_name
        self.pet_data = pet_data
        self.start_main()

    def login(self, instance):
        username = self.username_input.text.strip()
        pet_name = self.pet_name_input.text.strip()
        self.pet_data = load_pet_data(username, pet_name)
        if self.pet_data:
            self.username = username
            self.pet_name = pet_name
            self.start_main()
        else:
            self.show_popup("Error", "Pet not found!")

    def start_main(self):
        self.root.remove_widget(self.login_layout)
        self.root.add_widget(self.dialogue_layout)
        self.dialogue_label.text = f"Hi! I'm {self.pet_name}, your AI pet.\n"

    def process_input(self, instance=None):
        user_input = self.dialogue_input.text.strip()
        if not user_input:
            return

        self.dialogue_input.text = ""
        dialogue = self.pet_data["dialogue"]
        experience = self.pet_data["experience"]
        points = self.pet_data["points"]
        personality = self.pet_data["personality"]

        if "— это" in user_input:
            term, meaning = user_input.split("— это", 1)
            term, meaning = term.strip(), meaning.strip()
            experience.append((term, meaning, "Lesson"))
            points += 10
            pet_response = f"{self.pet_name}: Learned: '{term}' is '{meaning}'."
        else:
            prediction = self.get_prediction(user_input, personality)
            decentralized_msg = self.simulate_p2p_help()
            self.dialogue_label.text += f"You: {user_input}\n{self.pet_name}: {prediction}\n{decentralized_msg}\n"
            self.show_feedback_popup(user_input, prediction, points)
            return

        self.update_dialogue(user_input, pet_response, points)

    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message), size_hint=(None, None), size=(200, 200))
        popup.open()

    def show_feedback_popup(self, user_input, prediction, points):
        popup = Popup(title=f"{self.pet_name}", content=BoxLayout(orientation='vertical'), size_hint=(None, None), size=(200, 200))
        popup.content.add_widget(Label(text="Did I guess your mood right?"))
        yes_button = Button(text="Yes")
        no_button = Button(text="No")
        popup.content.add_widget(yes_button)
        popup.content.add_widget(no_button)

        def on_yes(instance):
            nonlocal points
            if tf_available:
                self.train_model(user_input, 1 if "Positive" in prediction else 0)
            points += 5
            pet_response = f"{self.pet_name}: Thanks, I'm learning!"
            self.update_dialogue(user_input, pet_response, points)
            popup.dismiss()

        def on_no(instance):
            nonlocal points
            if tf_available:
                self.train_model(user_input, 0 if "Positive" in prediction else 1)
            points += 10
            pet_response = f"{self.pet_name}: Fixed myself!"
            self.update_dialogue(user_input, pet_response, points)
            popup.dismiss()

        yes_button.bind(on_press=on_yes)
        no_button.bind(on_press=on_no)
        popup.open()

    def update_dialogue(self, user_input, pet_response, points):
        dialogue = self.pet_data["dialogue"]
        dialogue.append((user_input, pet_response))
        if len(dialogue) > 20:
            dialogue.pop(0)
        self.pet_data["points"] = points
        self.pet_data["dialogue"] = dialogue
        self.pet_data["experience"] = self.pet_data["experience"]
        self.pet_hash = save_pet_data(self.username, self.pet_name, self.pet_data)
        self.dialogue_label.text += f"{pet_response} (Points: {points})\n"
        self.dialogue_scroll.scroll_y = 0  # Auto-scroll bottom

    def train_model(self, text, label):
        """Placeholder for TFLite training (not supported natively)."""
        if tf_available:
            Logger.info(f"Training stub: Text='{text}', Label={label}")
            # TFLite не поддерживает обучение, дообучай на ПК

    def get_prediction(self, text, personality):
        """Predict sentiment with TFLite or fallback."""
        positive_words = ["good", "fun", "happy", "love"]
        negative_words = ["sad", "bad", "angry"]
        text_lower = text.lower()

        if tf_available and interpreter:
            try:
                inputs = tf.constant([text_lower.encode('utf-8')], shape=(1,), dtype=tf.string)
                interpreter.set_tensor(input_details[0]['index'], inputs)
                interpreter.invoke()
                output = interpreter.get_tensor(output_details[0]['index'])
                prediction = 1 if output[0][1] > output[0][0] else 0
                base_response = "Positive" if prediction == 1 else "Negative"
            except Exception as e:
                Logger.error(f"TFLite prediction failed: {e}")
                base_response = self._fallback_prediction(text_lower, positive_words, negative_words)
        else:
            base_response = self._fallback_prediction(text_lower, positive_words, negative_words)

        return self._personalize_response(base_response, personality)

    def _fallback_prediction(self, text, positive_words, negative_words):
        """Fallback sentiment prediction."""
        if any(word in text for word in positive_words):
            return "Positive"
        elif any(word in text for word in negative_words):
            return "Negative"
        return "Neutral"

    def _personalize_response(self, base_response, personality):
        """Personalize response based on personality."""
        if base_response == "Negative":
            if personality == "Curious":
                return "You seem upset. What's wrong?"
            elif personality == "Optimist":
                return "Cheer up, it'll be okay!"
            else:  # Joker
                return "Feeling down? My jokes scare sadness away!"
        else:
            if personality == "Curious":
                return f"{base_response}. Why's that?"
            elif personality == "Optimist":
                return f"{base_response}. Awesome!"
            else:  # Joker
                return f"{base_response}. Told you I'm smart!"
        return f"{base_response}. What's up?"

    def simulate_p2p_help(self):
        """Simulate P2P help from other pets."""
        network = load_network()
        if random.random() < 0.3 and len(network) > 1:
            other_users = [u for u in network if u != self.username]
            helper = random.choice(other_users)
            helper_pet = random.choice(network[helper])
            helper_data = load_pet_data(helper, helper_pet)
            if helper_data:
                helper_data["points"] += 5
                save_pet_data(helper, helper_pet, helper_data)
                return f"Got help from {helper_pet} ({helper}). +5 points to {helper}!"
        return "I'm helping you myself!"

if __name__ == "__main__":
    PetApp().run()
