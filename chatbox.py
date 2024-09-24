import os
import streamlit as st
from groq import Groq

# Access your secret file
with open('secret.txt') as f:
    key = f.read().strip()

# Initialize Groq client
groq_client = Groq(api_key=key)

# Set the model to 70B
MODEL = 'llama-3.1-70b-versatile'

# Initialize conversation history
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

def format_response(response, max_line_length=20):
    """Format the response into multiple lines without truncating."""
    words = response.split()

    # Create formatted response with lines of max_line_length words
    formatted_response = ''
    for i in range(0, len(words), max_line_length):
        line = ' '.join(words[i:i+max_line_length])
        formatted_response += line + '\n'

    return formatted_response.strip()

st.set_page_config(layout="wide")
st.title("ChatBot with Groq API")

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
.stTextInput>div>div>input {
    bottom: 0;
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
        user_input = st.text_input("Type your message...", key="user_input")
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

        # Format response with no truncation
        formatted_response = format_response(model_response)

        # Update conversation history with model response
        st.session_state.conversation_history.append({"role": "assistant", "content": formatted_response})

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
