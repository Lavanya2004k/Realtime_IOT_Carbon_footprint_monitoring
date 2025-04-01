import streamlit as st
import pandas as pd
from datetime import datetime
import json
from kafka import KafkaConsumer
from web3 import Web3
from textblob import TextBlob

st.set_page_config(page_title="ESG & Blockchain Dashboard", layout="wide")

consumer = KafkaConsumer(
    'carbonfootprint',
    bootstrap_servers=['localhost:9092'],
    value_deserializer=lambda v: json.loads(v.decode('utf-8')),
    auto_offset_reset='earliest',
    enable_auto_commit=True
)

web3 = Web3(Web3.HTTPProvider("https://rpc.ankr.com/bsc/48b208604a24d6b44887751595a5f16a82814b1aecdb818edfd89f7a12da96b8"))
with open("CarbonCreditTokenABI.json") as f:
    CONTRACT_ABI = json.load(f)
CONTRACT_ADDRESS = "0x1a4c3b6c7a08c0989Ff780514568ed85786aa659"
WALLET_ADDRESS = "0x1a4c3b6c7a08c0989Ff780514568ed85786aa659"

def sentiment_analysis(text):
    return TextBlob(text).sentiment.polarity

def generate_suggestions(env_score, soc_score, gov_score):
    sentiment = sentiment_analysis(f"E:{env_score}, S:{soc_score}, G:{gov_score}")
    if sentiment > 0.5:
        return "Strong scores! Maintain transparency and adopt cleaner solutions."
    elif 0 <= sentiment <= 0.5:
        return "Moderate scores. Focus on governance and social policies."
    else:
        return "Low scores. Prioritize emissions and ethical practices."

def get_wallet_balance():
    try:
        balance = web3.eth.get_balance(WALLET_ADDRESS)
        return web3.from_wei(balance, 'ether')
    except Exception as e:
        st.error(f"Blockchain error: {e}")
        return 0

def consume_data():
    data_list = []
    for message in consumer:
        data = message.value
        data_list.append(data)
        if len(data_list) >= 20:
            break
    return data_list

st.title("🌍 ESG & Blockchain Dashboard")

st.subheader("📈 Data Streaming")
if st.button("Start Consuming"):
    data_store = consume_data()
    df = pd.DataFrame(data_store)
    st.success("Data Consumption Completed!")

    st.write("### Recent ESG & Environmental Data")
    st.dataframe(df.tail(10))

    st.line_chart(df[['timestamp', 'aqi']].set_index('timestamp'))
    st.line_chart(df[['timestamp', 'CO2_ppm', 'NO2_ppm', 'SO2_ppm']].set_index('timestamp'))
    st.line_chart(df[['timestamp', 'Temperature_C', 'Humidity_%']].set_index('timestamp'))

    avg_env = df['environmental_score'].mean()
    avg_soc = df['social_score'].mean()
    avg_gov = df['governance_score'].mean()
    suggestions = generate_suggestions(avg_env, avg_soc, avg_gov)
    st.subheader("📊 ESG Suggestions")
    st.write(suggestions)

    balance = get_wallet_balance()
    st.subheader("💰 Wallet Balance")
    st.metric("Wallet Balance (ETH)", f"{balance:.4f}")
    st.markdown("[Invest](https://portfolio.metamask.io/)")
    st.markdown(f"[Tracking carbon credits](https://bscscan.com/address/{WALLET_ADDRESS})")
