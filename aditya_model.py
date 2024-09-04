from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
import streamlit as st
import os
import google.generativeai as genai
from PIL import Image
import io
import tempfile  # For handling temporary files

# Load environment variables
load_dotenv() 

# Configure Google Gemini API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to load Google Gemini Pro Vision API And get response
def get_gemini_response(input, image, prompt):
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content([input, image[0], prompt])
    return response.text

# Function to handle image input and prepare it for the API
def input_image_setup(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        image_parts = [
            {
                "mime_type": uploaded_file.type,
                "data": bytes_data
            }
        ]
        return image_parts
    else:
        raise FileNotFoundError("No file uploaded")

# Function to generate PDF report with colors and better structure
def generate_pdf_report(response_text, image=None, file_name="health_report.pdf"):
    buffer = io.BytesIO()  # Create an in-memory buffer
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setFont("Helvetica", 12)

    # Add title with color and larger font
    pdf.setFillColor(colors.darkblue)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, 770, "Health Analysis Report")

    pdf.setFont("Helvetica", 12)
    pdf.setFillColor(colors.black)

    # Insert the uploaded image into the PDF
    if image is not None:
        # Save image to a temporary file and use it in drawImage()
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_img:
            image.save(temp_img.name)
            pdf.drawImage(temp_img.name, 50, 600, width=2 * inch, height=2 * inch)

    # Split the response text into lines for proper formatting
    lines = response_text.split('\n')
    
    # Header formatting with bold and color
    pdf.setFont("Helvetica-Bold", 12)
    pdf.setFillColor(colors.green)
    pdf.drawString(40, 550, "Analysis Findings:")

    # Move down the page for text content
    text_y_position = 530
    pdf.setFont("Helvetica", 12)
    pdf.setFillColor(colors.black)

    # Loop through the lines and add them to the PDF, adjusting the line height
    for line in lines:
        if text_y_position <= 100:  # If we reach the bottom of the page, add a new page
            pdf.showPage()
            text_y_position = 750
        pdf.drawString(40, text_y_position, line)
        text_y_position -= 20

    # Adding footer with disclaimer
    pdf.setFillColor(colors.red)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(40, 50, "Consult with a Doctor before making any decisions.")

    pdf.showPage()
    pdf.save()
    
    buffer.seek(0)  # Reset the buffer's file pointer
    return buffer

# Initialize our Streamlit app
st.set_page_config(page_title="Gemini Health App")
st.header("Visual Health Report: Possible Conditions from Your Image")

# Input fields
input = st.text_input("Input Prompt: ", key="input")
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

# Show uploaded image
image = None
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image of your problem", use_column_width=True)

# Default input prompt for the model
input_prompt = """You are a medical practitioner and an expert in analyzing medical-related images working for a very reputed hospital you also have good knowledge about cancer identification. You will be provided with images and you need to identify the anomalies, any disease or health issues. You need to generate the result in a detailed manner. Write all the findings, next steps, recommendations, etc. You only need to respond if the image is related to a human body and health issues. You must have to answer but also write a disclaimer saying that "Consult with a Doctor before making any decisions".
 
Remember, if certain aspects are not clear from the image, it's okay to state 'Unable to determine based on the provided image.'

Now analyze the image and answer the above questions in the same structured manner defined above. Generate a detailed report. The report should include: 1. The type of diseases (if applicable). 2. Precautions to take for this type of disease. 3. Basic medications or treatments that might be recommended. Please provide a comprehensive and informative response."""

# Submit button
submit = st.button("Analyze Image")

# If submit button is clicked
if submit and uploaded_file is not None:
    image_data = input_image_setup(uploaded_file)
    response = get_gemini_response(input_prompt, image_data, input)
    
    # Show response in the app
    st.subheader("Here is your Your Possible Diagnosis:")
    st.write(response)

    # Generate and download the improved PDF report
    buffer = generate_pdf_report(response, image)
    
    st.download_button(
        label="Download PDF Report",
        data=buffer,
        file_name="health_report.pdf",
        mime="application/pdf"
    )
