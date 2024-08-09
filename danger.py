import streamlit as st
import os
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
from gtts import gTTS
from streamlit_option_menu import option_menu

st.title("My Library")
st.divider()

with st.sidebar:
    navigate = option_menu(
        menu_title="Sections",
        options=["Upload Files", "Gallery"]
    )

# pdf's content
def read_pdf(file_path):
    pdf = PdfReader(file_path)
    return pdf

# convert pages to images for user
def display_pdf(file_path, page_number, poppler_path=None):
    images = convert_from_path(file_path, first_page=page_number, last_page=page_number, poppler_path=poppler_path)
    if images:
        image = images[0]
        st.image(image, caption=f"Page {page_number}")

# extract text from a specific page
def extract_text(pdf, page_number):
    page = pdf.pages[page_number - 1]
    text = page.extract_text()
    return text

# store uploaded files (for later use)
def save_uploaded_files(uploaded_files):
    file_paths = {}
    for uploaded_file in uploaded_files:
        file_content = uploaded_file.read()
        temp_file_path = f"./tempf/{uploaded_file.name}"
        os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)

        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(file_content)

        file_paths[uploaded_file.name] = temp_file_path
    return file_paths

# tts function
def convert_text_to_audio(pdf, file_name, page_number):
    audio_file_path = f"./tempf/{file_name}_page_{page_number}.mp3"

    if os.path.exists(audio_file_path):
        # Load existing audio file
        audio_file = open(audio_file_path, "rb")
        audio_bytes = audio_file.read()
        return audio_bytes
    else:
        # Create a new audio file if there wasn't any saved files
        text = extract_text(pdf, page_number)
        if text:
            tts = gTTS(text)
            tts.save(audio_file_path)

            audio_file = open(audio_file_path, "rb")
            audio_bytes = audio_file.read()
            return audio_bytes
        else:
            st.write("No text found on this page.")
            return None

# Check if 'tempf' folder exists and load existing PDFs
def load_existing_files():
    existing_files = {}
    if os.path.exists("./tempf"):
        for file_name in os.listdir("./tempf"):
            if file_name.endswith(".pdf"):
                existing_files[file_name] = f"./tempf/{file_name}"
    return existing_files

# main section
def run_app(selected_file_paths):
    # allow user to select which file to display
    selected_file_name = st.selectbox("Select a file to display", list(selected_file_paths.keys()))

    if selected_file_name:
        # read and display the selected file
        pdf = read_pdf(selected_file_paths[selected_file_name])
        num_pages = len(pdf.pages)

        # Initialize session state for page number if not already done
        if f"page_number_{selected_file_name}" not in st.session_state:
            st.session_state[f"page_number_{selected_file_name}"] = 1

        # Use session state for page number
        page_number = st.session_state[f"page_number_{selected_file_name}"]

        # buttons
        col1, col2, col3, col4, col5 = st.columns([1, 2, 1, 2, 1])

        with col1:
            if st.button("⬅️", key="prev"):
                if page_number > 1:
                    st.session_state[f"page_number_{selected_file_name}"] -= 1

        with col2:
            st.empty()

        with col3:
            if st.button("Listen"):
                audio_bytes = convert_text_to_audio(pdf, selected_file_name, st.session_state[f"page_number_{selected_file_name}"])
                if audio_bytes:
                    st.session_state["audio_bytes"] = audio_bytes

        with col4:
            st.empty()

        with col5:
            if st.button("➡️", key="next"):
                if page_number < num_pages:
                    st.session_state[f"page_number_{selected_file_name}"] += 1

        # Display audio file if available
        if "audio_bytes" in st.session_state:
            st.audio(st.session_state["audio_bytes"], format="audio/mp3")

        # Update the page display
        display_pdf(selected_file_paths[selected_file_name], st.session_state[f"page_number_{selected_file_name}"])

# store existing files on app startup
selected_file_paths = load_existing_files()

if navigate == "Upload Files":
    # upload PDF files (user)
    selected_files = st.file_uploader("Upload PDF files", type=["pdf"], accept_multiple_files=True)
    if selected_files:
        # add files to the existing paths
        new_file_paths = save_uploaded_files(selected_files)
        selected_file_paths.update(new_file_paths)
        st.success("Files have been uploaded successfully!")

if navigate == "Gallery":
    if selected_file_paths:
        run_app(selected_file_paths)
    else:
        st.write("No PDF files found in the library. Please upload files in the 'Upload Files' section.")
