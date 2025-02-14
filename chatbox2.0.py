import os
import re
import streamlit as st
from groq import Groq

# Access your secret file
with open('secret.txt') as f:
    key = f.read().strip()

# Initialize Groq client
groq_client = Groq(api_key=key)

# Set the model to 70B
MODEL = 'llama-3.3-70b-versatile'

# Initialize conversation history
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

def format_response(response):
    """Format the response and style section headers."""
    # Use regex to find and style section headers
    response = re.sub(r'\*\*(.*?)\*\*', r'<span style="color:black; font-weight:bold;">\1</span>', response)  # Section headers in red
    # Add space before the first section header
    response = re.sub(r'(<span style="color:black; font-weight:bold;">.*?</span>)', r'<br/>\1', response, count=1)
    return response

def save_to_file(title, content, filename='output.html'):
    """Save the title and formatted content to an HTML file."""
    with open(filename, 'w') as file:
      
        file.write(content)
       

st.set_page_config(layout="wide")
st.title("ArticleMaster: Your AI Writing Assistant")

# Custom CSS to improve chat appearance
st.markdown("""
<style>
.user-message {
    background-color: #DCF8C6;
    padding: 10px;
    border-radius: 10px;
    margin-bottom: 10px;
}
.bot-message {
    background-color: #E0E0E0;
    padding: 10px;
    border-radius: 10px;
    margin-bottom: 10px;
}
.stTextArea>div>textarea {
    height: 150px !important; /* Increase the height of the input box */
}
.stApp {
    padding-bottom: 0 !important;
}
</style>
""", unsafe_allow_html=True)

# Chat display area
chat_container = st.container()

# Input area in the sidebar
with st.sidebar:
    st.header("Chat Input")

    with st.form(key='message_form', clear_on_submit=True):
        user_input = st.text_area("Type your message...", key="user_input")  # Changed to text_area for larger input
        submit_button = st.form_submit_button(label='Send')

if submit_button and user_input:
    # Update conversation history with user input
    st.session_state.conversation_history.append({"role": "user", "content": user_input})

    # Generate response using Groq model
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=st.session_state.conversation_history,
            model=MODEL
        )

        # Get the model response
        model_response = chat_completion.choices[0].message.content
        
        # Split the response into lines
        lines = model_response.splitlines()
        
        # Assume the first line is the title
        title_candidate = lines[0].strip()
        
        # Remove any asterisks from the title_candidate
        title_candidate = title_candidate.replace('**', '').strip()

        title_html = f'<h3 style="color:black;">{title_candidate}</h3>'
        
        # Combine the rest of the lines as the formatted response
        formatted_response = format_response("\n".join(lines[1:]))

        # Save the title and formatted response to an HTML file
        save_to_file(title_candidate, formatted_response)

        # Update conversation history with model response including title
        st.session_state.conversation_history.append({"role": "assistant", "content": title_html + formatted_response})

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

# Display conversation history in the chat container
with chat_container:
    for message in st.session_state.conversation_history:
        if message['role'] == 'user':
            st.markdown(f'<div class="user-message">You: {message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="bot-message">ChatBot: {message["content"]}</div>', unsafe_allow_html=True)

    # Add some space at the bottom to prevent overlap with input box
    st.markdown("<div style='margin-bottom:70px'></div>", unsafe_allow_html=True)
