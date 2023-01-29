from flask import Flask, render_template, request, redirect  # add request & redirect
import pandas as pd
import os
import openai
import translators as ts
import translators.server as tss
from sqlalchemy import create_engine


def get_recipe(food_to_make):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    ai_response = openai.Completion.create(
    model="text-davinci-003",
    prompt="How to cook " + food_to_make,
    max_tokens=1000,
    temperature=0
    )
    ai_choices = ai_response.choices
    return ai_choices[0]["text"]


def get_stuff_ai(ing_text_response):

    from_language, to_language = 'en', 'cs'
    ingredience_cz = tss.google(ing_text_response, from_language, to_language)

    mat = [n.split('\n') for n in ingredience_cz]

    ingr = [line.split(",") for line in ingredience_cz.strip().split("\n")]
    ingr = ingr[1:]

    ingr_tf = list()
    for ingredience in ingr:
        ingredience = ingredience[0].strip()
        ingredience = ingredience[1:]
        ingr_tf.append(ingredience)
    
    return(ingr_tf)


def get_stuff(recipe):
    list_ingr = get_stuff_ai(recipe)
    dtING = pd.DataFrame({'ingridient': list_ingr})
    dtING_r = pd.DataFrame()
    for index, thing_in in dtING.iterrows():
        if len(thing_in['ingridient']) < 3:
            continue
        closest_prod_q = "select CAST (product_id as varchar) as product_id, product_name, textual_amount, price_amount from rohlik_out.current_product_prices cpp order by SIMILARITY(category_name,'"+thing_in['ingridient']+"')+SIMILARITY(product_name,'"+thing_in['ingridient']+"') desc fetch first 1 rows only;"
        dtCG = pd.read_sql_query(closest_prod_q, engine)
        dtCG['ingridient'] = thing_in['ingridient']
        #dtCG['product_id'] = dtCG['product_id'].to_string()
        dtCG['rohlik_link'] = "https://www.rohlik.cz/" + str(dtCG['product_id'][0])
        #dtCG['product_id'].to_string()
        dtCG['price'] = str(dtCG['price_amount'][0]) + " CZK"
        dtING_r = pd.concat([dtING_r, dtCG])

    return dtING_r

engine = create_engine("")# DB connection string
conn = engine.connect()
    
app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    groceries = pd.DataFrame()
    if request.method == 'POST':
        thing_to_be_cooked = request.form['thing_to_be_cooked']
        recipe = get_recipe(thing_to_be_cooked)
        s_recipe = recipe.split("Instructions:")
        groceries = get_stuff(s_recipe[0])
        return render_template('index.html', groceries=groceries, instructions = s_recipe[1])

    else:
        
        return render_template('index.html', groceries=pd.DataFrame())


if __name__ == '__main__':
    app.run(debug=True)