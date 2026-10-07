import time
import streamlit as st
from google import genai
from google.genai import types
from prompts import SYSTEM_PROMPT
import smtplib
import hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


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


# ---------------- GEMINI SETUP ----------------

try:
    client = genai.Client(
        api_key=st.secrets["GEMINI_API_KEY"]
    )
except Exception as e:
    st.error(f"Unable to initialize Gemini: {e}")
    st.stop()


# ---------------- IMAGE UPLOAD ----------------

uploaded_image = st.file_uploader(
    "📸 Upload your study image",
    type=["jpg", "jpeg", "png"]
)


if uploaded_image:

    image_bytes = uploaded_image.getvalue()

    image_hash = hashlib.md5(
        image_bytes
    ).hexdigest()

    if st.session_state.get("image_hash") != image_hash:

        st.session_state["image_hash"] = image_hash
        st.session_state["explanation"] = None

    st.image(
        uploaded_image,
        caption="Your uploaded study material",
        use_container_width=True
    )


    # ---------------- AI EXPLANATION ----------------

    if st.session_state.get("explanation") is None:

        with st.spinner("🤖 Analyzing your study material..."):

            explanation = None

            # First model
            models_to_try = [
                "gemini-3.5-flash",
                "gemini-3.5-flash-lite"
            ]

            for model_name in models_to_try:

                for attempt in range(2):

                    try:

                        response = client.models.generate_content(

                            model=model_name,

                            contents=[

                                types.Part.from_bytes(
                                    data=image_bytes,
                                    mime_type=uploaded_image.type
                                ),

                                (
                                    "Analyze this study material. "
                                    "Identify the main topic and give "
                                    "EXACTLY 5 important points from the image. "
                                    "Keep every point short and simple. "
                                    "Use numbered points from 1 to 5."
                                )
                            ],

                            config=types.GenerateContentConfig(

                                system_instruction=SYSTEM_PROMPT

                            )
                        )


                        if response.text:

                            explanation = response.text

                            break


                    except Exception as e:

                        error_message = str(e)


                        # Retry only for 503 errors

                        if "503" in error_message:

                            if attempt == 0:

                                st.warning(
                                    f"{model_name} is temporarily busy. "
                                    "Trying again..."
                                )

                                time.sleep(3)

                            else:

                                st.warning(
                                    f"{model_name} is unavailable. "
                                    "Trying another model..."
                                )

                        else:

                            st.error(
                                f"Gemini error: {error_message}"
                            )

                            break


                # Stop if a model worked

                if explanation:

                    break


            # ---------------- FINAL RESULT ----------------

            if explanation:

                st.session_state["explanation"] = explanation

            else:

                st.error(
                    "⚠️ Gemini is currently unavailable. "
                    "Both AI models were unable to process the image. "
                    "Please try again later."
                )


    # ---------------- SHOW EXPLANATION ----------------

    explanation = st.session_state.get("explanation")


    if explanation:

        st.subheader("🤖 AI Explanation")

        st.markdown(explanation)


        st.divider()


        # ---------------- EMAIL ----------------

        st.subheader("📧 Send Explanation to Email")


        receiver_email = st.text_input(
            "Enter the recipient's email address",
            key="receiver_email"
        )


        if st.button("📨 Send Email"):

            if not receiver_email.strip():

                st.warning(
                    "Please enter an email address."
                )

            elif "@" not in receiver_email or "." not in receiver_email:

                st.warning(
                    "Please enter a valid email address."
                )

            else:

                try:

                    message = MIMEMultipart()

                    message["From"] = (
                        st.secrets["GMAIL_ADDRESS"]
                    )

                    message["To"] = (
                        receiver_email.strip()
                    )

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


                    with smtplib.SMTP_SSL(
                        "smtp.gmail.com",
                        465,
                        timeout=30
                    ) as server:

                        server.login(

                            st.secrets["GMAIL_ADDRESS"],

                            st.secrets[
                                "GMAIL_APP_PASSWORD"
                            ]
                        )

                        server.send_message(
                            message
                        )


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


        # ---------------- FOLLOW-UP CHAT ----------------

        st.subheader(
            "💬 Ask About Your Study Material"
        )


        question = st.chat_input(
            "Ask a question about the uploaded image..."
        )


        if question:

            with st.spinner(
                "🤖 Preparing your answer..."
            ):

                try:

                    chat_response = (
                        client.models.generate_content(

                            model="gemini-3.5-flash",

                            contents=[

                                types.Part.from_bytes(
                                    data=image_bytes,
                                    mime_type=uploaded_image.type
                                ),

                                (
                                    "Here is the explanation "
                                    "already given to the student:\n"
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
                    )


                    if chat_response.text:

                        st.write(
                            "🤖 **AI Answer**"
                        )

                        st.markdown(
                            chat_response.text
                        )

                    else:

                        st.warning(
                            "No answer was returned. "
                            "Please try your question again."
                        )


                except Exception as e:

                    st.error(
                        f"Gemini chat error: {e}"
                    )


# ---------------- HOME MESSAGE ----------------

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