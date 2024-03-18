import openai
import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import threading
import time
import schedule

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

LOG_FILE = "logs.txt"

def log_to_file(message):
    with open(LOG_FILE, "a") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

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
comments_lock = threading.Lock()

def clear_old_comments():
    global comments_dict
    current_time = time.time()
    with comments_lock:
        for key, value in list(comments_dict.items()):
            if current_time - value['timestamp'] >= 10800:
                del comments_dict[key]
                log_to_file(f"Comment {key} deleted.")
        log_to_file("Old comments cleared.")

threading.Thread(target=clear_old_comments, daemon=True).start()

@app.route('/check_connection', methods=['POST'])
def check_connection():
    log_to_file("API hit: /check_connection")
    try:
        data = request.get_json()
        message = data.get('message', '')
        if message == "Is the connection good?":
            return jsonify({"message": "Connection is good"})
        else:
            return jsonify({"error": "Invalid request"})
    except Exception as e:
        log_to_file(f"Error in /check_connection endpoint: {str(e)}")
        return jsonify({"error": "An error occurred"}), 500

@app.route('/put_comments_queue', methods=['POST'])
def put_comments_queue():
    log_to_file("API hit: /put_comments_queue")
    try:
        data = request.get_json()
        descriptions_list = data.get('descriptions_list', [])
        
        for description in descriptions_list:
            comment = get_OPENAI_response(PROMPT, description['post_description'])
            with comments_lock:
                comments_dict[description['id']] = {'comment': comment, 'timestamp': time.time()}
        log_to_file("Comments queued.")
        return jsonify({"message": "Descriptions put to queue"})
    except Exception as e:
        log_to_file(f"Error in /put_comments_queue endpoint: {str(e)}")
        return jsonify({"error": "An error occurred"}), 500

@app.route('/get_created_comments', methods=['POST'])
def get_created_comments():
    log_to_file("API hit: /get_created_comments")
    try:
        data = request.get_json()
        ids_list = data.get('ids_list', [])
        
        results_list = []
        with comments_lock:
            for item in ids_list:
                comment_data = comments_dict.get(item['id'])
                if comment_data:
                    results_list.append({"id": item['id'], "comment": comment_data['comment']})
        
        return jsonify({"results_list": results_list})
    except Exception as e:
        log_to_file(f"Error in /get_created_comments endpoint: {str(e)}")
        return jsonify({"error": "An error occurred"}), 500

@app.route('/get_message_count',methods=['POST','GET'])
def get_message_count():
    log_to_file("API hit: /get_message_count")
    try:
        data = request.get_json()
        ques = data.get('message','')
        if ques == "How many generated messages you have now?":
            with comments_lock:
                msg_count = len(comments_dict)
            temp = {"message":f"I have {msg_count} messages now"}
            return jsonify(temp)
    except Exception as e:
        log_to_file(f"Error in /get_message_count endpoint: {str(e)}")
        return jsonify({"error": "An error occurred"}), 500

    
schedule.every(10800).seconds.do(clear_old_comments)

def schedule_thread():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Creating a separate thread for the schedule
schedule_thread = threading.Thread(target=schedule_thread)
schedule_thread.daemon = True
schedule_thread.start()

if __name__ == '__main__':
    app.run(debug=True)
