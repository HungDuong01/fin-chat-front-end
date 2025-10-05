from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import os
import time
import json

dotenv_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path)

api_key=os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

model = 'gpt-3.5-turbo-16k'

class AssistantManager:	
	def __init__(self,model:str = model):
		self.client = client
		self.model = model
		self.assistant = None
		self.thread = None
		self.assistant_id = None
		self.thread_id = None
		self.run = None
		self.summary = None

		#Retrieve existing assistant
		if self.assistant_id:
			self.assistant = self.client.beta.assistants.retrieve(
				assistant_id= self.assistant_id

			)
		if self.thread_id:
			self.thread = self.client.beta.threads.retrieve(
				thread_id= self.thread_id
			)
	
	def create_assistant(self,name,instructions,tools):
		if not self.assistant:
			assistant_obj = self.client.beta.assistants.create(
				name = name,
				instructions= instructions,
				tools = tools,
				model = self.model
			)

			self.assistant_id = assistant_obj.id
			self.assistant = assistant_obj
			print(f"AssistantID::: {self.assistant.id}")

	
	def create_thread(self):
		if not self.thread:
			thread_obj = self.client.beta.threads.create()
			self.thread_id = thread_obj.id
			self.thread = thread_obj
			print(f"Thread ID :::: {self.thread.id}")

	
	def ass_message_to_thread(self,role,content):
		if self.thread:
			self.client.beta.threads.messages.create(
				thread_id = self.thread.id,
				role = role,
				content = content
			)

	def run_assistant(self,instructions):
		if self.thread and self.assistant:
			self.run = self.client.beta.threads.runs.create(
				thread_id = self.thread.id,
				assistant_id= self.assistant.id,
				instructions= instructions
			)

	def process_message(self):
		if self.thread:
			message = self.client.beta.threads.messages.list(thread_id= self.thread.id)
			summary = []
			last_message = message.data[0]
			role = last_message.role
			response = last_message.content[0].text.value

			#for msg in message:
			#	role = msg.role
			#	content = msg.content[0].text.value


	def wait_for_completed(self):
		if self.thread and self.run:
			while True:
				time.sleep(2)
				run_status = self.client.beta.threads.runs.retrieve(
					thread_id= self.thread.id,
					run_id=self.run.id
				)
				print(f"Run status ::: {run_status.model_dump_json(indent=4)}")

				if run_status.status == "completed":
					self.process_message()
					break



	





	

	


			#summary_prompt = 
			"""Người dùng vừa hỏi: "{message}"

			Đây là câu trả lời chuyên môn từ hệ thống nội bộ:
			\"\"\"{response}\"\"\"

			Hãy tổng hợp lại thông tin trên và trả lời người dùng bằng văn phong thân thiện, dễ hiểu.
			"""

			#client.beta.threads.messages.create(thread_id=thread_id, role="user", content=summary_prompt)
			#run_main(thread_id, MAIN_AGENT_ID)
			#response = get_latest_response(thread_id)