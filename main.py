from dotenv import load_dotenv
import os
import streamlit as st
import pandas as pd
from PIL import Image
import google.generativeai as genai
import json
from Database import Database


st.set_page_config(page_title="FinSight ",  page_icon=":money:", layout="wide")

#  To load all the env varible  from .env
load_dotenv()

api_key = os.getenv('api_key')
if not api_key:
    st.error("API key not found")
    st.stop()

genai.configure(api_key=api_key)

# To load gemini
model = genai.GenerativeModel('gemini-flash-latest')

# Helper Functions


def get_gemini_respose(prompt, image_parts):
    respose = model.generate_content([prompt, image_parts[0]])
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


st.sidebar.title("FinSight 📊")
choice = st.sidebar.radio("Menu:", ["Upload Invoice 🧾", "Dashboard 📈"])


# --- Page 1: Upload ---
if choice == "Upload Invoice 🧾":
    st.title("Upload New Invoice 📸")

    input_prompt = """
      You are an expert financial accountant. 
      Analyze the uploaded invoice image and extract data into strict JSON format.

     Required Fields:
     1. "store_name": string.
     2. "date": YYYY-MM-DD.
     3. "total_amount": float (remove currency symbols).
     4. "category": ONE of [Food, Transport, Shopping, Bills, Health, Education, Other].
     5. "items": A LIST of objects. Each object MUST have these keys:
     - "name": string (item name)
     - "quantity": int (default 1 if not clear)
     - "price": float (price PER ITEM, default 0 if not clear)

     Example JSON Output:
     {
      "store_name": "Lulu Hypermarket",
      "date": "2023-10-25",
      "total_amount": 150.00,
      "category": "Food",
      "items": [
      {"name": "Milk", "quantity": 2, "price": 10.0}, 
      {"name": "Bread", "quantity": 1, "price": 5.0}
       ]
     }
     IMPORTANT: Return ONLY raw JSON. No Markdown.
     """

    uploaded_file = st.file_uploader(
        "Chose an image of the invoice : ", type=['jpg', 'jpeg', 'png'])
    image = ""
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image. ", width=400)

        if st.button("Analyze & Save Data💾"):
            with st.spinner(" Analyzing invoice...⏳"):

                try:
                    image_data = input_image_details(uploaded_file)
                    response = get_gemini_respose(input_prompt, image_data)

                    cleaned_text = response.replace(
                        "```json", "").replace("```", "").strip()
                    data = json.loads(cleaned_text)

                    db = Database()
                    db.insert_invoice(
                        data['store_name'],
                        data['date'],
                        data['total_amount'],
                        data['category'],
                        data['items']

                    )

                    if saved:
                        st.success("Invoice analyzed successfully!")
                        st.json(data)

                    else:
                        st.error("Failed to save to database please try agine.")

                except Exception as e:
                    st.error(f"Error analyzing invoice: {e}")

elif choice == "Dashboard 📈":
    st.title("Expenses Analysis 📊")

    db = Database()
    # نجلب البيانات باستخدام الدالة الجديدة التي تدمج المنتجات
    data = db.fetch_all_invoices()

    if data:

        df = pd.DataFrame(
            data, columns=['ID', 'Store', 'Date', 'Amount', 'Category', 'Items'])

        # 2. عرض  (Metrics)
        total_spent = df['Amount'].sum()
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Spent 💸", f"{total_spent} SAR")
        col2.metric("Total Invoices 🧾", len(df))

        # حساب أكثر فئة تكراراً
        top_category = df['Category'].mode()[0] if not df.empty else "N/A"
        col3.metric("Top Category 🔥", top_category)

        st.markdown("---")  # خط فاصل

        # 3. الرسم البياني (Bar Chart)
        st.subheader("Expenses by Category")
        chart_data = df.groupby("Category")["Amount"].sum()
        st.bar_chart(chart_data)

        # 4. الجدول التفصيلي
        with st.expander("View Detailed History 📝"):
            # نخفي الـ ID ونعرض الباقي
            st.dataframe(df.drop(columns=['ID']), use_container_width=True)

    else:
        st.info(
            "No data available yet. Go to 'Upload Invoice' to add your first receipt! 🚀")
