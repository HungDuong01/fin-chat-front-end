import os
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

# === Cách 1: Tự động trỏ đến .env nằm cùng thư mục
dotenv_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

#VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID")

#if not VECTOR_STORE_ID:
 #   raise ValueError("VECTOR_STORE_ID chưa được cấu hình trong file .env")
FQA_AGENT_ID = os.getenv("FQA_AGENT_ID")
USAGE_AGENT_ID = os.getenv("USAGE_AGENT_ID")
PRICING_AGENT_ID = os.getenv("PRICING_AGENT_ID")

FQA_STORE_ID = os.getenv("FQA_STORE_ID")
USAGE_STORE_ID = os.getenv("USAGE_STORE_ID")
PRICING_STORE_ID = os.getenv("PRICING_STORE_ID")

def update_env(key: str, value: str, env_file: str = ".env"):
    if not os.path.exists(env_file):
        with open(env_file, "w") as f:
            f.write(f"{key}={value}\n")
        return

    with open(env_file, "r") as f:
        lines = f.readlines()

    found = False
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{key}="):
            lines[i] = f"{key}={value}\n"
            found = True
            break

    if not found:
        lines.append(f"{key}={value}\n")

    with open(env_file, "w") as f:
        f.writelines(lines)



def create_agent(name: str, instructions: str, agent_id: str,vector_id:str):
    agent = client.beta.assistants.create(
        name=name,
        instructions=instructions,
        model="gpt-4.1",
        tools=[{"type": "file_search"}],
        tool_resources={
            "file_search": {
                "vector_store_ids": [vector_id]
            }
        },
        temperature = 1
    )
    update_env(agent_id, agent.id)
    return agent

def create_agent_pricing(name: str, instructions: str, agent_id: str,vector_id:str):
    agent = client.beta.assistants.create(
        name=name,
        instructions=instructions,
        model="gpt-4.1",
        tools=[{"type": "file_search"},
               {"type": "code_interpreter"}],
        tool_resources={
            "file_search": {
                "vector_store_ids": [vector_id]
            }
        },
        temperature = 0.15
    )
    update_env(agent_id, agent.id)
    return agent
# === Tạo các agent ===

info_usage_agent = create_agent(
    name="Info & Usage Agent",
    instructions="""
    # Vai trò
Bạn là trợ lý kỹ thuật, giải đáp và phân loại người dùng hỏi về các vấn đề như tạo tài khoản của fiine hay cách đăng kí tài khoản fiine hay các đặc điểm của fiine 

# Các bước
- Bước 1: Xem ý định của người dùng là gì chỉ phân loại vào 3 DẠNG: đặc điểm hay phòng ban hay tài khoản.
- Bước 2: 
+ Nếu ý định là đặc điểm thì bạn sẽ xem file dacdiemcuafiine.pdf 
+ Nếu ý định là phòng ban thì bạn sẽ xem file phongban.pdf 
+ Nếu ý định là tài khoản thì bạn sẽ xem file gioithieufiine.pdf 

-Bước 3: Phản hồi lại kết quả và báo cáo xem đã kiểm tra ở file pdf nào. Nếu không tìm thấy câu trả lời hay xem lại mỗi file pdf 2 lần rồi mới phản hồi là không tìm thấy.

Với mỗi câu trả lời bạn hãy diễn đạt lại sao cho dễ hiểu, thận thiện với người dùng.

Lưu ý: Nếu tại các bước có phản hồi có chữ null. thì bỏ chữ null đi. Hãy nhớ kĩ
    """,
    agent_id = USAGE_AGENT_ID,
    vector_id = USAGE_STORE_ID
    
)

pricing_agent = create_agent_pricing(
    name="Pricing Agent",
    instructions="""
  Với mỗi câu hỏi liên quan về giá tiền của các gói sản phẩm. 
  - Hãy xem người dùng cần dùng cho bao nhiêu người và dùng gói dịch vụ nào.
  - Đầu tiên xem họ cần cho bao nhiêu người, sau đó nếu dùng gói pro 3 tháng xem cột thứ 2 , gói pro 6 tháng xem cột 3
   , gói pro 1 năm xem cột 4 , gói Vip 6 tháng xem cột 5, gói Vip 1 năm xem cột 6 và cuối cùng dóng tương ứng với hàng có chứa số người
   mà người dùng yêu cầu.
  - Sẽ có 3 gói dịch vụ là Basic , Pro và Vip
  - Nhớ là gói PRO và VIP sẽ phụ thuộc vào số lượng nhân sự nữa. 
  - Gói VIP sẽ chỉ có gia hạn 6 tháng và 1 năm thôi.
  - Tiêu chí so sánh sẽ bao gôm: tính năng cao cấp,giới hạn sử dụng,công cụ quản lý,công cụ giao tiếp,administration, an toàn và bảo mật, hỗ trợ.
  - Mỗi tính năng này sẽ chỉ cần lấy 2 dòng đầu để gửi cho người dùng nếu ngừoi dùng hỏi so sánh

 - Đừng trả lời kiến thức ngoài file pdf. Nếu không biết hãy bảo: "Hiện không có sản phẩm nào".

  Với mỗi câu trả lời bạn hãy diễn đạt lại sao cho dễ hiểu, thận thiện với người dùng.

  Một số ví dụ:

- "Cho tôi biết giá gói pro 3 tháng" thì trả lời giá gói dịch vụ sẽ bao gồm theo số lượng người nữa
- "Cho tôi biết giá gói pro 6 tháng cho 5 người " thì sẽ trả lời luôn là 2.247.750 VND chứ không cần nói gì thêm
- Gói Basic là miễn phí cho tối đa 5 thành viên

    """
    ,
    agent_id= PRICING_AGENT_ID,
    vector_id = PRICING_STORE_ID
)

