from flask import Flask
from flask import render_template
from flask import Response, request, jsonify
app = Flask(__name__)

#for gpt
import os
import openai

import api_key
openai.api_key = api_key.SECRET_KEY

#for dalle
import json
from base64 import b64decode
from pathlib import Path


#This is the basic data representation
recipe_data = {
  "ingredients":[],
  "keywords":[],
  "recipes":[]
}

# This is what the representation looks like when there is a food and a recipe generated
# sample_recipe_data = {
#    "ingredients": ["eggs", "flour", "salt", "sugar", "vanilla extract"],
#    "keywords": ["easy"],
#    "recipes": [{"ingredients": ["eggs", "flour", "salt", "sugar", "vanilla extract"], "keywords": ["easy"], "food": "vanilla cake", "recipe": "step 1, step 2, etc."}]
# }

sample_recipe_data_1 = {
    "ingredients": ["eggs", "flour", "salt", "sugar", "vanilla extract"],
    "keywords": ["hard", "fun"],
    "recipes": []
}

#### INIT with example data
# recipe_data = sample_recipe_data_1


@app.route('/submit', methods=['GET', 'POST'])
def submit():
    global recipe_data
    data = request.get_json()   

    recipe_data["ingredients"] = data["ingredients"]
    recipe_data["keywords"] = data["keywords"]
    
    keywords = recipe_data["keywords"]

    food = get_food(recipe_data["ingredients"])
    recipe = get_recipe(food, keywords)
    image_url = get_image(food)

    recipe_data["recipes"].append({"ingredients": recipe_data["ingredients"], "keywords": recipe_data["keywords"], "food": food, "recipe": recipe, "image": image_url})

    return jsonify(recipe_data)

# First call: gets the type of food
def get_food(ingredients):
    prompt = "I have these ingredients: " + ", ".join(ingredients) + ". What is a food I can make from these ingredients? Do not give me a recipe, just the name like so: 'vanilla pancakes'"
    food = openai.Completion.create(engine="text-davinci-003", prompt=prompt, max_tokens=256)

    return food["choices"][0]["text"].strip()
    
# Second call: gets a recipe from the type of food generated
def get_recipe(food, keywords):
    prompt = "What is a " + ", ".join(keywords) + "recipe for " + food + "? Please only list ingredients, tools, and steps. Do not give me extra statements like 'Certainly! Here's a medium difficulty recipe for a vanilla cake.' Please just give me the recipe. Do not add any extra statements after the steps are listed."
    recipe = openai.Completion.create(engine="text-davinci-003", prompt=prompt, max_tokens=256)

    return recipe["choices"][0]["text"].strip()

# Third call: gets an image from the type of food generated
def get_image(food):
    response = openai.Image.create(prompt=food, n=1, size="256x256", response_format="b64_json")

    # Make a json file to represent the generated image
    DATA_DIR = Path.cwd() / "image_responses"
    DATA_DIR.mkdir(exist_ok=True)
    JSON_FILE = DATA_DIR / f"{food[:10]}--{response['created']}.json"
    with open(JSON_FILE, mode="w", encoding="utf-8") as file:
        json.dump(response, file)

    # Change the json image into a png
    IMAGE_DIR = Path.cwd() / "static/recipe_images" / JSON_FILE.stem
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    with open(JSON_FILE, mode="r", encoding="utf-8") as file:
        image_response = json.load(file)

    for index, image_dict in enumerate(image_response["data"]):
        image_data = b64decode(image_dict["b64_json"])
        image_file = IMAGE_DIR / f"{JSON_FILE.stem}--{index}.png"

        with open(image_file, mode="wb") as png:
            png.write(image_data)

    path_to_image = image_file.as_posix()
    url_for_flask = path_to_image[path_to_image.find('static'):]

    return path_to_image[path_to_image.find('static'):]

@app.route('/')
def home():
    print(recipe_data)
    return render_template('home.html', data=recipe_data)   

if __name__ == '__main__':
    # app.run(debug = True, port = 4000)    
    app.run(debug = True)



