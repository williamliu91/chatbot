import os
import streamlit as st
from groq import Groq
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
import base64

# Function to load the image and convert it to base64
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Path to the locally stored QR code image
qr_code_path = "qrcode.png"  # Ensure the image is in your app directory

# Convert image to base64
qr_code_base64 = get_base64_of_bin_file(qr_code_path)

# Custom CSS to position the QR code close to the top-right corner under the "Deploy" area
st.markdown(
    f"""
    <style>
    .qr-code {{
        position: fixed;  /* Keeps the QR code fixed in the viewport */
        top: 10px;       /* Sets the distance from the top of the viewport */
        right: 10px;     /* Sets the distance from the right of the viewport */
        width: 200px;    /* Adjusts the width of the QR code */
        z-index: 100;    /* Ensures the QR code stays above other elements */
    }}
    </style>
    <img src="data:image/png;base64,{qr_code_base64}" class="qr-code">
    """,
    unsafe_allow_html=True
)


# Download VADER lexicon
nltk.download('vader_lexicon', quiet=True)

# Access your secret file
with open('secret.txt') as f:
    key = f.read().strip()

# Initialize Groq client and sentiment analyzer
groq_client = Groq(api_key=key)
sia = SentimentIntensityAnalyzer()

# Set the model to 70B
MODEL = 'llama-3.1-70b-versatile'

def analyze_sentiment(text):
    """
    Analyze sentiment of text and return sentiment scores, category, and emoji.
    """
    sentiment = sia.polarity_scores(text)
    compound_score = sentiment['compound']
    
    # Determine sentiment category and corresponding emoji
    if compound_score >= 0.5:
        sentiment_category = "Very Positive"
        color = "green"
        emoji = "🤗"  # hugging face
    elif compound_score >= 0.05:
        sentiment_category = "Positive"
        color = "green"
        emoji = "😊"  # smiling face
    elif compound_score <= -0.5:
        sentiment_category = "Very Negative"
        color = "red"
        emoji = "😢"  # crying face
    elif compound_score <= -0.05:
        sentiment_category = "Negative"
        color = "red"
        emoji = "😕"  # slightly frowning face
    else:
        sentiment_category = "Neutral"
        color = "gray"
        emoji = "😐"  # neutral face
        
    return {
        'scores': sentiment,
        'category': sentiment_category,
        'color': color,
        'emoji': emoji
    }

def get_trend_emoji(avg_sentiment):
    """
    Get trend emoji based on average sentiment score.
    """
    if avg_sentiment >= 0.5:
        return "📈 Highly Positive Trend"
    elif avg_sentiment >= 0.05:
        return "↗️ Positive Trend"
    elif avg_sentiment <= -0.5:
        return "📉 Highly Negative Trend"
    elif avg_sentiment <= -0.05:
        return "↘️ Negative Trend"
    else:
        return "➡️ Neutral Trend"

def format_response(response, max_line_length=20):
    """Format the response into multiple lines without truncating."""
    words = response.split()
    formatted_response = ''
    for i in range(0, len(words), max_line_length):
        line = ' '.join(words[i:i+max_line_length])
        formatted_response += line + '\n'
    return formatted_response.strip()

# Initialize conversation history and sentiment history
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'sentiment_history' not in st.session_state:
    st.session_state.sentiment_history = []

st.title("Sentiment-Aware ChatBot 🤖")

# Enhanced CSS to include sentiment indicators
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
.sentiment-indicator {
    font-size: 0.9em;
    padding: 2px 6px;
    border-radius: 4px;
    margin-left: 10px;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}
.sentiment-emoji {
    font-size: 1.2em;
    margin-right: 4px;
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

# Sidebar with input and sentiment summary
with st.sidebar:
    st.header("Chat Input")
    
    # Add sentiment summary for the conversation
    if st.session_state.sentiment_history:
        total_sentiment = sum(s['scores']['compound'] for s in st.session_state.sentiment_history)
        avg_sentiment = total_sentiment / len(st.session_state.sentiment_history)
        
        st.markdown("### 📊 Conversation Sentiment")
        
        # Display average sentiment with emoji
        sentiment_color = "green" if avg_sentiment >= 0.05 else "red" if avg_sentiment <= -0.05 else "gray"
        st.markdown(f"<span style='color: {sentiment_color}; font-size: 1.1em;'>Average sentiment score: {avg_sentiment:.2f}</span>", 
                   unsafe_allow_html=True)
        
        # Display trend with emoji
        trend_text = get_trend_emoji(avg_sentiment)
        st.markdown(f"### {trend_text}")
        
        # Display sentiment distribution
        positive_count = sum(1 for s in st.session_state.sentiment_history if s['scores']['compound'] >= 0.05)
        negative_count = sum(1 for s in st.session_state.sentiment_history if s['scores']['compound'] <= -0.05)
        neutral_count = len(st.session_state.sentiment_history) - positive_count - negative_count
        
        st.markdown("### 📈 Sentiment Distribution")
        st.markdown(f"😊 Positive: {positive_count}")
        st.markdown(f"😐 Neutral: {neutral_count}")
        st.markdown(f"😕 Negative: {negative_count}")

    with st.form(key='message_form', clear_on_submit=True):
        user_input = st.text_input("Type your message...", key="user_input")
        submit_button = st.form_submit_button(label='Send 📤')

if submit_button and user_input:
    # Add user message to conversation history
    st.session_state.conversation_history.append({
        "role": "user",
        "content": user_input
    })

    try:
        # Get response from Groq
        chat_completion = groq_client.chat.completions.create(
            messages=st.session_state.conversation_history,
            model=MODEL
        )

        # Get and format the model response
        model_response = chat_completion.choices[0].message.content
        formatted_response = format_response(model_response)
        
        # Analyze sentiment of the response
        sentiment_analysis = analyze_sentiment(formatted_response)
        
        # Add bot message to conversation history
        st.session_state.conversation_history.append({
            "role": "assistant",
            "content": formatted_response
        })
        
        # Store sentiment separately
        st.session_state.sentiment_history.append(sentiment_analysis)

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

# Display conversation history with sentiment indicators
with chat_container:
    sentiment_index = 0
    for i, message in enumerate(st.session_state.conversation_history):
        if message['role'] == 'user':
            st.markdown(f'<div class="user-message">👤 You: {message["content"]}</div>',
                       unsafe_allow_html=True)
        else:
            sentiment = st.session_state.sentiment_history[sentiment_index]
            st.markdown(
                f'''<div class="bot-message">
                    🤖 ChatBot: {message["content"]}
                    <span class="sentiment-indicator" style="color: {sentiment['color']}">
                        <span class="sentiment-emoji">{sentiment['emoji']}</span>
                        {sentiment['category']} ({sentiment['scores']['compound']:.2f})
                    </span>
                </div>''',
                unsafe_allow_html=True
            )
            sentiment_index += 1

    # Add bottom spacing
    st.markdown("<div style='margin-bottom:70px'></div>", unsafe_allow_html=True)