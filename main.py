import streamlit as st
import random
import json
import re
from datetime import datetime
import pickle
import os

# Set page config
st.set_page_config(
    page_title="Free Unlimited Chatbot 🤖",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===========================================
# CUSTOM STYLING - No API calls needed
# ===========================================
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Chat containers */
    .stChatMessage {
        border-radius: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
        background: rgba(255, 255, 255, 0.15);
    }
    
    /* User message */
    .stChatMessage[data-testid*="user"] {
        background: rgba(56, 139, 253, 0.25);
        border-left: 5px solid #3889fd;
    }
    
    /* Bot message */
    .stChatMessage[data-testid*="assistant"] {
        background: rgba(155, 81, 224, 0.25);
        border-left: 5px solid #9b51e0;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(45deg, #6a11cb 0%, #2575fc 100%);
        color: white;
        font-weight: bold;
        border: none;
        border-radius: 10px;
        padding: 12px 24px;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2);
    }
    
    /* Input box */
    .stChatInput {
        border-radius: 15px;
        border: 2px solid rgba(255, 255, 255, 0.3);
        background: rgba(255, 255, 255, 0.1);
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: rgba(30, 30, 46, 0.8);
    }
    
    /* Headers */
    h1, h2, h3 {
        color: white !important;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #00ffaa !important;
        font-size: 2rem !important;
    }
    
    /* Divider */
    hr {
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# ===========================================
# KNOWLEDGE BASE SYSTEM
# ===========================================
class KnowledgeBase:
    def __init__(self):
        self.jokes = []
        self.qa_pairs = []
        self.facts = []
        self.load_data()
    
    def load_data(self):
        """Load and categorize data from data.txt"""
        try:
            with open('data.txt', 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
            
            for line in lines:
                # Check if it's a Q&A pair (contains ? and answer)
                if '?' in line and ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        question = parts[0].strip()
                        answer = parts[1].strip()
                        if question.endswith('?'):
                            self.qa_pairs.append({'question': question, 'answer': answer})
                            continue
                
                # Check if it's a joke (contains punchline keywords)
                joke_keywords = ['joke', 'funny', 'laugh', 'pun', 'humor', 'why did', 'what do you call']
                if any(keyword in line.lower() for keyword in joke_keywords):
                    self.jokes.append(line)
                else:
                    self.facts.append(line)
            
            # If no data loaded, use default
            if not any([self.jokes, self.qa_pairs, self.facts]):
                self.load_default_data()
                
        except FileNotFoundError:
            self.load_default_data()
    
    def load_default_data(self):
        """Load default data if data.txt is empty"""
        self.jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "I told my wife she was drawing her eyebrows too high. She looked surprised.",
            "What do you call fake spaghetti? An impasta!",
            "Why did the scarecrow win an award? He was outstanding in his field!",
            "How does a penguin build its house? Igloos it together!",
        ]
        
        self.qa_pairs = [
            {'question': 'What is the capital of France?', 'answer': 'Paris'},
            {'question': 'Who painted the Mona Lisa?', 'answer': 'Leonardo da Vinci'},
            {'question': 'What is the largest planet?', 'answer': 'Jupiter'},
            {'question': 'How many continents are there?', 'answer': '7 continents'},
            {'question': 'What is the chemical symbol for water?', 'answer': 'H2O'},
        ]
        
        self.facts = [
            "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly good to eat.",
            "Octopuses have three hearts. Two pump blood to the gills, while the third pumps it to the rest of the body.",
            "Bananas are berries, but strawberries aren't.",
            "A group of flamingos is called a 'flamboyance'.",
            "The shortest war in history was between Britain and Zanzibar on August 27, 1896. It lasted only 38 minutes.",
        ]

# ===========================================
# CHATBOT BRAIN
# ===========================================
class ChatBot:
    def __init__(self):
        self.kb = KnowledgeBase()
        self.mood = "friendly"
        self.conversation_history = []
        
    def find_best_answer(self, question):
        """Find the best matching answer from knowledge base"""
        question_lower = question.lower()
        
        # Check for exact match in Q&A
        for qa in self.kb.qa_pairs:
            if qa['question'].lower() in question_lower or question_lower in qa['question'].lower():
                return qa['answer']
        
        # Check for keyword matching
        best_match = None
        best_score = 0
        
        for qa in self.kb.qa_pairs:
            score = 0
            q_words = set(qa['question'].lower().split())
            u_words = set(question_lower.split())
            common = q_words.intersection(u_words)
            score = len(common) / max(len(q_words), 1)
            
            if score > best_score and score > 0.3:
                best_score = score
                best_match = qa['answer']
        
        if best_match:
            return best_match
        
        # If no match found, provide a relevant response
        return self.generate_smart_response(question)
    
    def generate_smart_response(self, question):
        """Generate a smart response when no direct answer is found"""
        question_lower = question.lower()
        
        response_types = {
            'joke': ["I don't know the answer, but here's a joke to cheer you up: ", 
                    "That's a tricky one! While I think about it, enjoy this joke: "],
            'fact': ["I'm not sure about that, but here's an interesting fact: ",
                    "Great question! I don't have that answer, but did you know: "],
            'help': ["I'm still learning! Could you rephrase your question? ",
                    "I don't have that information yet. Try asking me something else or tell me a 'joke'!"]
        }
        
        # Check question type
        if any(word in question_lower for word in ['who', 'what', 'where', 'when', 'why', 'how']):
            # It's a factual question
            if random.random() > 0.5 and self.kb.facts:
                return random.choice(response_types['fact']) + random.choice(self.kb.facts)
        
        # Default to joke or helpful response
        if random.random() > 0.3 and self.kb.jokes:
            return random.choice(response_types['joke']) + random.choice(self.kb.jokes)
        
        return random.choice(response_types['help'])
    
    def get_response(self, user_input):
        """Main response generator"""
        user_input = user_input.strip()
        
        # Greetings
        greetings = ['hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening']
        if any(user_input.lower().startswith(g) for g in greetings):
            responses = [
                "Hello there! 👋 I'm your free unlimited chatbot! Ask me anything or say 'joke' for humor!",
                "Hey! 🤗 Ready to chat about anything? I know jokes, facts, and can answer questions!",
                "Hi! 😊 I'm here 24/7 with unlimited free chatting! What's on your mind?"
            ]
            return random.choice(responses)
        
        # Farewells
        farewells = ['bye', 'goodbye', 'exit', 'quit', 'see you', 'farewell']
        if any(user_input.lower().startswith(f) for f in farewells):
            responses = [
                "Goodbye! 👋 Thanks for chatting! Come back anytime - I'm always free!",
                "See you later! 😊 Remember, I'm always here with unlimited free chats!",
                "Bye! 🎉 Don't forget to tell your friends about our free unlimited conversations!"
            ]
            return random.choice(responses)
        
        # Joke requests
        joke_triggers = ['joke', 'funny', 'make me laugh', 'humor', 'tell joke', 'pun']
        if any(trigger in user_input.lower() for trigger in joke_triggers):
            if self.kb.jokes:
                prefix = random.choice([
                    "😂 Here's a fresh joke for you: ",
                    "🎭 Get ready to laugh: ",
                    "😄 This one always cracks me up: "
                ])
                return prefix + random.choice(self.kb.jokes)
            else:
                return "I'm out of jokes! 😅 Add some to data.txt or just chat with me!"
        
        # Fact requests
        fact_triggers = ['fact', 'interesting', 'did you know', 'tell me something']
        if any(trigger in user_input.lower() for trigger in fact_triggers):
            if self.kb.facts:
                prefix = random.choice([
                    "🧠 Interesting fact: ",
                    "📚 Did you know? ",
                    "🌟 Here's a cool fact: "
                ])
                return prefix + random.choice(self.kb.facts)
        
        # Question - try to answer from knowledge base
        if '?' in user_input or any(word in user_input.lower() for word in ['what', 'how', 'why', 'when', 'where', 'who']):
            answer = self.find_best_answer(user_input)
            return answer
        
        # Default conversational response
        responses = [
            f"Interesting point about '{user_input[:30]}...'! What else would you like to know?",
            "I hear you! Ask me a question, request a joke, or just keep chatting!",
            "Got it! I'm here for unlimited free conversation. What's next?",
            "Thanks for sharing! I'm always learning. What would you like to discuss?",
            "Nice! I'm your 24/7 free chatbot companion. How can I help you today?"
        ]
        return random.choice(responses)

# ===========================================
# STREAMLIT APP
# ===========================================
def main():
    # Initialize session state
    if 'bot' not in st.session_state:
        st.session_state.bot = ChatBot()
    
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "🌟 **Welcome to FREE Unlimited Chatbot!** 🤖\n\nI'm your 100% free, no-limits AI companion! I can:\n• Tell jokes 🎭\n• Answer questions ❓\n• Share facts 📚\n• Chat about anything! 💬\n\nType 'joke' for humor or ask me anything!"}
        ]
    
    if 'message_count' not in st.session_state:
        st.session_state.message_count = 0
    
    if 'conversation_start' not in st.session_state:
        st.session_state.conversation_start = datetime.now()
    
    # Header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🤖 FREE Unlimited Chatbot")
        st.markdown("### 💬 **100% Free • No Limits • Always Online**")
    
    # Main layout
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Chat history
        chat_container = st.container(height=500)
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Type your message here... (100% free, no limits)"):
            # Increment message counter
            st.session_state.message_count += 1
            
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)
            
            # Get bot response
            with st.spinner("Thinking..."):
                response = st.session_state.bot.get_response(prompt)
            
            # Add bot response
            st.session_state.messages.append({"role": "assistant", "content": response})
            with chat_container:
                with st.chat_message("assistant"):
                    st.markdown(response)
    
    with col2:
        # Sidebar controls
        st.sidebar.header("📊 Chat Stats")
        
        # Calculate chat duration
        duration = datetime.now() - st.session_state.conversation_start
        hours, remainder = divmod(duration.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        st.sidebar.metric("💬 Messages Sent", st.session_state.message_count)
        st.sidebar.metric("⏱️ Chat Duration", f"{hours}h {minutes}m")
        st.sidebar.metric("💰 Cost", "$0.00")
        
        st.sidebar.markdown("---")
        st.sidebar.header("⚙️ Quick Actions")
        
        # Quick action buttons
        if st.sidebar.button("🎭 Tell me a joke!", use_container_width=True):
            st.session_state.message_count += 1
            joke_response = st.session_state.bot.get_response("joke")
            st.session_state.messages.append({"role": "assistant", "content": joke_response})
            st.rerun()
        
        if st.sidebar.button("📚 Share a fact", use_container_width=True):
            st.session_state.message_count += 1
            if st.session_state.bot.kb.facts:
                fact_response = "📚 **Did you know?** " + random.choice(st.session_state.bot.kb.facts)
                st.session_state.messages.append({"role": "assistant", "content": fact_response})
                st.rerun()
        
        if st.sidebar.button("🔄 Clear chat", use_container_width=True):
            st.session_state.messages = [
                {"role": "assistant", "content": "🌟 **Welcome back!** Chat has been cleared. Ready for more unlimited free chatting! 🤖"}
            ]
            st.session_state.conversation_start = datetime.now()
            st.rerun()
        
        st.sidebar.markdown("---")
        st.sidebar.header("📝 Manage Knowledge")
        
        # Add new knowledge
        with st.sidebar.expander("➕ Add new content"):
            content_type = st.selectbox("Type:", ["Joke", "Q&A Pair", "Fact"])
            new_content = st.text_area("Content:")
            
            if st.button("Add to bot"):
                if new_content:
                    if content_type == "Joke":
                        st.session_state.bot.kb.jokes.append(new_content)
                    elif content_type == "Q&A Pair":
                        if '?' in new_content:
                            parts = new_content.split(':', 1)
                            if len(parts) == 2:
                                qa = {'question': parts[0].strip(), 'answer': parts[1].strip()}
                                st.session_state.bot.kb.qa_pairs.append(qa)
                    else:  # Fact
                        st.session_state.bot.kb.facts.append(new_content)
                    
                    # Save to data.txt
                    with open('data.txt', 'a', encoding='utf-8') as f:
                        f.write(f"\n{new_content}")
                    
                    st.success(f"✅ Added new {content_type.lower()}!")
        
        # Knowledge stats
        st.sidebar.markdown("---")
        st.sidebar.subheader("🧠 Knowledge Base")
        st.sidebar.write(f"🎭 Jokes: {len(st.session_state.bot.kb.jokes)}")
        st.sidebar.write(f"❓ Q&A Pairs: {len(st.session_state.bot.kb.qa_pairs)}")
        st.sidebar.write(f"📚 Facts: {len(st.session_state.bot.kb.facts)}")
    
    # Footer
    st.markdown("---")
    footer_col1, footer_col2, footer_col3 = st.columns(3)
    with footer_col1:
        st.markdown("### 🚀 **Features**")
        st.markdown("• 🤖 **Unlimited Chatting**")
        st.markdown("• 💯 **100% Free Forever**")
        st.markdown("• 📚 **Learn from data.txt**")
    
    with footer_col2:
        st.markdown("### 🌟 **Capabilities**")
        st.markdown("• 🎭 Tell Jokes & Humor")
        st.markdown("• ❓ Answer Questions")
        st.markdown("• 💬 General Chat")
    
    with footer_col3:
        st.markdown("### 📱 **Deploy Anywhere**")
        st.markdown("• ☁️ Streamlit Cloud")
        st.markdown("• 🖥️ Local Hosting")
        st.markdown("• 🔄 Always Online")

# Run the app
if __name__ == "__main__":
    main()