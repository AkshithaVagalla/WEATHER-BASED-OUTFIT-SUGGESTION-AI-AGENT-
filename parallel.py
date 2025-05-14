import requests
import random
from datetime import datetime
import os
import pandas as pd
import gradio as gr

# Directory containing the images
image_dir = r"C:\Users\Akshitha\OneDrive\small projects -AI\weather agent\myntradataset\images"
csv_file = r"C:\Users\Akshitha\OneDrive\small projects -AI\weather agent\myntradataset\styles.csv"

# Load the CSV file into a DataFrame
try:
    styles_df = pd.read_csv(csv_file, engine='python', on_bad_lines='skip')
    print("✅ CSV loaded successfully!")
except Exception as e:
    print(f"❌ Error loading CSV: {e}")
    exit()

# Check required columns
required_columns = ['id', 'productDisplayName', 'season']
if not all(col in styles_df.columns for col in required_columns):
    print(f"❌ Missing columns in CSV. Required: {required_columns}")
    exit()

# Function to fetch real weather data using WeatherAPI (free version)
def get_weather_data(city):
    base_url = "http://api.weatherapi.com/v1/current.json"
    api_key = "...................................................."  # Replace with your WeatherAPI key
    params = {
        'q': city,
        'key': api_key
    }
    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        if response.status_code == 200:
            temp = data['current']['temp_c']
            condition = data['current']['condition']['text']
            return temp, condition
        else:
            print(f"⚠️ WeatherAPI Error: {data.get('error', {}).get('message', 'Unknown error')}")
            return None, None
    except Exception as e:
        print(f"❌ Failed to fetch weather: {e}")
        return None, None

# Function to fetch image path and description for each outfit
def get_image_and_description(outfit_id):
    # You can adapt this function based on your CSV data
    # Assuming the CSV contains columns like 'id', 'productDisplayName', and 'imagePath'
    
    outfit = styles_df[styles_df['id'] == outfit_id].iloc[0]
    image_path = os.path.join(image_dir, outfit['id'] + ".jpg")  # Adjust file extension if needed
    description = outfit['productDisplayName']
    
    return image_path, description

# Other functions (skincare recommendations, greeting, etc.) remain the same

# Main function
def suggest_fits(city, name):
    # Fetch real weather data
    temp, condition = get_weather_data(city)
    if temp is None or condition is None:
        # Fallback to random values if API fails
        temp = random.randint(10, 35)
        condition = random.choice(["Sunny", "Cloudy", "Rainy", "Stormy", "Snowy"])
        weather_display = f"⚠️ Couldn't fetch weather for {city}. Showing random recommendations: {condition} | 🌡 {temp}°C"
    else:
        weather_display = f"🌦 {condition} in {city} | 🌡 {temp}°C"

    # Get season (same as before)
    current_month = datetime.now().month
    if 3 <= current_month <= 5:
        season = "Spring"
    elif 6 <= current_month <= 8:
        season = "Summer"
    elif 9 <= current_month <= 11:
        season = "Fall"
    else:
        season = "Winter"
    weather_display += f" | 🍂 {season}"

    # Filter outfits based on weather (same logic)
    if temp > 25:
        suitable_outfits = styles_df[styles_df['season'] == 'Summer']
    elif temp < 15:
        suitable_outfits = styles_df[styles_df['season'] == 'Winter']
    else:
        suitable_outfits = styles_df[styles_df['season'] == 'Fall'] if season == "Spring" else styles_df[styles_df['season'] == season]
    
    if len(suitable_outfits) < 3:
        suitable_outfits = styles_df
    
    # Randomly pick 3 outfits
    try:
        outfit_numbers = random.sample(list(suitable_outfits['id']), 3)
    except ValueError:
        outfit_numbers = random.sample(list(styles_df['id']), 3)
    
    # Fetch images and descriptions
    outfit1_image_path, outfit1_desc = get_image_and_description(outfit_numbers[0])
    outfit2_image_path, outfit2_desc = get_image_and_description(outfit_numbers[1])
    outfit3_image_path, outfit3_desc = get_image_and_description(outfit_numbers[2])
    
    # Skincare and greeting
    skincare = get_skincare_recommendation(temp, condition)
    greeting = f"Hello {name}! Here are your personalized recommendations:"
    
    return (greeting, weather_display, outfit1_desc, outfit2_desc, outfit3_desc, 
            skincare, outfit1_image_path, outfit2_image_path, outfit3_image_path)

# Gradio Interface (same as before)
with gr.Blocks(theme=gr.themes.Soft()) as app:
    gr.Markdown(""" 
    # 👗 **FitCast** ✨  
    *Your AI Style & Skincare Concierge*  
    *Fashion. Weather. Skincare. All in One.*
    """)
    with gr.Row():
        with gr.Column(scale=1):
            city = gr.Textbox(label="🏙️ Enter your City", placeholder="e.g., Tokyo")
            name = gr.Textbox(label="🧍 Your Name", placeholder="e.g., Akshitha")
            get_btn = gr.Button("✨ Get My Recommendations", variant="primary")
        with gr.Column(scale=2):
            greeting = gr.Textbox(label="👋 Greeting", interactive=False)
            weather_info = gr.Textbox(label="🌦 Weather Info", interactive=False)
            skincare = gr.Textbox(label="🧴 Skincare Tips", interactive=False, lines=3)
    with gr.Tabs():
        with gr.Tab("👒 Outfit 1"):
            outfit1_image = gr.Image(label="Outfit 1", type="filepath", height=400)
            outfit1 = gr.Textbox(label="Description", interactive=False)
        with gr.Tab("🧣 Outfit 2"):
            outfit2_image = gr.Image(label="Outfit 2", type="filepath", height=400)
            outfit2 = gr.Textbox(label="Description", interactive=False)
        with gr.Tab("🕶 Outfit 3"):
            outfit3_image = gr.Image(label="Outfit 3", type="filepath", height=400)
            outfit3 = gr.Textbox(label="Description", interactive=False)
    get_btn.click(
        fn=suggest_fits,
        inputs=[city, name],
        outputs=[greeting, weather_info, outfit1, outfit2, outfit3, skincare, 
                 outfit1_image, outfit2_image, outfit3_image]
    )

app.launch(share=True)  # This will create a public link

