import gradio as gr
import google.generativeai as genai
import requests
import random

# Configure Gemini API
genai.configure(api_key="..................................")  # Replace with your Gemini API Key

# OpenWeatherMap API
weather_api_key = "......................................."  # Replace with your OpenWeatherMap Key

# Get weather data for city
def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={weather_api_key}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        temp = data["main"]["temp"]
        condition = data["weather"][0]["description"]
        return round(temp), condition.capitalize()
    else:
        return None, None

# Generate outfits and skincare based on weather
def get_outfits_and_skincare(temp, condition, name):
    model = genai.GenerativeModel("gemini-1.5-pro-latest")

    prompt = f"""
    Assume you are an elite personal fashion assistant trained in global trends, weather relevance, and user charm.

    Weather is {temp}°C with {condition}. User's name is {name}.
    
    Respond in refined, warm tone. No repetition of words across outputs.

    Generate 3 stylish, non-redundant and weather-appropriate streetwear outfits:
    - Top
    - Bottom
    - Footwear
    - Optional Accessory
    - Fashion caption (like Instagram with poetic tone)

    Also:
    - Suggest 1 “Look of the Day” with a stylish name and short refined description.
    - Give a thoughtful skincare tip specific to the weather.

    Output format:
    ## Outfit 1
    ...

    ## Outfit 2
    ...

    ## Outfit 3
    ...

    ## Look of the Day
    Name: ...
    Description: ...

    ## Skincare Tip
    ...
    """

    response = model.generate_content(prompt)
    return response.text if response.text else "Sorry, I couldn't generate fashion ideas."

# Parser to extract data from Gemini response
def parse_response(text):
    def extract_block(title):
        start = text.find(f"## {title}")
        if start == -1:
            return "Not found"
        end = text.find("##", start + 5)
        return text[start:end].strip() if end != -1 else text[start:].strip()

    outfit1 = extract_block("Outfit 1")
    outfit2 = extract_block("Outfit 2")
    outfit3 = extract_block("Outfit 3")
    look = extract_block("Look of the Day")
    skincare = extract_block("Skincare Tip")
    
    return outfit1, outfit2, outfit3, look, skincare

# Combined function for UI
def suggest_fits(city, name):
    temp, condition = get_weather(city)
    if temp is None:
        return "Couldn't fetch weather data. Try another city.", "", "", "", "", ""

    raw = get_outfits_and_skincare(temp, condition, name)
    outfit1, outfit2, outfit3, look, skincare = parse_response(raw)

    weather_display = f"🌡 **{temp}°C** | 🌦 **{condition}**"
    return weather_display, outfit1, outfit2, outfit3, look, skincare

# Gradio UI
with gr.Blocks(theme=gr.themes.Monochrome()) as app:
    gr.Markdown("## 👗 **FitCast ✨** — Your AI Style Concierge\n*Fashion. Weather. Charm.*")
    gr.Markdown("> *Stay elegantly prepared — rain or shine.*")

    with gr.Row():
        city = gr.Textbox(label="🏙️ Enter your City", placeholder="e.g., Tokyo")
        name = gr.Textbox(label="🧍 Your Name", placeholder="e.g., Akshitha")

    get_btn = gr.Button("✨ Get My Weather Fit")

    weather_info = gr.Textbox(label="🌦 Weather Info", interactive=False)

    with gr.Tab("👒 Outfit 1"):
        outfit1 = gr.Textbox(label="", lines=6, interactive=False)

    with gr.Tab("🧣 Outfit 2"):
        outfit2 = gr.Textbox(label="", lines=6, interactive=False)

    with gr.Tab("🕶 Outfit 3"):
        outfit3 = gr.Textbox(label="", lines=6, interactive=False)

    look_day = gr.Textbox(label="🌟 Look of the Day", lines=3, interactive=False)
    skincare = gr.Textbox(label="🧴 Skincare Tip", lines=2, interactive=False)

    get_btn.click(fn=suggest_fits, inputs=[city, name],
                  outputs=[weather_info, outfit1, outfit2, outfit3, look_day, skincare])

# Run the app
app.launch()


