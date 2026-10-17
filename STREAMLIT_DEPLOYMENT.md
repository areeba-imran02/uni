# Streamlit Community Cloud quick deployment

1. Extract `UniVerse_AI_Streamlit.zip`.
2. Upload the extracted project **files** to a GitHub repository.
3. Open https://share.streamlit.io/ → Create app.
4. Select your repo/branch and set Main file path to `app.py`.
5. Click Deploy.
6. For persistent user/project data, configure a managed PostgreSQL URL in app Secrets before public use. Do not commit credentials.

The Streamlit app uses the existing deterministic Python workflow engine directly. It does not need the React frontend or a separate FastAPI server to run the Streamlit UI. The original React/FastAPI implementation is preserved in the project.
