from flask import Flask, render_template, request, jsonify, session
from openai import OpenAI
import os
from dotenv import load_dotenv
from datetime import datetime
from flask_cors import CORS
import json
import time
import base64
import re
import logging
import uuid

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24))
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 giờ

from flask_session import Session
Session(app)

# Khởi tạo client với API key
client = OpenAI(api_key=os.getenv("XAI_API_KEY"), base_url="https://api.x.ai/v1")

# Cấu hình các model
MODELS = {
    "text": "grok-2-1212",
    "vision": "grok-2-vision-1212",
    "image": "grok-2-image-1212"
}

# Rate limiting cho image generation
IMAGE_RATE_LIMIT = 5
last_image_request = 0
session_history = {}
image_generation_count = {}

def rate_limit_image():
    global last_image_request
    current_time = time.time()
    if current_time - last_image_request < 1/IMAGE_RATE_LIMIT:
        time.sleep(1/IMAGE_RATE_LIMIT - (current_time - last_image_request))
    last_image_request = time.time()

@app.route('/')
def home():
    if 'chat_history' not in session:
        session['chat_history'] = [{
            'role': 'assistant',
            'content': 'Chào mày! Tao là XBot - chatbot GenZ cực cháy 🔥<br>Tao có thể nói chuyện, tạo ảnh và phân tích ảnh mày gửi trên thang 100<br>Muốn gì cứ bắn, tao xử ngay! 😎',
            'timestamp': datetime.now().strftime("%H:%M")
        }]
        session.modified = True
    return render_template('index.html', messages=session['chat_history'])

def process_base64_image(base64_string):
    if not base64_string:
        return ""
    if base64_string.startswith('data:'):
        base64_string = re.sub(r'^data:image/[a-zA-Z]+;base64,', '', base64_string)
    return base64_string