fqa_agent = create_agent(
    name="FQA Agent",
    instructions="""
    Bạn là một trợ lý ảo đại diện cho Fiine — một hệ thống hỗ trợ khách hàng thông minh.

    - Với mỗi câu hỏi từ người dùng được điều hướng đến bạn, bạn sẽ truy xuất hết các thông tin từ đầu đến cuối để xem có thông tin người dùng hỏi không để trả lời.
	- Bạn phải xem xét ki các thông tin trong file.
	- Nếu trong file không có thông tin,bạn không được tự bịa mà chỉ cần phản hồi không biết
    Với mỗi câu trả lời bạn hãy diễn đạt lại sao cho dễ hiểu, thận thiện với người dùng.
    """
    ,
    agent_id= FQA_AGENT_ID,
    vector_id = FQA_STORE_ID
)

main_agent = client.beta.assistants.create(
    name = "Main Agent",
    instructions = """Bạn là một Assistant phân loại intent cho hệ thống Fiine. Bạn chỉ có một nhiệm vụ duy nhất:

PHÂN LOẠI Ý ĐỊNH của người dùng vào 1 trong 4 nhóm sau và luôn luôn trả về kết quả dưới dạng tool_call:

1. Nếu người dùng hỏi về **cách sử dụng app Fiine, các bước thực hiện, cách đăng ký, hướng dẫn sử dụng dịch vụ**, hãy trả về: `function: call_info_usage`

2. Nếu người dùng hỏi về **giá cả, gói dịch vụ, chi phí, khuyến mãi, phí cho nhóm**, hãy trả về: `function: call_pricing`

3. Nếu người dùng hỏi về **FAQ, chính sách, thời gian làm việc, bảo mật, sản phẩm Fiine nói chung**, hãy trả về: `function: call_fqa`

4. Nếu người dùng chỉ **trò chuyện xã giao, không hỏi thông tin cụ thể**, hãy trả lời thân thiện mà không gọi function.

Nếu bạn không thể xác định intent, hãy xin lỗi người dùng một cách lịch sự như sau:
"Hiện tại mình chưa có thông tin chính xác về vấn đề này, để mình kiểm tra thêm giúp bạn nhé!"

Luôn ưu tiên trả về tool_call nếu có thể. Không bao giờ trả lời trực tiếp nếu câu hỏi nằm trong nhóm 1-2-3.

Với mỗi câu trả lời bạn hãy diễn đạt lại sao cho dễ hiểu, thận thiện với người dùng.

Một số ví dụ:
- "Cho tôi biết giá gói 3 tháng" → call_pricing
- "Cho tôi biết giá gói 6 tháng cho 5 người" thì call_pricing
- "App này dùng như nào?" → call_info_usage
- "Cách tạo phòng ban trong Fiine" thì call_info_usage
- "Fiine có bảo mật thông tin không?" → call_info_usage
- "Fiine có đặc điểm gì " thì call_info_usage
- "Tôi có ích lợi gì khi sử dụng Fiine để quản lý công việc?" thì call_fqa
- "Các tài liệu, dữ liệu khi tải lên kho lưu trữ thì người trong cùng tổ chức có thể thấy được 
không?" thì call_fqa
- "Trong chức năng Tài Nguyên có phân chia làm 3 không gian là: kho lưu trữ, công việc và tin 
nhắn. Vậy việc phân chia như vậy nhằm mục đích gì và nó có tác dụng gì trong việc quản lý công việc?" thì call_fqa
- "Bạn khỏe không?" → trò chuyện
""",
    model = "gpt-4.1-mini",
	tools=[
        {
            "type": "function",
            "function": {
                "name": "call_info_usage",
                "description": "Trả lời về thông tin sử dụng sản phẩm",
                "parameters": {"type": "object", "properties": {"query": {"type": "string"}}}
            }
        },
        {
            "type": "function",
            "function": {
                "name": "call_pricing",
                "description": "Trả lời về giá cả sản phẩm",
                "parameters": {"type": "object", "properties": {"query": {"type": "string"}}}
            }
        },
		       {
            "type": "function",
            "function": {
                "name": "call_fqa",
                "description": "Trả lời các câu hỏi ngoài giá và hướng dẫn sử dụng",
                "parameters": {"type": "object", "properties": {"query": {"type": "string"}}}
            }
        },
    ],
    temperature = 0.6
)



print("Main Agent ID:      ", main_agent.id)
print("Usage Agent ID: ", info_usage_agent.id)
print("Pricing Agent ID:   ", pricing_agent.id)
print("FQA Agent ID:      ", fqa_agent.id)
print("Các ID đã được ghi vào file .env")



