import os
import json
import requests
from datetime import date
from groq import Groq

USED_TOPICS_FILE = "used_topics.json"

def load_used_topics():
    if os.path.exists(USED_TOPICS_FILE):
        with open(USED_TOPICS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_used_topics(topics):
    with open(USED_TOPICS_FILE, "w", encoding="utf-8") as f:
        json.dump(topics, f, ensure_ascii=False, indent=2)

def generate_topic(used_topics):
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    recent = used_topics[-30:] if len(used_topics) > 30 else used_topics
    used_list = "\n".join(f"- {t}" for t in recent)

    prompt = f"""You are helping an English language learning community on Telegram.
Generate ONE engaging topic of the day for discussion.

Format your response exactly like this:
📌 [Topic Title]

💬 Start the conversation:
• [Question 1]
• [Question 2]
• [Question 3]

Keep it friendly, interesting, and suitable for intermediate English learners.
Today's date: {date.today().strftime("%B %d, %Y")}

Topics already used — do NOT repeat these:
{used_list if used_list else "None yet — this is the first topic!"}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
        temperature=0.9
    )

    return response.choices[0].message.content.strip()

def post_to_telegram(text):
    bot_token = os.environ["BOT_TOKEN"]
    chat_id = os.environ["CHAT_ID"]

    response = requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
    )

    if not response.ok:
        raise Exception(f"Telegram API error: {response.text}")

def extract_title(topic_text):
    for line in topic_text.split("\n"):
        line = line.strip()
        if line:
            return line.replace("📌", "").strip()
    return topic_text[:80]

def main():
    print("Loading used topics...")
    used_topics = load_used_topics()
    print(f"Total topics used so far: {len(used_topics)}")

    print("Generating new topic via Groq...")
    topic = generate_topic(used_topics)
    print(f"\nGenerated:\n{topic}\n")

    print("Posting to Telegram...")
    post_to_telegram(topic)
    print("Posted successfully!")

    title = extract_title(topic)
    used_topics.append(title)
    save_used_topics(used_topics)
    print("Saved to used_topics.json")

if __name__ == "__main__":
    main()
