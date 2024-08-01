import openai
import streamlit as st
import requests
import json
import chardet  # Ensure chardet is imported

# Get the API key from environment variables
api_key = st.secrets['OPENAI_API']

if not api_key:
    st.error("Kein API-Schlüssel gesetzt. Bitte setze die Umgebungsvariable OPENAI_API_KEY.")
else:
    openai.api_key = api_key
    st.write(f" ")

# URL of the trainingsdaten.json file in your GitHub repository
url = "https://raw.githubusercontent.com/Bernhard-Keller123/AventraGPT_QM/main/trainingdata.json"

# Function to load training data from GitHub
def lade_trainingsdaten_aus_github(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check for HTTP errors
        content = response.content.decode('utf-8')  # Decode content
        if content:
            try:
                return json.loads(content)  # Parse JSON data
            except json.JSONDecodeError:
                st.error("Fehler beim Parsen der JSON-Daten von GitHub. Die Datei ist möglicherweise beschädigt oder leer.")
                return []
        else:
            st.warning("Die Datei von GitHub ist leer.")
            return []
    except requests.RequestException as e:
        st.error(f"Fehler beim Laden der Trainingsdaten von GitHub: {e}")
        return []

trainingsdaten = lade_trainingsdaten_aus_github(url)
chat_history = [{"role": "system", "content": td} for td in trainingsdaten]

def generiere_antwort(prompt):
    chat_history.append({"role": "user", "content": prompt})
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=chat_history,
            max_tokens=600,
            n=1,
            stop=None,
            temperature=0.7
        )
        antwort = response.choices[0].message['content'].strip()
        chat_history.append({"role": "assistant", "content": antwort})
        return antwort
    except openai.error.OpenAIError as e:
        if "quota" in str(e):
            return "Du hast dein aktuelles Nutzungslimit überschritten. Bitte überprüfe deinen Plan und deine Abrechnungsdetails unter https://platform.openai.com/account/usage."
        return str(e)

# Streamlit App
st.title("AventraGPT_MK")

# Input field for the prompt
prompt = st.text_input("Du: ")

# Button to send the prompt
if st.button("Senden"):
    if prompt:
        antwort = generiere_antwort(prompt)
        st.text_area("AventraGPT:", value=antwort, height=200, max_chars=None)

# File upload for training data
uploaded_file = st.file_uploader("Trainingsdaten hochladen", type=["txt"])

# Button to load training data
if st.button("Trainingsdaten laden"):
    if uploaded_file:
        try:
            # Try to read the file and detect encoding
            raw_data = uploaded_file.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            training_data = raw_data.decode(encoding)

            # Update the training data and save it
            if training_data.strip():  # Check if data is not empty
                trainingsdaten.append(training_data)
                with open('trainingdata.json', 'w') as f:
                    json.dump({"message": "START", "data": trainingsdaten}, f, ensure_ascii=False, indent=4)
                chat_history.append({"role": "system", "content": training_data})
                st.success("Trainingsdaten erfolgreich geladen.")
            else:
                st.error("Die hochgeladene Datei enthält keine Daten.")
        except Exception as e:
            st.error(f"Fehler beim Laden der Datei: {e}")

# Display the chat history
st.subheader("Trainingsdaten und Gesprächsverlfs")
for eintrag in chat_history:
    if eintrag['role'] == 'user':
        st.write(f"Du: {eintrag['content']}")
    elif eintrag['role'] == 'assistant':
        st.write(f"LLM: {eintrag['content']}")
    elif eintrag['role'] == 'system':
        st.write(f"System: {eintrag['content']}")
