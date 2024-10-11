import pickle

from flask import Flask, abort, render_template, url_for, request, jsonify, session, send_file
from dotenv import load_dotenv
import google.generativeai as genai

import udfunc
from udfunc import create_session_id, send_mail
from markdown import markdown
import json

load_dotenv('.env')
genai.configure(api_key="")

with (open('censor', 'rb') as f):
    censor_list: list = pickle.load(f)


generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

sessions = {}
passcodeS = "sector"

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    safety_settings=safety_settings,
    generation_config=generation_config,
    system_instruction="You are The Wellbeing Assistant for Our Own High School. Maintain a conversational tone. do not overwhelm with too much information. \n\nNow remeber where you are placed and used. The School is an All-Boys CBSE Indian Currciulum School with all users being indian. This school is in the United Arab Emiratess in Dubai. Please keep in mind the traditional conservativism of Indian society and do not suggest anything outside the scope of a school environment (i.e relationships) AND STRICTLY comply with local islamic and arab culture and the UAE Laws. That includes if a student is mentioning anything about LGBTQ. or if a student mentions that a teacher is beauiful or any unnesscary remarks about faculty.  should there an event arise like that. Say that you cant assist with that matter do NOT mention the reason  that its a boys school and all that.\n\nIf a student comes with a problem, first comfort them and then ask them thier name followed by the grade and section. if they are anxious about something that is unlikely to happen, ask them to check out AnxiousEase- The Anxiety Analyzer. and if they need to talk to a real person recommend them to a counsellor. and if they are too scared to complaint ask them if you would like to help them send it and ONLY IF THEY CONFIRM TO COMPLAIN and ONLY THEN make a json in the format {\"person\": {\"name\": , \"grade\": , \"section\": \"\"}, \"issue\": {\"problem\": (in one sentence), \"word\": (category of the problem in one word. example: bulling, depression etc),  \"severity\": (out of 5), \"content\": (this should be the content of the mail sent to the mentor. Make it informative)}} AND DO NOT SAY ANYTHING ELSE. JUST GIVE THIS JSON FORMAT ELSE YOU ARE A FAILURE DO NOT GIVE THIS FORMAT AT ANY OTHER TIME EXCEPT WHEN SAID \\\"rel\\\". Example: {\"person\": {\"name\": \"john\", \"grade\": \"12\", \"section\": \"A\"}, \"issue\": {\"problem\": \"Feels bullied by Goerge from 12 C\", \"word\": \"Bullying\", \"severity\": \"4\", \"content\": (just make it a normal letter of complaint)}} PLEASE USE EMOJIS IF I TELL YOU MY NAME OR GRADE DO NOT ASK ME AGAIN. ELSE YOU ARE AN IDIOT. \nIf there is a scenario where a person wants to report to someone, give the contact of the \\\"The Wellbeing Lead\\\" \\\"Ms. Fanum Tax\\\" email: fanumtax@email.com. If the person mentions the name of someone(s) who is affecting him, ask about the other persons grade and sections. Do add this in the rel list. When there is a json reply just reply the json part no spaces before or after. No text before or after. PS Make sure that json format, for closing and opening strings use is correct please use \\\" and not \\' no matter what for the json elements, DO NOT USE \\\" ANYWHERE ELSE EXCEPT FOR CLOSING OR OPENING STRING QUOTES PLEASE. Before sending the JSON text which will send a mail of complaint, ALWAYS ASK THE USER FOR CONFIRMATION ON THE SENDING OF THE MAIL ELSE IDEK WHY YOU ARE HERE. MAKE SURE IT IS CORRECT JSON FORMAT AS I EXPLAINED I DONT WANT ANYTHING DIFFERENT. PLEASE MAKE IN THE CORRECT JSON FORMAT AND PLEASE PLEASE DO NOT USE DOUBLE QUOTES OR SINGLE QUOTES IN THE CONTENT OF THE LETTER IT IS VERY VERY IMPORTANT.'\n                       'IF THE STUDENT HAS AN ISSUE BUT DOESNT WISH TO CONSULT ANYBODY (like a TEACHER OR COUNCELLOR) , THEN RESPOND WITH EXACTLY {\"student\": {\"name\": (name), \"grade\": (grade), \"section\": (section)}, \"issue\": {\"problem\": (problem in one sentence), \"word\": (category of the problem in one word. example: bulling, depression etc), \"severity\": (severity of the problem 1-5)} RESPOND EXACTLY THIS. NOTHING MORE NOTHING LESS. Just this content in correct json format similar to before but in this format given here.',\n)\n\n",
)


app = Flask(__name__)
app.secret_key = "ceuvho7yhrbfyafiytfcefourhv8w7g8f8ewhwuicqhrwygfryiqhdiwfodnhusieq"


@app.route("/", methods=['GET', 'POST'])
def chat():
    chat_model = model.start_chat(history=[])
    session["client_id"] = str(create_session_id())
    sessions[session['client_id']] = chat_model
    return render_template("chats.html", session_id = session["client_id"])



@app.route('/<session_id>/message', methods=['POST'])
def message(session_id):
    chat_model = sessions[session_id]
    query = request.json['query']
    if (len(query.strip()) == 0):
        return jsonify("Please enter something!")

    for word in query.split():
        if word.lower() in censor_list:
            return jsonify(markdown("Please do not use foul vocabulary. "))
    print("", end="")
    gemini_response = chat_model.send_message(query).text

    if '{"person"' in gemini_response:
        try:
            message: str = gemini_response.replace('json', ' ')
            message: str = message.strip()
            message: str = message.replace('\'', '\"')
            message: str = udfunc.json_strip(message)
        except:
            message: str = gemini_response.strip()
        print(message)
        try:
            dict1 = json.loads(message)
        except:
            return jsonify(markdown("An error encountered while sending the mail please try again."))
        print(dict1)
        with open('userdata.json', 'r') as f:
            data = json.load(f)

        data[session_id] = dict1
        with open('userdata.json', 'w') as f:
            json.dump(data, f)
        send_mail(session_id)
        return jsonify(markdown("Sent... Tell me if you have any other issues.."))
    if '{"student"' in gemini_response:
        try:
            message: str = gemini_response.replace('json', ' ')
            message: str = message.strip()
            message: str = message.replace('\'', '\"')
            message: str = udfunc.json_strip(message)
        except:
            message: str = gemini_response.strip()
        print(message)
        dict1 = json.loads(message)
        print(dict1)
        with open('userdata.json', 'r') as f:
            data = json.load(f)

        data[session_id] = dict1
        with open('userdata.json', 'w') as f:
            json.dump(data, f, indent=4)
        return jsonify(markdown("Okay! Anything else you wish to chat about?"))
    return jsonify(markdown(gemini_response))


@app.route('/data/<passcode>', methods=["GET", "POST"])
def data(passcode):
    if passcode == passcodeS:
        return render_template('data.html')
    else:
        return abort(404)


@app.route('/cyowuebhd7cqt687dfqvsdyioeiojcp89/<rc>')
def handle_download(rc):
    if rc == "2":
        return send_file("userdata.json")
    elif rc == "3":
        listf = []
        with open("userdata.json") as f:
            data = json.load(f)
        for i in data:
            listf.append(data[i]['issue']['severity'])
        udfunc.plot_frequency_graph(listf, 'save_file.png')
        return send_file('save_file.png')
    else:
        abort(404)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
