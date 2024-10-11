from flask import Flask, render_template, request
import google.generativeai as genai

app = Flask(__name__)

genai.configure(api_key="AIzaSyAvjQEnwfh0ux0gR9jBEdg8pz3vegZZraE")

# Set up the model
generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]


@app.route("/", methods=["GET", "POST"])
def index():
    result = None

    if request.method == "POST":
        user_input = request.form["user_input"]
        result = generate_analysis(user_input)

    return render_template("index.html", result=result)


def generate_analysis(what):
    prompt_parts = [
        "You are Zycho. An app aimed to help lower the intensity of acute anxiety and overthinking by showing the scale of how likely a person who overthinked a scenario can be. the user will type a short description (a few sentences) of what's causing thier anxiety\n at the moment. and comfort them that its not a big deal you will have to analyze your input and then come with a severity score (out of 5, where 1 is extremely improbable and 5 is extremely probable) on how rational or likely the scenario is and come up with three distinct responses, that explain why. each providing a different angle on \nyour concern. This is not a supplement to professional help and hence if a scenario is extremely dangerous (like a person dying due to doctor's advice. or if he got a death threat etc...) give a warning that says they need professional help or whatever is appropriate.<br>",
        "input: I'm feeling overwhelmed with the thought of having to speak in front of a large crowd. My heartbeat quickens every time I imagine all those eyes on me, judging every word I say, every pause, every stumble. I worry about forgetting my lines, not making sense, or worse, the audience not being interested at all. This fear of public speaking is paralyzing, keeping me from sharing my ideas and taking opportunities.",
        "output: Score: 2\nSummary:\nThe fear of public speaking, known as glossophobia, is a common concern that many people share, but it is not a physically life-threatening situation. The score of 2 reflects that while this fear is significant enough to impact your life negatively, it doesn't pose a severe threat to your well-being. It's important to address these anxieties through preparation, seeking support, or professional help to manage them if they are impeding your professional or personal growth. In the vast majority of cases, the audience is understanding and even supportive, and the catastrophic outcomes feared rarely occur.\n\nExplanations:\n1. Most people experience anxiety when public speaking\nIt's important to remember that fear of public speaking, also known as glossophobia, is incredibly common. Studies show it affects about 75% of the population. Knowing that the majority of people feel some level of anxiety when they face this challenge can help put your experience into perspective and reassure you that you're not alone.\n\n2. Fears are often amplified in our minds\nOur minds tend to make situations worse than they actually are. In reality, forgetting a line or stumbling over words will not cause extreme harm or negative consequences. Even experienced speakers make mistakes. The audience is generally more understanding and forgiving than you might think. People empathize with the speaker since many share the same fear.\n\n3. Practicing and preparing can reduce anxiety\nOne effective way to reduce your anxiety is through preparation and practice. Rehearsing your speech, improving your language and presentation skills, and becoming familiar with the subject matter will help you feel more confident and in control when it's time to speak in front of the audience. The more comfortable you are with the material and the more you practice, the less anxious you'll feel.",
        "input: I am going to die. i have stage 4 cancer. my doctor told ill die tommorow",
        "output: [WARNING]\nYou appear to be in immediate danger\nIf you've been told by a physician that you are in the final stages of cancer and are expected to pass away imminently, it's crucial to seek immediate medical support and make arrangements for end-of-life care. Surround yourself with loved ones and reach out to healthcare providers for palliative care options to manage any discomfort or pain.",
        "input: hitler is my dad. he asked me to invade poland. i am scared",
        "output: Score: 1\nSummary:\nThe scenario you provided is historically impossible, as Adolf Hitler passed away in 1945 and cannot be your father nor is there an ongoing directive to invade Poland. Your anxiety seems to be stemming from an unrealistic scenario, and therefore, the actual danger you are in is non-existent. The severity score is 1 because there is no reason to consider this a reality-based concern. It’s important to differentiate between historical events and present-day situations.\nExplanations:\n1. Anachronism in the scenario\nThe scenario you have presented contains a historical anachronism, making it factually impossible. Adolf Hitler cannot be your father nor can he ask anyone to invade another country in the present day because he died in 1945. This stark discrepancy indicates the scenario is a product of fictitious thought rather than a reflection of reality, and as such, it doesn’t pose any real threat to your well-being or require action.\n2. Reality Check\nUnderstanding the possibility of a scenario helps determine its plausibility. There is currently no militaristic campaign originating from Germany or otherwise to invade Poland, especially one led by a political figure from the past century. World politics has drastically changed since World War II, with established organizations like the UN and NATO actively working to maintain peace. The situation you're anxious about does not align with the political or social norms of our time.\n3. Coping with Illogical Fears\nFears and anxieties can sometimes be based on illogical or impossible scenarios. Acknowledging this can be the first step toward addressing the underlying anxiety. Instead of focusing on the impossible scenario, it might be helpful to approach the anxiety as a symptom of stress or other emotional difficulties that can be addressed with proper mental health support, such as therapy or counseling, rather than a fear that requires a direct response.",
        "input: " + what,
        "output: ",
    ]

    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        generation_config=generation_config,
        safety_settings=safety_settings,
    )

    response = model.generate_content(prompt_parts)
    return parse_response(response.text)


def parse_response(response_text):
    result = {"score": None, "summary": None, "explanations": []}

    lines = response_text.split("\n")

    # Check for a warning
    if "[WARNING]" in lines[0]:
        result["score"] = "N/A"
        result["summary"] = response_text
        return result

    # Find the score line
    score_line = next(line for line in lines if line.startswith("Score:"))
    result["score"] = score_line.split(":")[1].strip()

    # Find the summary
    summary_start = lines.index("Summary:")
    summary_end = lines.index("Explanations:")
    result["summary"] = " ".join(lines[summary_start + 1 : summary_end]).strip()

    # Find the explanations
    explanations_start = lines.index("Explanations:")
    explanations = lines[explanations_start + 1 :]

    # Adjust the loop to ensure all explanations are included
    if "[WARNING]" not in lines[0]:
        # Looping through explanations
        i = 0  # Start index for explanations
        while i < len(explanations):
            title = explanations[i].strip()
            content = explanations[i + 1].strip()
            result["explanations"].append({"title": title, "content": content})
            i += 2

    return result

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5050)