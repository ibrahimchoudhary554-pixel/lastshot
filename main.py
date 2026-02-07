import streamlit as st
import re
from datetime import datetime
import os

# Set page config - minimalist
st.set_page_config(
    page_title="Ibrahim's Assistant",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ===========================================
# BLACK & WHITE MINIMALIST STYLING
# ===========================================
st.markdown("""
<style>
    /* Remove all Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Black and white theme */
    .stApp {
        background-color: #000000;
        color: #ffffff;
    }
    
    /* Chat containers - minimalist */
    .stChatMessage {
        background-color: #111111;
        border: 1px solid #333333;
        border-radius: 2px;
        padding: 10px;
        margin: 5px 0;
    }
    
    /* User message */
    .stChatMessage[data-testid*="user"] {
        background-color: #1a1a1a;
        border-left: 3px solid #666666;
    }
    
    /* Assistant message */
    .stChatMessage[data-testid*="assistant"] {
        background-color: #0a0a0a;
        border-left: 3px solid #999999;
    }
    
    /* Chat input - minimalist */
    .stChatInput {
        border: 1px solid #333333;
        background-color: #111111;
        border-radius: 2px;
    }
    
    .stChatInput textarea {
        color: #ffffff;
        background-color: #111111;
    }
    
    /* Remove all decorations */
    .stButton > button {
        background-color: #222222;
        color: #ffffff;
        border: 1px solid #333333;
        border-radius: 2px;
        padding: 5px 10px;
    }
    
    .stButton > button:hover {
        background-color: #333333;
        border: 1px solid #444444;
    }
    
    /* Minimalist metrics */
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 1rem !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #999999 !important;
    }
    
    /* Headers - clean */
    h1, h2, h3 {
        color: #ffffff !important;
        font-weight: 300;
        letter-spacing: -0.5px;
    }
    
    /* Divider */
    hr {
        border: 0.5px solid #333333;
        margin: 20px 0;
    }
    
    /* Code blocks */
    .stCodeBlock {
        background-color: #111111;
        border: 1px solid #333333;
    }
</style>
""", unsafe_allow_html=True)

# ===========================================
# KNOWLEDGE BASE SYSTEM
# ===========================================
class KnowledgeBase:
    def __init__(self):
        self.qa_pairs = []
        self.fallback_responses = [
            "I don't have information about that in my knowledge base.",
            "That topic is not covered in my current data.",
            "I need more information about that topic.",
            "Please consult the documentation for that information.",
            "I cannot answer that question with my current knowledge."
        ]
        self.load_data()
    
    def load_data(self):
        """Load data from data.txt - strict format: Question: Answer"""
        try:
            with open('data.txt', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse Q&A pairs with strict format
            lines = content.split('\n')
            current_question = None
            current_answer = []
            
            for line in lines:
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    continue
                
                # Check if line starts a new Q&A (ends with colon or question mark)
                if line.endswith(':') or line.endswith('?'):
                    # Save previous Q&A if exists
                    if current_question and current_answer:
                        self.qa_pairs.append({
                            'question': current_question.strip(':?'),
                            'answer': ' '.join(current_answer).strip()
                        })
                    
                    # Start new Q&A
                    current_question = line
                    current_answer = []
                elif current_question:
                    # This is part of the answer
                    current_answer.append(line)
            
            # Save the last Q&A
            if current_question and current_answer:
                self.qa_pairs.append({
                    'question': current_question.strip(':?'),
                    'answer': ' '.join(current_answer).strip()
                })
            
            # Log loaded data
            print(f"Loaded {len(self.qa_pairs)} Q&A pairs from data.txt")
            
        except FileNotFoundError:
            print("data.txt not found. Creating sample data.")
            self.create_sample_data()
        except Exception as e:
            print(f"Error loading data.txt: {e}")
            self.create_sample_data()
    
    def create_sample_data(self):
        """Create sample data.txt if it doesn't exist"""
        sample_data = """Project Information:
This is Ibrahim's project assistant.
The assistant only answers questions based on the data.txt file.
All responses come strictly from the knowledge base.

How to use:
Ask questions about the topics covered in data.txt.
The assistant will provide factual responses based on available information.

Contact Information:
For questions not covered here, contact the administrator directly.

System Status:
The system is operational.
All responses are generated from the knowledge base.
No external data sources are used.

Data Format:
Questions should be followed by answers.
Each new Q&A starts with a line ending in colon or question mark."""
        
        with open('data.txt', 'w', encoding='utf-8') as f:
            f.write(sample_data)
        
        # Reload
        self.load_data()
    
    def find_answer(self, user_input):
        """Find the best matching answer for user input"""
        user_input_lower = user_input.lower().strip()
        
        # Remove punctuation for better matching
        user_words = set(re.findall(r'\w+', user_input_lower))
        
        best_match = None
        best_score = 0
        
        for qa in self.qa_pairs:
            question_lower = qa['question'].lower()
            
            # Exact phrase match
            if user_input_lower in question_lower or question_lower in user_input_lower:
                return qa['answer']
            
            # Keyword matching
            question_words = set(re.findall(r'\w+', question_lower))
            common_words = user_words.intersection(question_words)
            
            if common_words:
                # Calculate match score
                score = len(common_words) / max(len(question_words), 1)
                
                # Boost score if question starts with user input
                if question_lower.startswith(user_input_lower):
                    score += 0.5
                
                if score > best_score:
                    best_score = score
                    best_match = qa
        
        # Return best match if score is good enough
        if best_match and best_score > 0.3:
            return best_match['answer']
        
        # No match found
        return None

# ===========================================
# CHATBOT LOGIC
# ===========================================
class Assistant:
    def __init__(self):
        self.knowledge_base = KnowledgeBase()
        self.conversation_log = []
    
    def get_response(self, user_input):
        """Get response based on knowledge base"""
        # Clean input
        user_input = user_input.strip()
        
        # Check for greetings
        if user_input.lower() in ['hi', 'hello', 'hey', 'greetings']:
            return "Hello. I am the assistant. How can I help you?"
        
        # Check for farewells
        if user_input.lower() in ['bye', 'goodbye', 'exit', 'quit']:
            return "Goodbye. Contact me if you need further assistance."
        
        # Check for help
        if user_input.lower() in ['help', 'what can you do', '?']:
            return "I answer questions based on the knowledge base in data.txt. Ask me about topics covered there."
        
        # Search for answer in knowledge base
        answer = self.knowledge_base.find_answer(user_input)
        
        if answer:
            return answer
        
        # No answer found
        return "I don't have information about that in the knowledge base. Please ask about topics covered in data.txt."

# ===========================================
# STREAMLIT APP
# ===========================================
def main():
    # Initialize session state
    if 'assistant' not in st.session_state:
        st.session_state.assistant = Assistant()
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'message_count' not in st.session_state:
        st.session_state.message_count = 0
    
    # Title
    st.markdown("<h1 style='text-align: center; font-weight: 300;'>Hi! It's Ibrahim's Assistant</h1>", unsafe_allow_html=True)
    st.markdown("<div style='text-align: center; color: #999999; margin-bottom: 30px;'>Knowledge-based assistant | Data-driven responses</div>", unsafe_allow_html=True)
    
    # Display conversation
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask a question..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.message_count += 1
        
        # Get response
        with st.spinner(""):
            response = st.session_state.assistant.get_response(prompt)
        
        # Add assistant response
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Rerun to update
        st.rerun()
    
    # Minimal stats at bottom
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption(f"Messages: {st.session_state.message_count}")
    with col2:
        st.caption(f"Knowledge base: {len(st.session_state.assistant.knowledge_base.qa_pairs)} entries")
    with col3:
        st.caption("Status: Operational")

# Run the app
if __name__ == "__main__":
    main()
