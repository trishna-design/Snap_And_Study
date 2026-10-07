import streamlit as st
from google import genai
from google.genai import types
from prompts import SYSTEM_PROMPT

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# --------------------------------------------------
# Page Settings
# --------------------------------------------------

st.set_page_config(
    page_title="Snap & Study",
    page_icon="📚"
)

st.title("📚 Snap & Study")
st.write("Your AI-powered study assistant")


# --------------------------------------------------
# Connect to Gemini
# --------------------------------------------------

client = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"]
)


# --------------------------------------------------
# Upload Study Image
# --------------------------------------------------

uploaded_image = st.file_uploader(
    "📸 Upload your study image",
    type=["jpg", "jpeg", "png"]
)


if uploaded_image:

    # Display uploaded image
    st.image(
        uploaded_image,
        caption="Your uploaded study material"
    )

    # Convert image into bytes
    image_bytes = uploaded_image.getvalue()


    # --------------------------------------------------
    # AI Explanation
    # --------------------------------------------------

    st.subheader("🤖 AI Explanation")

    try:

        response = client.models.generate_content(
            model="gemini-3.5-flash",

            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=uploaded_image.type
                ),

                (
                    "Analyze this study material and explain it "
                    "for a student. Identify the main topic and "
                    "give the important points."
                )
            ],

            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT
            )
        )

        explanation = response.text

        st.write(explanation)


        # --------------------------------------------------
        # Email Section
        # --------------------------------------------------

        st.subheader("📧 Send Explanation to Email")

        receiver_email = st.text_input(
            "Enter the email address to receive the explanation"
        )


        if st.button("📨 Send Email"):

            if receiver_email:

                try:

                    message = MIMEMultipart()

                    message["From"] = st.secrets[
                        "GMAIL_ADDRESS"
                    ]

                    message["To"] = receiver_email

                    message["Subject"] = (
                        "Snap & Study - AI Explanation"
                    )


                    email_body = f"""
Hello,

Here is your Snap & Study AI explanation:

{explanation}

Best regards,
Snap & Study
"""


                    message.attach(
                        MIMEText(
                            email_body,
                            "plain"
                        )
                    )


                    # Connect to Gmail
                    with smtplib.SMTP_SSL(
                        "smtp.gmail.com",
                        465
                    ) as server:

                        server.login(
                            st.secrets["GMAIL_ADDRESS"],
                            st.secrets["GMAIL_APP_PASSWORD"]
                        )

                        server.send_message(
                            message
                        )


                    st.success(
                        "✅ Explanation sent successfully!"
                    )


                except Exception:

                    st.error(
                        "❌ Unable to send the email. "
                        "Please check your Gmail settings."
                    )


            else:

                st.warning(
                    "Please enter an email address."
                )


        # --------------------------------------------------
        # Chat Section
        # --------------------------------------------------

        st.subheader(
            "💬 Ask about your study material"
        )


        question = st.chat_input(
            "Ask a question about the uploaded image..."
        )


        if question:

            try:

                chat_response = (
                    client.models.generate_content(
                        model="gemini-3.5-flash",

                        contents=[
                            types.Part.from_bytes(
                                data=image_bytes,
                                mime_type=uploaded_image.type
                            ),

                            question
                        ],

                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT
                        )
                    )
                )


                st.write("🤖 **AI:**")

                st.write(
                    chat_response.text
                )


            except Exception as e:
    		st.error(f"Gemini chat error: {e}")


    except Exception as e:
    	st.error(f"Gemini error: {e}")