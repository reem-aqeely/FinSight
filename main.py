from dotenv import load_dotenv
import os
import streamlit as st
from PIL import Image
import google.generativeai as genai


#  To load all the env varible  from .env
load_dotenv()


genai.configure(api_key=os.getenv('api_key'))

# To load gemini
model = genai.GenerativeModel('gemini-flash-latest')


def get_gemini_respose(input, image, prompt):
    respose = model.generate_content([input, image[0], prompt])
    return respose.text


def input_image_details(uploaded_file):  # يحول الصوره الى بايتات لفهم محتواها
    if uploaded_file is not None:
        # Read the file into bytes
        bytes_data = uploaded_file.getvalue()

        image_parts = [
            {
                "mime_type": uploaded_file.type,  # get th mime type of the uploaded_file
                "data": bytes_data
            }
        ]
        return image_parts
    else:
        raise FileNotFoundError("No file uploaded!")


# Initialize streamlit app
st.set_page_config(page_title="MultiLanguage Invoice Extractor")

st.header("MultiLanguage Invoice Extractor")
input = st.text_input("Input Promot: ", key="input")
uploaded_file = st.file_uploader(
    "Chose an image of the invoice : ", type=['jpg', 'jpeg', 'png'])
image = ""
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image. ", use_column_width=True)

submit = st.button("Tell me about the invoice ")

input_promt = """""You are an expert in understanding invoices. We will upload a  a imge as invoice
and you will gane to answer any questions vased on the uploaded invoice image """""

# If submit button is clicked
if submit:
    image_data = input_image_details(uploaded_file)
    response = get_gemini_respose(input_promt, image_data, input)
    st.subheader(" The response is: ")
    st.write(response)
