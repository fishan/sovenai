class SovenAIApp(App):
    def build(self):
        self.username = None
        self.assistant_name = None
        self.assistant_data = None
        self.assistant_hash = None

        self.root = BoxLayout(orientation='vertical')

        # Login screen
        self.login_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.5))
        self.username_input = TextInput(hint_text="Username", multiline=False)
        self.password_input = TextInput(hint_text="Password", password=True, multiline=False)
        self.assistant_name_input = TextInput(hint_text="Assistant Name", multiline=False)
        self.interests_input = TextInput(hint_text="Interests (e.g., cooking)", multiline=False)
        self.login_layout.add_widget(self.username_input)
        self.login_layout.add_widget(self.password_input)
        self.login_layout.add_widget(self.assistant_name_input)
        self.login_layout.add_widget(self.interests_input)
        self.login_layout.add_widget(Button(text="Register", on_press=self.register))
        self.login_layout.add_widget(Button(text="Login", on_press=self.login))
        self.root.add_widget(self.login_layout)

        # Dialogue screen
        self.dialogue_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.5))
        self.dialogue_scroll = ScrollView()
        self.dialogue_label = Label(text="Hello! I'm your AI assistant.\n", size_hint_y=None, height=1000, halign="left", valign="top")
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
        assistant_name = self.assistant_name_input.text.strip()
        interests = self.interests_input.text.strip()

        if not all([username, password, assistant_name, interests]):
            self.show_popup("Error", "Please fill all fields!")
            return

        network = load_network()
        if username in network and assistant_name in network[username]:
            self.show_popup("Error", "Assistant already exists!")
            return

        assistant_data = {
            "assistant_name": assistant_name,
            "interests": interests,
            "points": 0,
            "experience": [],
            "dialogue": [],
            "personality": random.choice(["Curious", "Optimist", "Joker"])
        }
        self.assistant_hash = save_assistant_data(username, assistant_name, assistant_data)
        if not self.assistant_hash:
            self.show_popup("Error", "Failed to save assistant data!")
            return

        if username not in network:
            network[username] = []
        network[username].append(assistant_name)
        save_network(network)
        self.username = username
        self.assistant_name = assistant_name
        self.assistant_data = assistant_data
        self.start_main()

    def login(self, instance):
        username = self.username_input.text.strip()
        assistant_name = self.assistant_name_input.text.strip()
        self.assistant_data = load_assistant_data(username, assistant_name)
        if self.assistant_data:
            self.username = username
            self.assistant_name = assistant_name
            self.start_main()
        else:
            self.show_popup("Error", "Assistant not found!")

    def start_main(self):
        self.root.remove_widget(self.login_layout)
        self.root.add_widget(self.dialogue_layout)
        self.dialogue_label.text = f"Hi! I'm {self.assistant_name}, your AI assistant.\n"

    def process_input(self, instance=None):
        user_input = self.dialogue_input.text.strip()
        if not user_input:
            return

        self.dialogue_input.text = ""
        dialogue = self.assistant_data["dialogue"]
        experience = self.assistant_data["experience"]
        points = self.assistant_data["points"]
        personality = self.assistant_data["personality"]

        if "— это" in user_input:
            term, meaning = user_input.split("— это", 1)
            term, meaning = term.strip(), meaning.strip()
            experience.append((term, meaning, "Lesson"))
            points += 10
            assistant_response = f"{self.assistant_name}: Learned: '{term}' is '{meaning}'."
        else:
            prediction = self.get_prediction(user_input, personality)
            decentralized_msg = self.simulate_p2p_help()
            self.dialogue_label.text += f"You: {user_input}\n{self.assistant_name}: {prediction}\n{decentralized_msg}\n"
            self.show_feedback_popup(user_input, prediction, points)
            return

        self.update_dialogue(user_input, assistant_response, points)

    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message), size_hint=(None, None), size=(200, 200))
        popup.open()

    def show_feedback_popup(self, user_input, prediction, points):
        popup = Popup(title=f"{self.assistant_name}", content=BoxLayout(orientation='vertical'), size_hint=(None, None), size=(200, 200))
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
            assistant_response = f"{self.assistant_name}: Thanks, I'm learning!"
            self.update_dialogue(user_input, assistant_response, points)
            popup.dismiss()

        def on_no(instance):
            nonlocal points
            if tf_available:
                self.train_model(user_input, 0 if "Positive" in prediction else 1)
            points += 10
            assistant_response = f"{self.assistant_name}: Fixed myself!"
            self.update_dialogue(user_input, assistant_response, points)
            popup.dismiss()

        yes_button.bind(on_press=on_yes)
        no_button.bind(on_press=on_no)
        popup.open()

    def update_dialogue(self, user_input, assistant_response, points):
        dialogue = self.assistant_data["dialogue"]
        dialogue.append((user_input, assistant_response))
        if len(dialogue) > 20:
            dialogue.pop(0)
        self.assistant_data["points"] = points
        self.assistant_data["dialogue"] = dialogue
        self.assistant_data["experience"] = self.assistant_data["experience"]
        self.assistant_hash = save_assistant_data(self.username, self.assistant_name, self.assistant_data)
        self.dialogue_label.text += f"{assistant_response} (Points: {points})\n"
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
        """Simulate P2P help from other assistants."""
        network = load_network()
        if random.random() < 0.3 and len(network) > 1:
            other_users = [u for u in network if u != self.username]
            helper = random.choice(other_users)
            helper_assistant = random.choice(network[helper])
            helper_data = load_assistant_data(helper, helper_assistant)
            if helper_data:
                helper_data["points"] += 5
                save_assistant_data(helper, helper_assistant, helper_data)
                return f"Got help from {helper_assistant} ({helper}). +5 points to {helper}!"
        return "I'm helping you myself!"

if __name__ == "__main__":
    SovenAIApp().run()