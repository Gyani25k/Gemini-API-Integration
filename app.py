import os
from flask import Flask, request, jsonify
import google.generativeai as genai
import threading
import time
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('GEMINI_API_KEY')

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel('gemini-pro')

app = Flask(__name__)

PROMPT = """
        You are a proficient social media content generator with expertise in crafting engaging comments. 
        Craft a detailed prompt instructing me to generate comments for social media posts, including text provided by the user. 
        The responses should align with the user's specified requirements or preferences. 
        Highlight your ability to enhance comments by incorporating emojis for added expressiveness and you should give only one comment in response to the user input.
        Only provide output comment in response no prompt only output
        
        """

def get_gemini_response(input, user_prompt):
    response = model.generate_content([input, user_prompt])
    return response.text

comments_dict = {}

comments_lock = threading.Lock()

def clear_old_comments():
    while True:
        time.sleep(3 * 3600) 
        with comments_lock:
            current_time = time.time()
            old_comments = [key for key, timestamp in comments_dict.items() if current_time - timestamp >= 3 * 3600]
            for key in old_comments:
                del comments_dict[key]
            print(f"{len(old_comments)} comments deleted!")

threading.Thread(target=clear_old_comments, daemon=True).start()


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
        comment = get_gemini_response(PROMPT, description['post_description'])
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

@app.route('/get_message_count',methods=['POST','GET'])
def get_message_count():
    try:
        data = request.get_json()
        ques = data.get('message','')
        if ques == "How many generated messages you have now?":
            msg_count = len(comments_dict)
            temp = {"message":f"I have {msg_count} messages now"}
            return jsonify(temp)
    except Exception as e:
        temp = {"message":str(e)}
        return jsonify(temp)
    

if __name__ == '__main__':
    app.run(debug=True)
