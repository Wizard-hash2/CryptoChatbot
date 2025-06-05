import streamlit as st
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from pycoingecko import CoinGeckoAPI
import random

# Initialize CoinGecko API with free endpoint
cg = CoinGeckoAPI()

# Download NLTK data safely
@st.cache_resource
def setup_nltk():
    """Setup NLTK resources."""
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', quiet=True)

setup_nltk()
stop_words = set(stopwords.words('english'))

# Greeting and conversation patterns
greetings = {
    'hello': ['Hello!', 'Hi there!', 'Hey!', 'Greetings!'],
    'hi': ['Hi!', 'Hello!', 'Hey there!', 'Welcome!'],
    'hey': ['Hey!', 'Hi!', 'Hello there!', 'Greetings!'],
    'greetings': ['Greetings!', 'Hello!', 'Welcome!', 'Hi there!']
}

capabilities = """
I'm your Crypto Information Assistant, created by Ngenoh! 🚀

I can help you with:
1. Real-time Cryptocurrency Data:
   - Current prices
   - Market capitalization
   - 24-hour price changes
   - Latest market updates

2. Sustainability Information:
   - Energy usage ratings
   - Sustainability scores
   - Environmental impact

3. Latest News:
   - Recent developments
   - Market updates
   - Project news

4. Supported Cryptocurrencies:
   - Bitcoin (BTC)
   - Ethereum (ETH)
   - Cardano (ADA)

Just ask me anything about these topics! For example:
- "What's Bitcoin's current price?"
- "Tell me about Ethereum's sustainability"
- "Show me Cardano's market cap and news"

Message sent by Ngenoh - Your Crypto Guide 🌟
"""

# Static sustainability and energy data (not available in API)
sustainability_data = {
    "bitcoin": {
        "energy_use": "high",
        "sustainability_score": 3/10,
    },
    "ethereum": {
        "energy_use": "medium",
        "sustainability_score": 6/10,
    },
    "cardano": {
        "energy_use": "low",
        "sustainability_score": 8/10,
    }
}

def is_greeting(text):
    """Check if the input is a greeting."""
    text = text.lower().strip()
    return (
        text in greetings or
        text.startswith('hi ') or
        text.startswith('hello ') or
        text.startswith('hey ')
    )

def get_greeting_response():
    """Generate a random greeting response."""
    all_greetings = []
    for responses in greetings.values():
        all_greetings.extend(responses)
    return random.choice(all_greetings)

@st.cache_data(ttl=60)  # Cache for 60 seconds
def get_crypto_data(crypto_id):
    """Get real-time data from CoinGecko API with caching."""
    try:
        data = cg.get_coin_by_id(
            crypto_id,
            localization=False,
            tickers=False,
            market_data=True,
            community_data=False,
            developer_data=False,
            sparkline=False
        )
        
        market_data = data.get('market_data', {})
        return {
            'current_price': market_data.get('current_price', {}).get('usd'),
            'market_cap': market_data.get('market_cap', {}).get('usd'),
            'price_change_24h': market_data.get('price_change_percentage_24h'),
            'last_updated': market_data.get('last_updated'),
        }
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return None

def get_crypto_news(crypto_id):
    """Get latest news for a cryptocurrency."""
    try:
        news = cg.get_coin_by_id(
            crypto_id,
            localization=False,
            tickers=False,
            market_data=False,
            community_data=False,
            developer_data=False,
            sparkline=False
        )
        return news.get('description', {}).get('en', '')[:200] + "..."
    except Exception:  # Removed unused 'e' variable
        return "News data unavailable"

def preprocess_text(text):
    """Preprocess the input text for better understanding."""
    # Tokenize and convert to lowercase
    tokens = word_tokenize(text.lower())
    
    # Remove punctuation and stopwords
    tokens = [token for token in tokens if token.isalnum()]
    tokens = [token for token in tokens if token not in stop_words]
    
    return tokens