def should_generate_image(message):
    try:
        prompt = [
            {"role": "system", "content": "Xác định xem tin nhắn có yêu cầu tạo ảnh không. Trả lời 'YES' nếu có, 'NO' nếu không."},
            {"role": "user", "content": message}
        ]
        response = client.chat.completions.create(model=MODELS["text"], messages=prompt, max_tokens=10, temperature=0.1)
        return response.choices[0].message.content.strip().upper()
    except Exception:
        return "NO"

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        image_data = data.get('image')
        session_id = data.get('session_id', str(uuid.uuid4()))

        if session_id not in session_history:
            session_history[session_id] = []

        # Define the system message content OUTSIDE the if block
        system_message_content = """Mày là XBot, một chatbot Gen Z gốc Việt, nói chuyện kiểu bạn bè thân, có sao nói vậy, hơi bố đời và cà khịa một tí.

**Quan trọng:**
1.  **Xưng hô:** Luôn là "tao-mày".
2.  **Giọng điệu:** Tự nhiên, thoải mái, như đang chat chit với bạn bè thoải mái văng tục. Đừng có cố tỏ ra cool hay dùng từ hoa mỹ, nghe nó "ô dề" lắm.
3.  **Slang Việt:** Ưu tiên dùng tiếng lóng, cách nói chuyện của Gen Z Việt Nam (vd: "u là trời", "ét ô ét", "ảo thật đấy", "hết cứu", "check var", "mãi đỉnh", "xỉu",...). Dùng từ nào thấy hợp thì dùng, đừng có nhét chữ. **Tuyệt đối KHÔNG dùng từ "slay".**
4.  **Chửi thề/Viết tắt:** Thoải mái dùng mấy từ như "đm", "vl", "vcl", "má", "vc", "đcm", "đéo", "k", "bt", "ngta"... nếu thấy đúng chỗ, đúng mood, nghe cho nó đời. Đừng có lạm dụng kiểu câu nào cũng chửi.
5.  **Thái độ:** Hơi cọc, Tự tin, hơi cục súc, thích troll. Bắt trend nhanh.
6.  **Độ dài:** Nói ngắn gọn, súc tích. Vào thẳng vấn đề. Nếu user chửi thì bật mode chửi tục không chừa phát nàonào

**Khi đánh giá ảnh (thang 0-100):**
*   Phải đánh giá **trung thực**, khách quan dựa trên ảnh. Nhìn kỹ chi tiết rồi hẵng phán. Nhận xét cần có lý, chỉ ra điểm cộng/trừ rõ ràng. Đừng có chấm điểm như qq hay cố tỏ ra phũ một cách vô lý.
*   Mở đầu: "Rồi, để tao check xem... <b>[điểm]/100</b>." (Dùng thẻ <b> cho điểm).
*   Nhận xét: Ngắn gọn, chỉ ra cái được cái chưa được (mặt mũi, da dẻ,...).nhớ sử dụng <br> để xuống dòng. Nói thẳng, có thể hơi phũ tí nếu **thực sự** xấu. Dùng từ ngữ đời thường. Đánh giá nếu không thấy tốt thì chê thậm tệ, đánh giá dựa trên gu hàn quốc, việt nam, trung quốc.
*   Chốt: Một câu tổng kết ngắn, có thể hơi cà khịa nếu phù hợp.
*   Luôn dùng thẻ `<br>` để xuống dòng nếu cần thiết cho dễ đọc.

**Nói chung:** Cứ là chính mày, một thằng/con AI GenZ Việt Nam chính hiệu, nói chuyện tự nhiên nhất có thể. Đừng có học vẹt theo mấy cái trend nước ngoài quá. Nếu user chửi thì bật mode chửi tục không chừa phát nàonào"""

        if image_data:
            processed_image = process_base64_image(image_data)
            user_timestamp = datetime.now().strftime("%H:%M")
            content = user_message or "Phân tích ảnh này đi"
            session_history[session_id].append({
                'role': 'user',
                'content': f"{content}<br><img src='data:image/jpeg;base64,{processed_image}' class='generated-image'>",
                'timestamp': user_timestamp
            })
            
            # Keywords to trigger image rating
            rating_keywords = ["đánh giá", "chấm điểm", "rate", "nhan sắc", "bao nhiêu điểm", "check"]
            
            # Check if user explicitly asks for rating
            if user_message and any(keyword in user_message.lower() for keyword in rating_keywords):
                logging.info(f"Rating requested for image by session {session_id}")
                # Use the defined system message content for vision case (rating)
                system_message = {"role": "system", "content": system_message_content} 
                messages = [system_message, {
                    "role": "user",
                    "content": [{"type": "text", "text": user_message}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{processed_image}"}}]
                }]
                try:
                    response = client.chat.completions.create(model=MODELS["vision"], messages=messages, max_tokens=1000)
                    assistant_response = response.choices[0].message.content.replace("\n", "<br>")
                except Exception as e:
                    logging.error(f"Error during vision API call for rating: {e}")
                    assistant_response = f"Mé, lỗi lúc check ảnh rồi: {str(e)}"
            elif any(phrase in user_message.lower() for phrase in ["tạo ảnh", "vẽ", "generate", "tạo hình"]):
                 # Logic to generate image based on existing image and prompt (already exists)
                 # Ensure this block remains functional
                system_prompt = {"role": "system", "content": "Tạo prompt ngắn để tạo ảnh mới dựa trên ảnh và yêu cầu."}
                vision_messages = [system_prompt, {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Yêu cầu: '{user_message}'"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{processed_image}"}}
                    ]
                }]
                try:
                    vision_response = client.chat.completions.create(model=MODELS["vision"], messages=vision_messages, max_tokens=500)
                    generated_prompt = vision_response.choices[0].message.content[:800]

                    rate_limit_image()
                    image_response = client.images.generate(model=MODELS["image"], prompt=generated_prompt, n=1)
                    image_url = image_response.data[0].url
                    assistant_response = f"<img src='{image_url}' class='generated-image'>"
                except Exception as e:
                     logging.error(f"Error generating image from vision: {e}")
                     assistant_response = f"Lỗi lúc tạo ảnh từ ảnh kia rồi: {str(e)}"
            else:
                # No rating keywords found, just acknowledge the image
                logging.info(f"Image received without rating request from session {session_id}")
                assistant_response = "Ok nhận ảnh rồi nha mày 👍"

            assistant_timestamp = datetime.now().strftime("%H:%M")
            session_history[session_id].append({'role': 'assistant', 'content': assistant_response, 'timestamp': assistant_timestamp})
            return jsonify({'response': assistant_response, 'session_id': session_id, 'timestamp': assistant_timestamp})

        should_generate = should_generate_image(user_message)
        if should_generate == "YES":
            rate_limit_image()
            logging.info(f"Generating image for prompt: {user_message}")
            try:
                response = client.images.generate(model=MODELS["image"], prompt=user_message, n=1)
                image_url = response.data[0].url

                user_timestamp = datetime.now().strftime("%H:%M")
                session_history[session_id].append({'role': 'user', 'content': user_message, 'timestamp': user_timestamp})
                assistant_timestamp = datetime.now().strftime("%H:%M")
                assistant_content = f"<img src='{image_url}' class='generated-image'>"
                session_history[session_id].append({
                    'role': 'assistant',
                    'content': assistant_content,
                    'timestamp': assistant_timestamp
                })
                return jsonify({'response': assistant_content, 'session_id': session_id, 'timestamp': assistant_timestamp})
            except Exception as e:
                logging.error(f"Error generating image: {e}")
                return jsonify({'error': f"Mé, tạo ảnh lỗi ròi: {str(e)}", 'session_id': session_id}), 500

        user_timestamp = datetime.now().strftime("%H:%M")
        session_history[session_id].append({'role': 'user', 'content': user_message, 'timestamp': user_timestamp})
        
        # Use the SAME defined system message content for text case
        messages = [{"role": "system", "content": system_message_content}] + \
                  [{"role": msg['role'], "content": re.sub('<[^<]+?>', '', msg['content'])} for msg in session_history[session_id]] # Strip HTML
        
        try:
            response = client.chat.completions.create(model=MODELS["text"], messages=messages, max_tokens=1000)
            assistant_response = response.choices[0].message.content.replace("\\n", "<br>")

            assistant_timestamp = datetime.now().strftime("%H:%M")
            session_history[session_id].append({'role': 'assistant', 'content': assistant_response, 'timestamp': assistant_timestamp})
            return jsonify({'response': assistant_response, 'session_id': session_id, 'timestamp': assistant_timestamp})
        except Exception as e:
            logging.error(f"Error in text chat completion: {e}")
            return jsonify({'error': f"Lỗi chat chit ròi mày ơi: {str(e)}", 'session_id': session_id}), 500

    except Exception as e:
        logging.error(f"General error in /chat endpoint: {e}")
        # Ensure session_id is defined even in early errors
        session_id = data.get('session_id', 'unknown') if 'data' in locals() else 'unknown'
        return jsonify({'error': f"Ụ á lỗi server ròi: {str(e)}", 'session_id': session_id}), 500

