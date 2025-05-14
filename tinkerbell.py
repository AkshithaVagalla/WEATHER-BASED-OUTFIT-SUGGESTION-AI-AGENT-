import gradio as gr
import google.generativeai as genai
import requests
import datetime
from diffusers import StableDiffusionPipeline
import torch

# --- API KEYS ---
genai.configure(api_key="...............................................")
weather_api_key = "........................................"  # OpenWeatherMap

# --- Device and dtype configuration ---
device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.float16 if device == "cuda" else torch.float32

# --- Load Dreamlike Photoreal 2.0 ---
pipe = StableDiffusionPipeline.from_pretrained(
    "dreamlike-art/dreamlike-photoreal-2.0",
    torch_dtype=dtype,
    safety_checker=None
).to(device)

# --- Weather Helper ---
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

def time_of_day():
    hour = datetime.datetime.now().hour
    if 6 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "afternoon"
    else:
        return "evening"

# --- Outfit Generator ---
def get_outfits_and_skincare(temp, condition, name, time_of_day, is_trip=False):
    model = genai.GenerativeModel("gemini-1.5-pro-latest")

    prompt = f"""
    Assume you are a stylish virtual fashion expert.

    Weather: {temp}°C, {condition}
    User: {name}
    Time: {time_of_day}
    Trip: {is_trip}

    Generate:
    - 3 streetwear outfits with Top, Bottom, Footwear, Accessory (optional), and poetic caption.
    - 1 "Look of the Day" with name + description.
    - 1 skincare tip related to weather.

    Format:
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

# --- Image Generator ---
def generate_image(prompt_text):
    try:
        result = pipe(prompt_text)
        image = result.images[0]
        image_path = "outfit_image.png"
        image.save(image_path)
        return image_path
    except Exception as e:
        print(f"Image generation failed: {e}")
        return None

# --- Main Suggestion Function ---
def suggest_fits(city, name, is_trip):
    temp, condition = get_weather(city)
    if temp is None:
        return "Couldn't fetch weather data. Try another city.", "", "", "", "", "", None

    tod = time_of_day()
    raw = get_outfits_and_skincare(temp, condition, name, tod, is_trip)
    outfit1, outfit2, outfit3, look, skincare = parse_response(raw)

    weather_display = f"🌡 {temp}°C | 🌦 {condition}"
    return weather_display, outfit1, outfit2, outfit3, look, skincare, None

# --- Image Trigger ---
def image_from_caption(outfit1_text):
    try:
        caption = outfit1_text.splitlines()[-1]
        if not caption.strip():
            caption = "a stylish streetwear outfit, photorealistic"
    except:
        caption = "a stylish streetwear outfit, photorealistic"
    return generate_image(caption)

# --- Gradio UI ---
with gr.Blocks(theme=gr.themes.Monochrome()) as app:
    gr.Markdown("## 👗 **FitCast ✨** — Your AI Style Concierge\n*Fashion. Weather. Charm.*")
    gr.Markdown("> *Stay elegantly prepared — rain or shine.*")

    with gr.Row():
        city = gr.Textbox(label="🏙️ Enter your City", placeholder="e.g., Tokyo")
        name = gr.Textbox(label="🧍 Your Name", placeholder="e.g., Akshitha")
        is_trip = gr.Checkbox(label="🎒 Going on a Trip?")

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
    image_output = gr.Image(label="🖼️ Outfit Preview")

    gen_img_btn = gr.Button("🎨 Generate Outfit Image")

    # UX: Show placeholder while processing
    get_btn.click(
        fn=lambda: ("Fetching fashion forecast...", "", "", "", "", "", None),
        outputs=[weather_info, outfit1, outfit2, outfit3, look_day, skincare, image_output]
    ).then(
        fn=suggest_fits,
        inputs=[city, name, is_trip],
        outputs=[weather_info, outfit1, outfit2, outfit3, look_day, skincare, image_output]
    )

    # Image generation triggered manually
    gen_img_btn.click(
        fn=image_from_caption,
        inputs=[outfit1],
        outputs=[image_output]
    )

app.launch()




