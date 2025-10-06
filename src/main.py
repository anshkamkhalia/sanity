# main.py
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session # For backend
import json, random # For data handling ids
from datetime import datetime # For dates
from save import write_json # For saving to files
from google import genai # For LLM
from message import Message # Message class
import matplotlib
matplotlib.use("Agg")  # Use a non-GUI backend
import matplotlib.pyplot as plt # For mood visualization
import seaborn as sns # For enchanced visualization
import uuid # For ids
from datetime import date # More dates
import os # Directory handling
import time # For times

# Colors/sizes
sns.set_style('darkgrid')
plt.rcParams['figure.figsize'] = (14,10)

# Create app
app = Flask(__name__, static_folder="static")
app.secret_key = "supersecretkey" # For flashes

today_str = datetime.today().strftime("%Y-%m-%d") # Get today's date

# ---------------- MINDFULNESS CHALLENGE DATA ----------------
data = [ # Mindfulness challenges
        "Write down 3 things you have really appreciated from the day today.",
        "Walk for 10 minutes today, without looking at your phone, focused on your surroundings.",
        "Without any judgement or criticism, count how many times your mind gets distracted today.",
        "Every time your phone vibrates or pings today, pause and follow one breath before looking at it.",
        "Brush your teeth with your non-dominant hand today to help encourage attention.",
        "De-clutter part of your house or office today, helping the mind to feel calmer and clearer.",
        "Drink a mindful cup of tea or coffee today, free from other distractions, focused on taste and smell.",
        "Move email and social media apps to the second page of your phone today.",
        "Notice the sensation as you change posture today from standing to sitting or sitting to standing.",
        "Without forcing it, ask someone how they are today and listen to the reply free from opinion.",
        "Commit to no screen time for 2 hours before bed today, other than playing the sleep exercise.",
        "Pause for 60 seconds to follow the breath each time you enter and exit the car/bus/train today.",
        "Sit down and listen to a favorite song or piece of music today, whilst doing nothing else at all.",
        "Take 5 x 2 minute breaks today and simply follow the breath, as you do in your meditation.",
        "Rather than text someone today, call them instead and have a proper conversation.",
        "Check the kids sleeping before going to bed today and follow three of their deep breaths.",
        "Reset your posture each time you sit down today, gently straightening the back.",
        "Give heartfelt thanks to someone today who has recently helped you in some way.",
        "Turn off all notifications on your phone today.",
        "Eat one meal alone today, without any distractions at all, focusing just on the tastes and smells.",
        "Take one full breath (both in and out) before pressing send any email or social post today.",
        "Commute without music today, just for one day and see how much more you notice.",
        "Buy someone a coffee/tea/cake today for no reason, and without expectation of thanks.",
        "Get some exercise today, without your phone, and focus on the physical sensations.",
        "Take 3 x 30 minute breaks from the phone today, set a timer if you need to.",
        "Take one square of chocolate today and allow it to melt in the mouth, enjoying without chewing.",
        "Write a handwritten card/letter to a good friend you've not seen for a long time.",
        "Do something playful, whatever makes you smile or laugh, at least one time today.",
        "When you get to work, or arrive home, today, pause and follow 10 breaths before entering.",
        "Carry some loose change today and share it with people on the street who need it more."
    ]

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html") # Homepage

# ---------------- AUTH FUNCTIONS ----------------
@app.route("/get-auth")
def return_auth():
    return jsonify({"logged_in": session.get("logged_in", False)}) # For authentication

def check_auth():
    if not session.get("logged_in"):
        return redirect(url_for("authentication_page")) # Checks if user is currently logged in
    return None

