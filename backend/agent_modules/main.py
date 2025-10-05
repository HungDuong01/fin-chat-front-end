from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import os
import time
#from extract_pdfs import search_pdf_with_query as search
import json
import re


dotenv_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path)

api_key=os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

MAIN_AGENT_ID = os.getenv("MAIN_AGENT_ID")
USAGE_AGENT_ID = os.getenv("USAGE_AGENT_ID")
PRICING_AGENT_ID = os.getenv("PRICING_AGENT_ID")
FQA_AGENT_ID = os.getenv("FQA_AGENT_ID")

FQA_STORE_ID = os.getenv("FQA_STORE_ID")
USAGE_STORE_ID = os.getenv("USAGE_STORE_ID")
PRICING_STORE_ID = os.getenv("PRICING_STORE_ID")

app = Flask(__name__)
CORS(app)

def clean_citation(text: str) -> str:
	return re.sub(r'【\d+:\d+†[^】]+】', '', text).strip()

def run_main(thread_id: str, assistant_id: str,timeout: int = 20):
	run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant_id)
	start_time = time.time()
	while True:
		run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
		print(f"[RUN STATUS] {run.status}") 
		# Nếu yêu cầu hành động (gọi tool) → TRẢ VỀ luôn để xử lý
		if run.status == "requires_action":
			return run
		if run.status in ["completed", "failed", "cancelled"]:
			break
		if time.time() - start_time > timeout:
			raise TimeoutError(f"Run {run.id} took too long to complete.")
		time.sleep(0.5)
	return run

def run_assistant(thread_id: str, assistant_id: str, timeout: int = 60):
	run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant_id)
	start_time = time.time()
	while True:
		run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
		print(f"[RUN STATUS] {run.status}") 
		if run.status in ["completed", "failed", "cancelled"]:
			break
		if time.time() - start_time > timeout:
			raise TimeoutError(f"Run {run.id} took too long to complete.")
		time.sleep(0.5)
	return run

def get_latest_response(thread_id: str, last_run_id: str = None) -> str:
	messages = client.beta.threads.messages.list(thread_id=thread_id).data
	for msg in reversed(messages):
		if msg.run_id == last_run_id and msg.role == "assistant":
			return msg.content[0].text.value.strip()
	return "[No assistant response]"

def wait_for_next_run_to_finish(thread_id, timeout=60):
	start = time.time()
	while True:
		runs = client.beta.threads.runs.list(thread_id=thread_id).data
		latest_run = runs[0] if runs else None
		if not latest_run:
			break
		if latest_run.status in ["completed", "failed", "cancelled"]:
			break
		if time.time() - start > timeout:
			raise TimeoutError("Run after submit_tool_outputs took too long.")
		time.sleep(0.5)

def wait_until_run_ready(thread_id, timeout=60):
	start = time.time()
	while True:
		runs = client.beta.threads.runs.list(thread_id=thread_id).data
		active_run = next((r for r in runs if r.status in ["queued", "in_progress", "requires_action"]), None)
		if not active_run:
			break
		if time.time() - start > timeout:
			raise TimeoutError("Another run is still active for this thread.")
		time.sleep(0.5)

def call_assistant(thread_id,agent_id,query:str):
	wait_until_run_ready(thread_id)
	client.beta.threads.messages.create(thread_id=thread_id,role="user",content=query)
	run = run_assistant(thread_id,agent_id)
	response = get_latest_response(thread_id,run.id)
	response = clean_citation(response)
	return response



