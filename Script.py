import os
import openai
import requests
import io
import json
import random
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from instagrapi import Client

# Load API keys and credentials from environment variables
openai.api_key = os.getenv('OPENAI_API_KEY')
huggingface_api_key = os.getenv('HUGGINGFACE_API_KEY')
instagram_username = os.getenv('INSTAGRAM_USERNAME')
instagram_password = os.getenv('INSTAGRAM_PASSWORD')

API_URLS = [
    "https://api-inference.huggingface.co/models/Corcelio/openvision",
    "https://api-inference.huggingface.co/models/DoctorDiffusion/doctor-diffusion-s-stylized-silhouette-photography-xl-lora",
    "https://api-inference.huggingface.co/models/Artples/LAI-ImageGeneration-vSDXL-2",
    "https://api-inference.huggingface.co/models/prompthero/openjourney"
]
headers = {"Authorization": f"Bearer {huggingface_api_key}"}

def process_image_with_text(image_bytes, title, fade_factor=0.4):
    image = Image.open(io.BytesIO(image_bytes))
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(fade_factor)
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("PPE.ttf", 40)
    except IOError:
        font = ImageFont.load_default()

    image_width, image_height = image.size

    def get_text_size(text, font):
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    max_width = image_width * 0.8
    title_lines = [title]

    if get_text_size(title, font)[0] > max_width:
        words = title.split()
        first_line = ""
        second_line = ""
        sl = 0
        for word in words:
            if get_text_size(first_line + word + ' ', font)[0] <= max_width and sl == 0:
                first_line += word + ' '
            else:
                second_line += word + ' '
                sl = 1
        title_lines = [first_line.strip(), second_line.strip()]

    total_text_height = sum(get_text_size(line, font)[1] for line in title_lines) + (len(title_lines) - 1) * 10
    y = (image_height - total_text_height) / 2

    for line in title_lines:
        text_width, text_height = get_text_size(line, font)
        x = (image_width - text_width) / 2
        draw.text((x, y), line, font=font, fill=(255, 255, 255))
        y += text_height + 10

    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()

MAX_RETRY_ATTEMPTS = 5
def query(payload, retry_count=0):
    if retry_count >= MAX_RETRY_ATTEMPTS:
        with open("fileDemp.jpeg", "rb") as image_file:
            return image_file.read()
    url = random.choice(API_URLS)
    response = requests.post(url, headers=headers, json=payload)
    image_bytes = response.content

    if len(image_bytes) <= 1024:
        return query(payload, retry_count + 1)
    else:
        return image_bytes

motivation_types = [
    "Fitness and Health",
    "Career and Professional Development",
    "Academic and Educational",
    "Personal Growth and Self-Improvement",
    "Financial and Wealth Management",
    "Entrepreneurship and Business",
    "Relationships and Social Connections",
    "Mindfulness and Mental Health",
    "Creativity and Artistic Pursuits",
    "Environmental and Social Causes",
    "Sports and Athletic Achievements",
    "Spiritual and Philosophical Growth",
    "Time Management and Productivity",
    "Overcoming Challenges and Resilience",
    "Community Service and Volunteering"
]

selected_motivation = random.choice(motivation_types)
prompt = f'''
You have to give me a structure like this
{{
    "title" : <Some motivation related title for {selected_motivation}>,
    "prompt" : <Image prompt related to the title for {selected_motivation}>,
}}

Remember , the title can be anything you make or anything popular already said by any scholar or phillosopher . Just give the asked format , nothing else. The prompt need to be some thing subtle as it is going to be the bacckground image of the title. ex. for a gym motivation , a guy lifting weights , but motivation can be of any kind like love,career,business,etc.
You can in some images but dont go for mountains more , lifestyle would be fine.the titles should touch heart , striking and have depth to it. you can use already availble quotes.
'''

response = openai.Completion.create(
    engine="gpt-4-turbo",
    prompt=prompt,
    max_tokens=100,
    temperature=0.7
)

obj_response = json.loads(response.choices[0].text.strip())
image_bytes = query({"inputs": obj_response["prompt"]})
final_image_bytes = process_image_with_text(image_bytes, obj_response["title"])

image_path = f"file{random.randint(1,10000)}.jpg"
with open(image_path, "wb") as image_file:
    image_file.write(final_image_bytes)

cl = Client()
cl.login(instagram_username, instagram_password)
media = cl.photo_upload(path=image_path, caption=obj_response['title'])
