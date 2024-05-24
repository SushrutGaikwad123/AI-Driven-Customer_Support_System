import streamlit as st
from langchain.prompts import PromptTemplate
from langchain.llms import CTransformers
from pymongo import MongoClient
import hashlib

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")  # replace with your MongoDB connection string
db = client["Llama2"]
collection = db["responses"]

def get_hash(text):
    """Generate a hash for the input text."""
    return hashlib.sha256(text.encode()).hexdigest()

def check_in_db(input_text, no_words, blog_style):
    """Check if the input is already in the database."""
    query = {
        "hash": get_hash(f"{input_text}_{no_words}_{blog_style}")
    }
    return collection.find_one(query)

def save_to_db(input_text, no_words, blog_style, response):
    """Save the generated response to the database."""
    entry = {
        "hash": get_hash(f"{input_text}_{no_words}_{blog_style}"),
        "input_text": input_text,
        "no_words": no_words,
        "blog_style": blog_style,
        "response": response
    }
    collection.insert_one(entry)

def getLLamaresponse(input_text, no_words, blog_style):
    llm = CTransformers(model='models/llama-2-7b-chat.ggmlv3.q8_0.bin',
                        model_type='llama',
                        config={'max_new_tokens': 256, 'temperature': 0.01})
    # Prompt Template
    template = """
        Write a blog for {blog_style} job profile for a topic {input_text}
        within {no_words} words.
    """

    prompt = PromptTemplate(input_variables=["blog_style", "input_text", "no_words"],
                            template=template)

    # Generate the response from the LLama 2 model
    response = llm(prompt.format(blog_style=blog_style, input_text=input_text, no_words=no_words))
    return response

st.set_page_config(page_title="Generate content using Llama 2",
                   page_icon='🤖',
                   layout='centered',
                   initial_sidebar_state='collapsed')

st.header("Generate Content: Using Llama 2")

input_text = st.text_input("Input")

# Creating two more columns for additional 2 fields
col1, col2 = st.columns([7, 3])

with col1:
    no_words = st.selectbox('Word Limit',
                            ('50', '100', '150', '200'), index=0)

with col2:
    blog_style = st.radio('Select Domain',
                          ["Student", "Professional", "Common people", "Researchers", "Data Scientist"], index=0)

submit = st.button("Generate")

# Final response
if submit:
    existing_entry = check_in_db(input_text, no_words, blog_style)
    if existing_entry:
        response = existing_entry["response"]
        st.write("Fetched from database:")
    else:
        response = getLLamaresponse(input_text, no_words, blog_style)
        save_to_db(input_text, no_words, blog_style, response)
        st.write("Generated by model:")
    st.write(response)