@app.route("/login", methods=["GET", "POST"])
def authentication_page(): # Auth
    invalid_cred = False # Tracks if user inputted invalid creds

    if request.method == "POST":
        # Gets credentials and action from html form
        email = request.form.get("email")
        password = request.form.get("password")
        action = request.form.get("action")

        # Signup
        if action == "signup":
            new_user_data = {"email": email, "password": password} # Creates new user data

            # Collects data
            try:
                with open("src/data.json", "r") as file: 
                    data = json.load(file)
            except:
                data = []
            
            # Updates and writes back to file
            data.append(new_user_data)
            write_json("src/data.json", data)

            # Store in session only
            session["logged_in"] = True
            session["email"] = email
            return redirect(url_for("dashboard", tab="main"))

        # Login
        elif action == "login":
            # Saves data

            try:
                with open("src/data.json", "r") as file:
                    data = json.load(file)
            except:
                data = []

            for entry in data:
                if entry["email"] == email and entry["password"] == password:
                    # Store in session only
                    session["logged_in"] = True
                    session["email"] = email
                    return redirect(url_for("dashboard", tab="main"))

            invalid_cred = True # If nothing works, it means user has entered invalid credentials

    return render_template("auth.html", error="Invalid credentials" if invalid_cred else None) # Renders auth page

# ---------------- DASHBOARD ----------------
@app.route("/dashboard/")
@app.route("/dashboard/<tab>", methods=["GET", "POST"])
def dashboard(tab=None):
    auth_redirect = check_auth()
    if auth_redirect:
        return auth_redirect # Checks if a user is currently logged in

    # Valid dashboard tabs
    valid_tabs = {
        None: "main",
        "main": "main",
        "journal": "journal",
        "resources": "resources",
        "ai": "ai",
        "guided_breathing": "guided_breathing",
        "mindfulness_challenge": "mindfulness_challenge",
        "crisis_support": "crisis_support",
        'forum': 'forum',
        'thread_page': 'thread_page',
        'check_in': 'check_in',
    }

    # Checks for invalid tabs
    if tab not in valid_tabs:
        return redirect(url_for("dashboard", tab="main"))

    context = {"tab": valid_tabs[tab]}

    context["username"] = session.get("email", "friend").split("@")[0]

    # Gets journal entries
    try:
        with open("src/entries.json", "r") as f:
            all_entries = json.load(f)
        user_entries = [e for e in all_entries if e["email"] == session["email"]]
    except (FileNotFoundError, json.JSONDecodeError):
        user_entries = []

    context["number_of_entries"] = len(user_entries)
     

    # Journal entries
    if tab == "journal":
        search_date = request.args.get("date")
        try:
            with open("src/entries.json", "r") as f:
                entries = json.load(f)
            if search_date:
                context["searched_entries"] = [
                    e for e in entries
                    if e["email"] == session["email"] and e["date"] == search_date
                ]
            else:
                context["searched_entries"] = [
                    e for e in entries if e["email"] == session["email"]
                ]
        except (FileNotFoundError, json.JSONDecodeError):
            context["searched_entries"] = []

    # Mindfulness challenge session data
    if tab == "mindfulness_challenge":
        context["accepted_challenge"] = session.get("accepted_challenge", False)
        context["challenge"] = session.get("challenge")
        context["success_msg"] = session.get("success_msg")

    return render_template("dashboard.html", **context)

# ---------------- AI POST ----------------
@app.route('/dashboard/ai', methods=["POST", "GET"])
def ai():
    auth_redirect = check_auth() # Auth checking
    if auth_redirect: 
        return auth_redirect

    api_key = "AIzaSyDyS_S4HBPOl4HOO2pxRYPJWlvVt0vUdlc" # Key
    
    if not api_key: 
        return jsonify({"reply": "API key not found. Please set GEMINI_API_KEY."})

    client = genai.Client(api_key=api_key) # Create genai client
  
    global username
    username = session.get("email", "friend").split("@")[0] # Extract username

    if request.method == "POST":
        user_message = request.json.get("message") # Get message
        print(f"[DEBUG] User message: {user_message}")

        # Gemini instructions
        gemini_prompt = f"""
        You are a compassionate and professional therapist.
        Provide emotional support, guidance, and encouragement to {username}.
        User says: "{user_message}"

        Instructions:
        1. Be empathetic, patient, and understanding.
        2. Keep responses appropriate, respectful, and safe.
        3. Focus on listening and offering gentle guidance.
        """

        try:
            # 1️⃣ Create chat
            chat = client.chats.create(model="gemini-2.0-flash")

            # 2️⃣ Send the prompt
            response = chat.send_message(gemini_prompt)

            reply_text = response.text if response else "Sorry, I couldn't get a response."
            print(f"[DEBUG] AI reply: {reply_text}")

            return jsonify({"reply": reply_text})

        except Exception as e:
            print(f"[ERROR] Gemini API failed: {e}")
            return jsonify({"reply": "Sorry, the AI is currently unavailable."})

    # GET request just renders the page
    return render_template("dashboard.html", tab="ai")


