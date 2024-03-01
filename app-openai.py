import openai
import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('OPENAI_API_KEY')

openai.api_key = API_KEY

MODEL = "gpt-3.5-turbo"

app = Flask(__name__)

PROMPT = """
        You are a proficient social media content generator with expertise in crafting engaging comments. 
        Craft a detailed prompt instructing me to generate comments for social media posts, including text provided by the user. 
        The responses should align with the user's specified requirements or preferences. 
        Highlight your ability to enhance comments by incorporating emojis for added expressiveness, and you should give only one comment in response to the user input.
        Only provide output comment in response no prompt only output
        
        """

def get_OPENAI_response(PROMPT, USER_INPUT):
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": USER_INPUT},
        ]
    )
    data1 = dict(response)
    data2 = dict(data1['choices'][0])
    data3 = dict(data2['message'])

    return data3['content']

comments_dict = {}

@app.route('/check_connection', methods=['POST'])
def check_connection():
    data = request.get_json()
    message = data.get('message', '')
    if message == "Is the connection good?":
        return jsonify({"message": "Connection is good"})
    else:
        return jsonify({"error": "Invalid request"})

@app.route('/put_comments_queue', methods=['POST'])
def put_comments_queue():
    data = request.get_json()
    descriptions_list = data.get('descriptions_list', [])
    
    for description in descriptions_list:
        comment = get_OPENAI_response(PROMPT, description['post_description'])
        comments_dict[description['id']] = comment
    
    return jsonify({"message": "Descriptions put to queue"})

@app.route('/get_created_comments', methods=['POST'])
def get_created_comments():
    data = request.get_json()
    ids_list = data.get('ids_list', [])
    
    results_list = []
    for item in ids_list:
        comment = comments_dict.get(item['id'])
        if comment:
            print(comment)
            results_list.append({"id": item['id'], "comment": comment})
    
    return jsonify({"results_list": results_list})

if __name__ == '__main__':
    app.run(debug=True)
    


