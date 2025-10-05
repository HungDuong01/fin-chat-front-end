import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { ChatService } from '../services/chat.services';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './home.component.html',
})
export class HomeComponent implements OnInit {
  constructor(private chatService: ChatService) {}

  ngOnInit(): void {}

  selectedImage: File | null = null;
  messages: { role: string; content: string }[] = [];
  newMessage = '';
  history: { title: string; full: string }[] = [];
  showHistory = false;
  expandedHistoryIndex: number | null = null;
  imagePreviewUrl: string | null = null;

  onImageSelected(event: Event) {
	const input = event.target as HTMLInputElement;
	if (input.files && input.files.length > 0) {
	  const file = input.files[0];
	  if (file.type.startsWith('image/')) {
		this.selectedImage = file;
  
		// Hiển thị ảnh
		const reader = new FileReader();
		reader.onload = () => {
		  this.imagePreviewUrl = reader.result as string;
		};
		reader.readAsDataURL(file);
	  } else {
		alert('Chỉ chấp nhận ảnh!');
		this.selectedImage = null;
		this.imagePreviewUrl = null;
	  }
	}
  }

  sendMessage() {
	const message = this.newMessage.trim();
	if (!message && !this.selectedImage) return;
  
	this.messages.push({ role: 'user', content: message });
  
	if (this.selectedImage) {
	  console.log('Sending image:', this.selectedImage);
	  const formData = new FormData();
	  formData.append('message', message);
	  formData.append('image', this.selectedImage);
  
	  this.chatService.sendImageAndText(formData).subscribe(
		(res) => this.handleResponse(res),
		(err) => this.handleError(err)
	  );
	} else {
	  const shortHistory = this.messages.slice(-3);
	  this.chatService.sendMessage(message, shortHistory).subscribe(
		(res) => this.handleResponse(res),
		(err) => this.handleError(err)
	  );
	}
  
	this.newMessage = '';
	this.selectedImage = null;
	this.imagePreviewUrl = null;
  }
  handleResponse(res: any) {
	if (Array.isArray(res.replies)) {
	  res.replies.forEach((r: any) => {
		if (r.intent && r.reply) {
		  this.messages.push({ role: 'assistant', content: `[${r.intent}]: ${r.reply}` });
		}
	  });
	} else {
	  this.messages.push({ role: 'agent', content: 'Phản hồi không hợp lệ.' });
	}
  }
  
  handleError(err: any) {
	const errorMessage = err.error?.error || err.message || 'Đã xảy ra lỗi.';
	this.messages.push({ role: 'agent', content: `Lỗi: ${errorMessage}` });
  }
  handleDrop(event: DragEvent) {
	event.preventDefault();
	const file = event.dataTransfer?.files?.[0];
	if (file && file.type.startsWith('image/')) {
	  this.selectedImage = file;
  
	  const reader = new FileReader();
	  reader.onload = () => {
		this.imagePreviewUrl = reader.result as string;
	  };
	  reader.readAsDataURL(file);
	} else {
	  alert('Chỉ chấp nhận ảnh!');
	  this.selectedImage = null;
	  this.imagePreviewUrl = null;
	}
  } 
  handleFileSelect(event: Event) {
	const input = event.target as HTMLInputElement;
	const file = input.files?.[0];
	this.processSelectedImage(file);
  }
  processSelectedImage(file: File | undefined) {
	if (file && file.type.startsWith('image/')) {
	  this.selectedImage = file;
  
	  const reader = new FileReader();
	  reader.onload = () => {
		this.imagePreviewUrl = reader.result as string;
	  };
	  reader.readAsDataURL(file);
	} else {
	  alert('Chỉ chấp nhận ảnh!');
	  this.selectedImage = null;
	  this.imagePreviewUrl = null;
	}
  }
  clearImage() {
	this.selectedImage = null;
	this.imagePreviewUrl = null;
  }
  

  toggleHistory() {
    this.showHistory = !this.showHistory;
  }

  addToHistoryAndReset() {
	if (this.messages.length > 0) {
	  const fullText = this.messages.map(m => `${m.role}: ${m.content}`).join('\n');
	  const firstLine = this.messages[0]?.content || 'Không có tiêu đề';
	  this.history.push({ title: firstLine, full: fullText });
	  this.messages = [];
	  this.newMessage = '';
	  this.chatService.resetConversation(); // ← thêm dòng này
	}
  }
  
  onDragOver(event: DragEvent) {
	event.preventDefault();
  }
  
  toggleHistoryItem(index: number) {
    this.expandedHistoryIndex = this.expandedHistoryIndex === index ? null : index;
  }
}