@app.route('/api/chat', methods=['POST'])
def handle_chat():
	data = request.json
	message = data.get("message")
	conversation_id = data.get("conversation_id")

	if not message:
		return jsonify({"error": "Missing message"}), 400

	# Tạo thread nếu chưa có
	if not conversation_id:
		thread = client.beta.threads.create()
		thread_id = thread.id
	else:
		thread_id = conversation_id

	# Chờ run cũ (nếu có) hoàn tất trước khi thêm message mới
	runs = client.beta.threads.runs.list(thread_id=thread_id).data
	if runs and runs[0].status not in ["completed", "failed", "cancelled"]:
		return jsonify({"error": "Thread is still running, please wait"}), 429

	# Gửi message của người dùng vào thread
	client.beta.threads.messages.create(thread_id=thread_id, role="user", content=message)
	print(f"[→ USER] {message}")

	# Gọi main agent để phân loại intent
	base_run = run_main(thread_id, MAIN_AGENT_ID)	

	# Nếu không có required_action (không yêu cầu tool), trả luôn


	if base_run.required_action is not None:
		try:
			tool_calls = base_run.required_action.submit_tool_outputs.tool_calls
			if not tool_calls:
				raise ValueError("No tool call returned by main assistant")

			tool_call = tool_calls[0]
			print(tool_call)
			target = tool_call.function.name.lower()
			agent = "main"
			query = json.loads(tool_call.function.arguments).get("query")
			print("Intent xác định:",target)
			print(" Query nhận được:", query)
			#print("Required action:", base_run.required_action)

			client.beta.threads.runs.submit_tool_outputs(
				thread_id=thread_id,
				run_id=base_run.id,
				tool_outputs=[
				{
					"tool_call_id": tool_call.id,
					"output": f"Intent {target} đã được xử lý"
				}
			]
			)
			wait_for_next_run_to_finish(thread_id)

			# Đảm bảo target đúng
			if target == "call_fqa":
				response = call_assistant(thread_id,FQA_AGENT_ID,query)
				agent = "faq"

			elif target == "call_pricing":
				response = call_assistant(thread_id,PRICING_AGENT_ID,query)
				agent = "pricing"

			elif target == "call_info_usage":
				response = call_assistant(thread_id,USAGE_AGENT_ID,query)
				agent = "info_usage"

			else:
				response = "Không xác định được intent."
		

			return jsonify({
				"conversation_id": thread_id,
				"response": response,
				"agent": agent
			})

		except Exception as e:
			print(f"[⚠️ TOOL HANDOFF ERROR] {e}")
			latest_run = client.beta.threads.runs.list(thread_id=thread_id).data[0]
			response = get_latest_response(thread_id,latest_run.id)
			return jsonify({
				"conversation_id": thread_id,
				"response": response,
				"agent": "base",
				"note": "Có lỗi trong quá trình điều hướng agent"
			})

	else:
		latest_run = client.beta.threads.runs.list(thread_id=thread_id).data[0]
		response = get_latest_response(thread_id,latest_run.id)
		return jsonify({
			"conversation_id": thread_id,
			"response": response,
			"agent": "main"
		})
	


	
from werkzeug.utils import secure_filename
import base64

@app.route('/api/analyze', methods=['POST'])
def analyze_image_and_text():
	# Lấy dữ liệu từ form
	message = request.form.get('message')
	image_file = request.files.get('image')

	if not image_file:
		return jsonify({'error': 'No image provided'}), 400
	
	if not image_file.mimetype.startswith('image/'):
		return jsonify({'error': 'File is not an image'}), 400

	print(f"[IMAGE] Received with message: {message}")

	# Lưu tạm ảnh để gửi lên OpenAI
	filename = secure_filename(image_file.filename)
	filepath = os.path.join("/tmp", filename)
	image_file.save(filepath)

	# Gửi message + image lên OpenAI (Vision)
	# Bạn có thể điều chỉnh content_type nếu dùng OpenAI API khác
	with open(filepath, "rb") as f:
		image_data = f.read()
	
	os.remove(filepath)
	response = client.chat.completions.create(
		model="gpt-4o",
		messages=[
			{
				"role": "user",
				"content": [
					{ "type": "text", "text": message or "Ảnh đây nút bạn bảo ở đâu" },
					{
						"type": "image_url",
						"image_url": {
							"url": f"data:image/jpeg;base64,{base64.b64encode(image_data).decode()}",
							"detail": "auto"
						}
					}
				]
			}
		],
		max_tokens=1000
	)

	# Trích nội dung trả lời
	result = response.choices[0].message.content.strip()

	return jsonify({
		"intent": "image_analysis",
		"response": result
	})


if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0', port=4000)





















		#Gửi prompt tổng hợp lại bằng main agent
		#summary_prompt = f"""
		#Người dùng vừa hỏi: "{message}"

		#Đây là câu trả lời chuyên môn từ hệ thống nội bộ:
		#\"\"\"{response}\"\"\"

		#Hãy tổng hợp lại thông tin trên và trả lời người dùng bằng văn phong thân thiện, dễ hiểu.
		#"""
		#client.beta.threads.messages.create(thread_id=thread_id, role="user", content=summary_prompt)
		#run_assistant(thread_id, MAIN_AGENT_ID)
		#response = get_latest_response(thread_id)


		#"""client.beta.threads.runs.submit_tool_outputs(


		# """   thread_id=thread_id,
		 #   run_id=base_run.id,
		  #  tool_outputs=[
		   #     {
			#        tool_call_id": tool_call.id,
			 #       output: fIntent {target} đã được xử lý
			  #  }
			#]
		#)"""