def analyze_crypto_query(user_question):
    """Analyze user question and provide response with real-time data."""
    # Check for special commands
    user_question = user_question.lower().strip()
    
    # Handle greetings
    if is_greeting(user_question):
        greeting = get_greeting_response()
        return f"{greeting}\n\n{capabilities}"
    
    # Handle help request
    if user_question in ['help', 'what can you do', 'capabilities']:
        return capabilities
    
    tokens = preprocess_text(user_question)
    response = ""
    
    # Define keyword mappings
    keywords = {
        'price': ['price', 'cost', 'worth', 'value'],
        'market': ['market', 'cap', 'capitalization'],
        'change': ['change', 'changed', 'movement', '24h', 'hours'],
        'energy': ['energy', 'power', 'consumption'],
        'green': ['sustainable', 'green', 'environment'],
        'news': ['news', 'update', 'latest', 'happening']
    }
    
    # Map crypto names to CoinGecko IDs
    crypto_mapping = {
        'bitcoin': 'bitcoin',
        'btc': 'bitcoin',
        'ethereum': 'ethereum',
        'eth': 'ethereum',
        'cardano': 'cardano',
        'ada': 'cardano'
    }
    
    # Identify mentioned cryptocurrencies
    cryptos_to_show = []
    for token in tokens:
        if token in crypto_mapping:
            cryptos_to_show.append(crypto_mapping[token])
    
    if not cryptos_to_show:
        cryptos_to_show = ['bitcoin', 'ethereum', 'cardano']
    
    # Determine what information to show
    show_price = any(word in tokens for word in keywords['price'])
    show_market = any(word in tokens for word in keywords['market'])
    show_change = any(word in tokens for word in keywords['change'])
    show_energy = any(word in tokens for word in keywords['energy'])
    show_green = any(word in tokens for word in keywords['green'])
    show_news = any(word in tokens for word in keywords['news'])
    
    show_all = not any([
        show_price, show_market, show_change,
        show_energy, show_green, show_news
    ])
    
    # Generate response
    for crypto_id in cryptos_to_show:
        response += f"\n{crypto_id.title()}:\n"
        
        # Get real-time data
        market_data = get_crypto_data(crypto_id)
        
        if market_data:
            if show_all or show_price:
                price = market_data['current_price']
                response += f"Current Price: ${price:,.2f}\n"
            
            if show_all or show_market:
                cap = market_data['market_cap']
                response += f"Market Cap: ${cap:,.0f}\n"
            
            if show_all or show_change:
                change = market_data['price_change_24h']
                response += f"24h Change: {change:.1f}%\n"
            
            if show_all or show_energy:
                energy = sustainability_data[crypto_id]['energy_use']
                response += f"Energy Usage: {energy}\n"
            
            if show_all or show_green:
                sustain = sustainability_data[crypto_id]['sustainability_score']
                score = int(sustain * 100)
                response += f"Sustainability Score: {score}/100\n"
            
            if show_all or show_news:
                news = get_crypto_news(crypto_id)
                response += f"Latest News: {news}\n"
            
            response += f"Last Updated: {market_data['last_updated']}\n"
        else:
            response += "Error fetching real-time data\n"
    
    if not response.strip():
        response = capabilities
    
    # Add signature to all responses
    response += "\n\nMessage sent by Ngenoh - Your Crypto Guide 🌟"
    return response

# Streamlit UI
st.title("🤖 Crypto Information Bot by Ngenoh")
st.write("Ask me anything about Bitcoin, Ethereum, or Cardano!")

# Add a note about data sources
st.sidebar.markdown("""
## Data Sources
- Real-time market data: CoinGecko API
- Sustainability scores: Static database
- Energy usage: Static database

Created with ❤️ by Ngenoh
""")

# Initialize session state for chat history
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What would you like to know?"):
    # Display user message
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        # Generate response
        response = analyze_crypto_query(prompt)
        
        # Display response
        st.markdown(response)
        st.session_state.messages.append(
            {"role": "assistant", "content": response}
        ) 