# ---------------- JOURNAL POST ----------------
@app.route("/dashboard/journal", methods=["POST"])
def journal_post():
    auth_redirect = check_auth()
    if auth_redirect:
        return auth_redirect

    # Add new entry
    entry = request.form.get("entry")
    entry_dict = {
        "email": session["email"],
        "entry": entry,
        "date": today_str
    }

    try:
        with open("src/entries.json", "r") as f:
            entries = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        entries = []

    entries.append(entry_dict)
    write_json("entries.json", entries)

    flash("Entry saved!", "success")
    return redirect(url_for("dashboard", tab="journal"))

# ---------------- MINDFULNESS CHALLENGE POST ----------------
@app.route("/mindfulness_challenge", methods=["POST"])
def mindfulness_challenge_post():
    auth_redirect = check_auth()
    if auth_redirect:
        return auth_redirect

    if "accepted_challenge" not in session:
        session["accepted_challenge"] = False
        session["challenge"] = None
        session["success_msg"] = None

    form_type = request.form.get("form_type")
    if form_type == "get_challenge":
        session["challenge"] = random.choice(data)
        session["accepted_challenge"] = True
        session["success_msg"] = None
    elif form_type == "finish_challenge":
        username = session.get("email", "friend").split("@")[0]
        session["success_msg"] = f"Great job, {username}!"

    return redirect(url_for("dashboard", tab="mindfulness_challenge"))

# ---------------- FORUM ----------------
@app.route('/dashboard/forum', methods=['GET', 'POST'])
def forum():
    messages = []
    with open('src/messages.json', 'r') as f:
        try:
            messages = json.load(f)
        except:
            messages = []

    create_new_thread = False
    form_name = request.form.get('form_name')

    if request.method == "POST":
        if form_name == "new_thread":
            create_new_thread = True

        elif form_name == "submit_question":
            question = request.form.get("question")
            question_obj = Message(question=question)

            new_data = {
                'id': str(uuid.uuid4()),  # unique thread ID
                'sender': session['email'],
                'question': question_obj.question,
                'likes': question_obj.likes,
                'replies': question_obj.replies,
                'date_posted': question_obj.date_posted,
            }
            messages.append(new_data)

            with open('src/messages.json', 'w') as f:
                json.dump(messages, f, indent=4)

            return redirect(url_for('thread_page', thread_id=new_data['id']))

    return render_template(
        'dashboard.html',
        tab='forum',
        threads=messages if messages else [],
        create_new_thread=create_new_thread
    )

# ---------------- THREAD PAGES ----------------
@app.route('/dashboard/forum/<thread_id>')
def thread_page(thread_id):
    with open('src/messages.json', 'r') as f:
        messages = json.load(f)

    thread = next((m for m in messages if m['id'] == thread_id), None)
    if not thread:
        return "Thread not found", 404

    return render_template("dashboard.html",tab='thread_page', thread=thread)

# ---------------- ADD REPLY ----------------
@app.route('/dashboard/forum/<thread_id>/reply', methods=['POST'])
def add_reply(thread_id):
    reply_text = request.form.get("reply", "").strip()
    reply_sender = session['email']

    if not reply_text:
        return redirect(url_for('thread_page', thread_id=thread_id))

    with open('src/messages.json', 'r') as f:
        messages = json.load(f)

    for thread in messages:
        if thread['id'] == thread_id:
            thread['replies'][reply_sender] = reply_text
            break

    with open('src/messages.json', 'w') as f:
        json.dump(messages, f, indent=4)

    return redirect(url_for('thread_page', thread_id=thread_id))


