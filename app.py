
import streamlit as st
from google import genai
from google.genai import types
from prompts import SYSTEM_PROMPT
import smtplib
import hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# --------------------------------------------------
# 1. PAGE SETTINGS
# --------------------------------------------------

st.set_page_config(
    page_title="Snap & Study",
    page_icon="📚",
    layout="centered"
)

st.title("📚 Snap & Study")
st.write("Your AI-powered study assistant")
st.write(
    "Upload a photo of your notes, textbook, "
    "question, or diagram to understand it easily."
)


# --------------------------------------------------
# 2. CONNECT TO GEMINI
# --------------------------------------------------

try:
    client = genai.Client(
        api_key=st.secrets["GEMINI_API_KEY"]
    )
except Exception as e:
    st.error(f"Unable to initialize Gemini: {e}")
    st.stop()


# --------------------------------------------------
# 3. UPLOAD STUDY IMAGE
# --------------------------------------------------

uploaded_image = st.file_uploader(
    "📸 Upload your study image",
    type=["jpg", "jpeg", "png"]
)


if uploaded_image:

    image_bytes = uploaded_image.getvalue()
    image_hash = hashlib.md5(image_bytes).hexdigest()

    # Reset the saved explanation when a new image is uploaded
    if st.session_state.get("image_hash") != image_hash:
        st.session_state["image_hash"] = image_hash
        st.session_state["explanation"] = None

    st.image(
        uploaded_image,
        caption="Your uploaded study material",
        use_container_width=True
    )

    # --------------------------------------------------
    # 4. GENERATE AI EXPLANATION
    # --------------------------------------------------

    if st.session_state.get("explanation") is None:

        with st.spinner("🤖 Analyzing your study material..."):

            try:
                response = client.models.generate_content(
                    model="gemini-3.5-flash",
                    contents=[
                        types.Part.from_bytes(
                            data=image_bytes,
                            mime_type=uploaded_image.type
                        ),
                        (
                            "Analyze this study material. "
                            "Identify the topic and explain it "
                            "in simple student-friendly language. "
                            "Organize the answer with headings, "
                            "important points, and examples where useful."
                        )
                    ],
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT
                    )
                )

                if not response.text:
                    st.error(
                        "Gemini returned an empty response. "
                        "Please try another image."
                    )
                else:
                    st.session_state["explanation"] = response.text

            except Exception as e:
                st.error(f"Gemini error: {e}")

    # --------------------------------------------------
    # 5. DISPLAY EXPLANATION
    # --------------------------------------------------

    explanation = st.session_state.get("explanation")

    if explanation:

        st.subheader("🤖 AI Explanation")
        st.markdown(explanation)

        st.divider()

        # --------------------------------------------------
        # 6. SEND EXPLANATION THROUGH EMAIL
        # --------------------------------------------------

        st.subheader("📧 Send Explanation to Email")

        receiver_email = st.text_input(
            "Enter the recipient's email address",
            key="receiver_email"
        )

        if st.button("📨 Send Email"):

            if not receiver_email.strip():
                st.warning("Please enter an email address.")

            elif "@" not in receiver_email or "." not in receiver_email:
                st.warning("Please enter a valid email address.")

            else:
                try:
                    message = MIMEMultipart()

                    message["From"] = st.secrets["GMAIL_ADDRESS"]
                    message["To"] = receiver_email.strip()
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
                        MIMEText(email_body, "plain")
                    )

                    with smtplib.SMTP_SSL(
                        "smtp.gmail.com",
                        465,
                        timeout=30
                    ) as server:

                        server.login(
                            st.secrets["GMAIL_ADDRESS"],
                            st.secrets["GMAIL_APP_PASSWORD"]
                        )

                        server.send_message(message)

                    st.success(
                        "✅ Explanation sent successfully!"
                    )

                except Exception:
                    st.error(
                        "Unable to send the email. "
                        "Please check your Gmail settings "
                        "and Streamlit secrets."
                    )

        st.divider()

        # --------------------------------------------------
        # 7. ASK FOLLOW-UP QUESTIONS
        # --------------------------------------------------

        st.subheader("💬 Ask About Your Study Material")

        question = st.chat_input(
            "Ask a question about the uploaded image..."
        )

        if question:

            with st.spinner("🤖 Preparing your answer..."):

                try:
                    chat_response = client.models.generate_content(
                        model="gemini-3.5-flash",
                        contents=[
                            types.Part.from_bytes(
                                data=image_bytes,
                                mime_type=uploaded_image.type
                            ),
                            (
                                "Here is the explanation already given "
                                "to the student:\n"
                                + explanation
                            ),
                            (
                                "Answer this follow-up question "
                                "clearly and simply:\n"
                                + question
                            )
                        ],
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT
                        )
                    )

                    if chat_response.text:
                        st.write("🤖 **AI Answer**")
                        st.markdown(chat_response.text)
                    else:
                        st.warning(
                            "No answer was returned. "
                            "Please try your question again."
                        )

                except Exception as e:
                    st.error(f"Gemini chat error: {e}")

else:
    st.info(
        "👆 Upload a study image to get started."
    )

    st.markdown(
        """
        **You can use Snap & Study to:**
        - Understand textbook pages and class notes
        - Explain diagrams and concepts
        - Get answers to follow-up questions
        - Send explanations to your email
        """
    )
