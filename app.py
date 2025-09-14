"""
Dream-to-Story — Streamlit app (single-file)
Features:
- User enters a dream (in Urdu/English)
- App detects dream mood (e.g., scary, joyful, confusing)
- App generates a short creative story based on the dream
- App suggests a possible moral / life lesson
- Options: choose genre, story length, download result

How to use (short):
1. Save this file as `app.py`.
2. Install dependencies: `pip install -r requirements.txt`
3. Put your OpenAI API key in environment variable `OPENAI_API_KEY` or in a `.env` file.
4. Run: `streamlit run app.py`

This file intentionally contains helpful comments (English + short Urdu hints).
"""

import os
import streamlit as st
from openai import OpenAI
from typing import Tuple
from dotenv import load_dotenv

# Load .env if present (for local development). .env should contain OPENAI_API_KEY
load_dotenv()

# Initialize OpenAI client using environment variable OPENAI_API_KEY
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    # Streamlit will show this to the user if key is missing
    st.warning("OPENAI_API_KEY not found. Please set it as an environment variable or in a .env file.")

client = OpenAI(api_key=api_key) if api_key else None

# ---- Helper functions ----

def analyze_mood(dream_text: str) -> str:
    """Use the model to classify the mood of the dream.
    Returns a short mood label like: 'Scary', 'Happy', 'Confusing', 'Hopeful', 'Surreal', etc.
    """
    if not client:
        return "Unknown (no API key)"

    system = (
        "You are a short-text mood classifier for dreams. "
        "Given a user dream text, reply with one short mood label only. "
        "Choose from: Scary, Happy, Peaceful, Anxious, Confusing, Exciting, Sad, Surreal, Neutral."
    )

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": dream_text}
        ],
        temperature=0.0,
        max_tokens=30,
    )
    label = resp.choices[0].message.content.strip()
    return label


def generate_story_and_moral(dream_text: str, genre: str, length: str) -> Tuple[str, str]:
    """Generate a creative short story and a moral from the dream text.
    Returns (story, moral)
    """
    if not client:
        return ("(API key missing)", "")

    # Guidance to the model -- clear, short format expected
    system = (
        "You are a creative writer who converts people's dreams into short fictional stories. "
        "Respond in two labeled sections: STORY: <story text> and MORAL: <one-sentence moral>. "
        "Keep language simple and vivid. Respect the chosen genre and requested length."
    )

    # Tailor length to approximate tokens / style
    length_hint = {
        "Short": "Keep it very short (3-5 sentences).",
        "Medium": "Make it medium length (5-8 sentences).",
        "Long": "Make it longer (8-12 sentences)."
    }.get(length, "Keep it short.")

    prompt = (
        f"User dream: {dream_text}\n"
        f"Genre: {genre}\n"
        f"Length hint: {length_hint}\n"
        "Write a short creative story inspired by the dream. Then write a one-sentence moral."
    )

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=550,
    )

    text = resp.choices[0].message.content.strip()

    # Try to split the model output into STORY and MORAL sections.
    story = text
    moral = ""
    # Look for explicit labels
    if "STORY:" in text.upper() and "MORAL:" in text.upper():
        # find positions case-insensitively
        up = text.upper()
        s_idx = up.find("STORY:")
        m_idx = up.find("MORAL:")
        story = text[s_idx + len("STORY:"):m_idx].strip()
        moral = text[m_idx + len("MORAL:"):].strip()
    else:
        # fallback: split by lines and take the last line as moral if short
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        if len(lines) >= 2:
            moral = lines[-1]
            story = "\n".join(lines[:-1])

    return story, moral


# ---- Streamlit UI ----

st.set_page_config(page_title="Dream → Story", page_icon="✨")
st.title("✨ Dream → Story — Turn your dream into a creative story")
st.markdown("Write a short description of a dream (Urdu or English). The app will detect the mood and create a story + a short moral.")

with st.form("dream_form"):
    dream_input = st.text_area("Describe your dream", height=160, placeholder="I was flying above a city... / Kal raat mujhe sapna aya ke...")
    col1, col2 = st.columns(2)
    with col1:
        genre = st.selectbox("Genre", ["Fantasy", "Mystery", "Drama", "Comedy", "Surreal", "Horror"], index=0)
    with col2:
        length = st.selectbox("Story length", ["Short", "Medium", "Long"], index=1)

    submit = st.form_submit_button("Create Story ✨")

if submit:
    if not dream_input.strip():
        st.warning("Please enter a dream description before clicking Create Story.")
    else:
        with st.spinner("Analyzing dream and writing story..."):
            mood = analyze_mood(dream_input)
            story, moral = generate_story_and_moral(dream_input, genre, length)

        st.subheader("🔎 Dream Mood")
        st.write(mood)

        st.subheader("📖 Story")
        st.write(story)

        st.subheader("💡 Moral")
        st.write(moral if moral else "(No explicit moral generated.)")

        # Allow download as a text file
        full_text = f"Dream:\n{dream_input}\n\nMood: {mood}\n\nStory:\n{story}\n\nMoral:\n{moral}\n"
        st.download_button("Download story as .txt", data=full_text, file_name="dream_story.txt")

        # Save to local file optionally
        try:
            os.makedirs("stories", exist_ok=True)
            import hashlib
            h = hashlib.sha1(dream_input.encode("utf-8")).hexdigest()[:8]
            fname = f"stories/dream_{h}.txt"
            with open(fname, "w", encoding="utf-8") as f:
                f.write(full_text)
            st.info(f"Saved locally: {fname}")
        except Exception as e:
            st.warning("Could not save locally: " + str(e))

# Footer / tips
st.markdown("---")
st.markdown("**Tips:**\n- Write 1-3 lines for a clearer story.\n- You can write in Urdu or English.\n- If you want more poetic language, increase the temperature in the code.\n- Keep your API key private.")

# Show example quick buttons
st.markdown("**Try these example dreams:**")
col1, col2, col3 = st.columns(3)
if col1.button("Flying over mountains"):
    st.experimental_set_query_params()
    st.session_state['__autofill'] = "I was flying over snow-capped mountains and suddenly the sky turned purple."
if col2.button("Lost in a city"):
    st.session_state['__autofill'] = "I wandered through an endless city with unfamiliar streets and shops that changed each time I looked away."
if col3.button("Unexpected exam"):
    st.session_state['__autofill'] = "I arrived at an exam hall and realized I didn't study the subject at all. Everyone was watching me."

# If autofill exists, show it
if ' __autofill' in st.session_state or '__autofill' in st.session_state:
    # fix potential key name spacing
    key = '__autofill' if '__autofill' in st.session_state else ' __autofill'
    st.experimental_rerun()


# Requirements note (displayed at top if running locally)
st.caption("Requirements: streamlit, openai (official), python-dotenv (optional). See the canvas code for full details.")

# End of file