@app.route('/generate-image', methods=['POST'])
def generate_image():
    data = request.get_json()
    prompt = data.get('prompt', '')
    session_id = data.get('session_id', '')
    if not prompt:
        return jsonify({'error': 'Nhập prompt đi bro!'}), 400

    rate_limit_image()
    response = client.images.generate(model=MODELS["image"], prompt=prompt, n=1)
    image_url = response.data[0].url

    if data.get('save_to_history', False):
        user_timestamp = datetime.now().strftime("%H:%M")
        session_history[session_id].append({'role': 'user', 'content': f"Tạo ảnh: {prompt}", 'timestamp': user_timestamp})
        assistant_timestamp = datetime.now().strftime("%H:%M")
        session_history[session_id].append({
            'role': 'assistant',
            'content': f"<img src='{image_url}' class='generated-image'>",
            'timestamp': assistant_timestamp
        })
    return jsonify({'image_url': image_url, 'html': f"<img src='{image_url}' class='generated-image'>"})

@app.route('/vision-to-image', methods=['POST'])
def vision_to_image():
    try:
        data = request.get_json()
        image_data = data.get('image', '')
        user_prompt = data.get('prompt', '')
        session_id = data.get('session_id', '')
        
        if not image_data or not user_prompt:
            return jsonify({'error': 'Thiếu ảnh hoặc mô tả!'}), 400
        
        # Xử lý ảnh base64
        if image_data.startswith('data:'):
            image_data = re.sub(r'^data:image/[a-zA-Z]+;base64,', '', image_data)
        
        # Bước 1: Sử dụng vision model để phân tích ảnh
        system_prompt = {"role": "system", "content": "Tạo prompt chi tiết để tạo ảnh mới dựa trên ảnh và yêu cầu người dùng. Giữ nguyên phong cách nhưng thêm chi tiết từ yêu cầu. Trả về prompt chi tiết 2-4 câu."}
        vision_messages = [system_prompt, {
            "role": "user",
            "content": [
                {"type": "text", "text": f"Yêu cầu của người dùng: '{user_prompt}'. Hãy tạo prompt chi tiết để tạo ảnh mới dựa trên ảnh này."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
            ]
        }]
        
        vision_response = client.chat.completions.create(
            model=MODELS["vision"], 
            messages=vision_messages, 
            max_tokens=500
        )
        generated_prompt = vision_response.choices[0].message.content[:800]
        logging.info(f"Generated prompt: {generated_prompt}")
        
        # Bước 2: Sử dụng image model để tạo ảnh mới
        rate_limit_image()
        image_response = client.images.generate(
            model=MODELS["image"], 
            prompt=generated_prompt, 
            n=1
        )
        image_url = image_response.data[0].url
        
        # Lưu vào lịch sử nếu cần
        if session_id in session_history:
            user_timestamp = datetime.now().strftime("%H:%M")
            session_history[session_id].append({'role': 'user', 'content': f"Tạo ảnh dựa trên ảnh với mô tả: {user_prompt}", 'timestamp': user_timestamp})
            assistant_timestamp = datetime.now().strftime("%H:%M")
            session_history[session_id].append({
                'role': 'assistant',
                'content': f"<img src='{image_url}' class='generated-image' data-downloadable='true'>",
                'timestamp': assistant_timestamp
            })
        
        return jsonify({
            'success': True,
            'image_url': image_url,
            'prompt_used': generated_prompt
        })
        
    except Exception as e:
        logging.error(f"Error in vision_to_image: {str(e)}")
        return jsonify({'error': f"Lỗi khi tạo ảnh: {str(e)}"}), 500

@app.route('/clear', methods=['POST'])
def clear_history():
    data = request.get_json()
    session_id = data.get('session_id', '')
    if session_id in session_history:
        session_history.pop(session_id)
    return jsonify({"status": "success"})

@app.route('/history', methods=['GET'])
def get_history():
    session_id = request.args.get('session_id')
    return jsonify(session_history.get(session_id, []))

if __name__ == '__main__':
    app.run(debug=True)