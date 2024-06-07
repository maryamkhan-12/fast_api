import streamlit as st
import requests
st.title("Resume Parser")

uploaded_file = st.file_uploader("Upload a resume", type=["pdf", "docx", "txt"])

if uploaded_file is not None:
    with st.spinner("Processing..."):
        # Send the file to the FastAPI backend
        files = {"file": uploaded_file.getvalue()}
        response = requests.post("http://127.0.0.1:8000/main.py/", files={"file": uploaded_file})
        
        if response.status_code == 200:
            extracted_info = response.json()
            st.success("Resume processed successfully!")
            st.json(extracted_info)
        else:
            st.error(f"Error: {response.status_code}")
            st.error(response.json()["detail"])