# ---------------- LIKE THREAD ----------------
@app.route('/dashboard/forum/<thread_id>/like', methods=['POST'])
def like_thread(thread_id):
    with open('src/messages.json', 'r') as f:
        messages = json.load(f)

    for thread in messages:
        if thread['id'] == thread_id:
            thread['likes'] += 1
            break

    with open('src/messages.json', 'w') as f:
        json.dump(messages, f, indent=4)

    return redirect(url_for('thread_page', thread_id=thread_id))

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()  
    return redirect(url_for("authentication_page"))

# ---------------- CHECK IN ----------------
@app.route('/dashboard/check_in', methods=["GET", "POST"])
def check_in():

    JSON_PATH = 'src/mood_entries.json'
    mood_data = {}
    success_msg = None

    # ---------------- Load existing mood entries safely ----------------
    if os.path.exists(JSON_PATH):
        try:
            with open(JSON_PATH, 'r') as f:
                content = f.read().strip()
                if content:
                    mood_data = json.loads(content)
                else:
                    mood_data = {}
        except json.JSONDecodeError:
            print("⚠️ Corrupt JSON file, resetting mood_data.")
            mood_data = {}
    else:
        mood_data = {}

    # Ensure session email exists
    email = session.get('email')
    if not email:
        return redirect(url_for("authentication_page"))

    # ---------------- Fix old JSON format ----------------
    # Convert {"date":[..], "score":[..]} into [{"date":..,"score":..}, ...]
    if email in mood_data:
        fixed_entries = []
        for entry in mood_data[email]:
            if isinstance(entry.get("date"), list) and isinstance(entry.get("score"), list):
                # Convert old format
                for d, s in zip(entry["date"], entry["score"]):
                    fixed_entries.append({"date": d, "score": s})
            else:
                fixed_entries.append(entry)
        mood_data[email] = fixed_entries

    user_mood = mood_data.get(email, [])

    # ---------------- Handle new POST submission ----------------
    if request.method == "POST":
        mood = request.form.get("mood_rank")
        today_str = date.today().isoformat()

        if any(entry["date"] == today_str for entry in user_mood):
            success_msg = "⚠️ You already checked in today! Come back tomorrow 🌅"
        else:
            try:
                mood_dict = {"date": today_str, "score": int(mood)}
                user_mood.append(mood_dict)
                mood_data[email] = user_mood
                # Save updated data
                with open(JSON_PATH, 'w') as f:
                    json.dump(mood_data, f, indent=4)
                success_msg = "✅ Saved! Remember to continue checking in!"
            except Exception as e:
                print(f"[ERROR] Failed to save mood: {e}")
                success_msg = "⚠️ Failed to save your mood. Try again."

    # Reload latest data
    user_mood = mood_data.get(email, [])

    # ---------------- GRAPH ----------------
    IMAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "images")
    os.makedirs(IMAGE_DIR, exist_ok=True)
    IMAGE_PATH = os.path.join(IMAGE_DIR, "mood_graph.png")

    if user_mood:
        # Sort by date
        user_mood_sorted = sorted(user_mood, key=lambda e: datetime.fromisoformat(e["date"]))
        x = [datetime.fromisoformat(entry["date"]).strftime("%b %d") for entry in user_mood_sorted]
        y = [entry["score"] for entry in user_mood_sorted]

        plt.figure(figsize=(14, 10))
        sns.lineplot(x=x, y=y, color="skyblue", marker="o", linewidth=3)
        plt.xlabel("Day", fontsize=16)
        plt.ylabel("Score", fontsize=16)
        plt.title("Mood Progression", fontsize=20)
        plt.xticks(rotation=45)
        plt.ylim(0, 10)
        plt.tight_layout()
        plt.savefig(IMAGE_PATH, bbox_inches="tight")
        plt.close()
    else:
        # Placeholder image
        plt.figure(figsize=(14, 10))
        plt.text(0.5, 0.5, "No mood data yet", ha='center', va='center', fontsize=20)
        plt.axis('off')
        plt.savefig(IMAGE_PATH, bbox_inches="tight")
        plt.close()

    # Cache-busting for browser
    graph_url = f"/static/images/mood_graph.png?ts={int(time.time())}"

    return render_template(
        'dashboard.html',
        tab='check_in',
        success_msg=success_msg,
        graph_url=graph_url
    )

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
