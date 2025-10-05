import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class ChatService {
  private chatUrl = 'http://127.0.0.1:4000/api/chat';
  private imageUrl = 'http://127.0.0.1:4000/api/analyze';
  private conversationId: string | null = null;

  constructor(private http: HttpClient) {}

  // Gửi tin nhắn text kèm context (conversationId, history)
  sendMessage(message: string, history: any[]): Observable<any> {
    const payload: any = {
      message,
      conversation_id: this.conversationId,
      history, // có thể dùng nếu backend hỗ trợ
    };

    return new Observable((observer) => {
      this.http.post<any>(this.chatUrl, payload).subscribe({
        next: (res) => {
          if (res.conversation_id) {
            this.conversationId = res.conversation_id;
          }

          const formatted = {
            replies: [
              {
                intent: res.agent || 'assistant',
                reply: res.response || '[Không có nội dung phản hồi]',
              },
            ],
          };

          // Thêm ghi chú nếu có (tool_call note...)
          if (res.note) {
            formatted.replies.push({
              intent: 'system',
              reply: `Ghi chú: ${res.note}`,
            });
          }

          observer.next(formatted);
          observer.complete();
        },
        error: (err) => observer.error(err),
      });
    });
  }

  // Gửi ảnh + text → /api/analyze
  sendImageAndText(formData: FormData): Observable<any> {
    return new Observable((observer) => {
      this.http.post<any>(this.imageUrl, formData).subscribe({
        next: (res) => {
          const formatted = {
            replies: [
              {
                intent: res.intent || 'assistant',
                reply: res.response || '[Không có nội dung phản hồi]',
              },
            ],
          };
          observer.next(formatted);
          observer.complete();
        },
        error: (err) => observer.error(err),
      });
    });
  }

  resetConversation() {
    this.conversationId = null;
  }
}
