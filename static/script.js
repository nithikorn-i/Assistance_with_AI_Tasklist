document.addEventListener('DOMContentLoaded', () => {
  console.log("🔥 ระบบเริ่มทำงาน");
  
  let currentChatId = null;
  let isWaitingResponse = false;

  // DOM Elements
  const userInput = document.getElementById('user-input');
  const machineModel = document.getElementById('Machine-model');
  const sendButton = document.getElementById('send-button');
  const chatBox = document.getElementById('chat-box');
  const chatViewer = document.getElementById('chat-viewer');
  const historyMenu = document.getElementById('history-menu');
  const newChatBtn = document.getElementById('new-chat-btn');
  const historyDropdownToggle = document.querySelector('.history-dropdown > a');
  const menuToggle = document.querySelector('.menu-toggle');
  const luxurySidebar = document.querySelector('.luxury-sidebar');
  menuToggle.addEventListener('click', () => {
  luxurySidebar.classList.toggle('mobile-show');
  });
  document.addEventListener('click', (event) => {
    const isClickInsideSidebar = luxurySidebar.contains(event.target);
    const isClickOnToggle = menuToggle.contains(event.target);
    if (!isClickInsideSidebar && !isClickOnToggle) {
      luxurySidebar.classList.remove('mobile-show');
    }
  });

  async function initializeApp() {
    try {
      console.log("🚀 กำลังเริ่มต้นระบบ...");
      disableInput(true);
      await loadAllChatHistories();
      const hasHistory = document.querySelectorAll('#history-menu li').length > 0;
      if (hasHistory) {
        const latestChatId = document.querySelector('#history-menu li').dataset.chatid;
        currentChatId = latestChatId;
        await loadChat(latestChatId);
      } else {
        await startNewChat();
      }
      historyDropdownToggle.addEventListener('click', (e) => {
      e.preventDefault();
      historyMenu.classList.toggle('show');
      });
      
      console.log("✅ เริ่มต้นระบบเสร็จสิ้น");
    } catch (error) {
      console.error("❌ ข้อผิดพลาดในการเริ่มต้นระบบ:", error);
      showError("ระบบเริ่มต้นไม่สำเร็จ: " + error.message);
    } finally {
      disableInput(false);
    }
  }

async function loadAllChatHistories() {
  try {
    console.log("🔍 กำลังโหลดประวัติแชททั้งหมด...");
    const res = await fetch('/get-all-chats');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    console.log("📊 ข้อมูลประวัติที่ได้รับ:", data);
    
    const historyMenu = document.getElementById('history-menu');
    historyMenu.innerHTML = '';

    if (data.chats && data.chats.length > 0) {
      highlightHistory(currentChatId);
      data.chats.forEach(chat => {
        const li = document.createElement('li');
        li.dataset.chatid = chat.chatId;

        // 🕒 แสดงเวลา
        const date = new Date(chat.lastActivity);
        const timeStr = date.toLocaleTimeString('th-TH', { hour: '2-digit', minute: '2-digit' });

        // 📝 span ข้อความแชท
        const span = document.createElement('span');
        span.textContent = `แชท ${timeStr}`;
        span.style.cursor = 'pointer';
        span.style.flexGrow = '1';  // ดันให้ข้อความอยู่ซ้ายสุด

        // 🗑️ ปุ่มลบ
        const deleteBtn = document.createElement('button');
        deleteBtn.textContent = '❌';
        deleteBtn.title = 'ลบแชท';
        deleteBtn.style.border = 'none';
        deleteBtn.style.background = 'none';
        deleteBtn.style.color = '#999';
        deleteBtn.style.fontSize = '14px';
        deleteBtn.style.cursor = 'pointer';
        deleteBtn.style.padding = '0';
        deleteBtn.style.marginLeft = '6px';

        // 👉 จัด layout
        li.style.display = 'flex';
        li.style.alignItems = 'center';
        li.style.gap = '6px';

        // 📌 คลิกแชท
        li.addEventListener('click', () => {
          loadChat(chat.chatId);
        });

        // 🗑️ คลิกลบ
        deleteBtn.addEventListener('click', async (e) => {
          e.stopPropagation(); // ป้องกันไม่ให้โหลดแชท
          if (confirm('คุณแน่ใจว่าจะลบแชทนี้?')) {
            await deleteChat(chat.chatId);
            await loadAllChatHistories();
            clearChat();
          }
        });

        // 🧱 ประกอบ li
        li.appendChild(span);
        li.appendChild(deleteBtn);
        historyMenu.appendChild(li);
      });
    } else {
      console.log("ℹ️ ไม่พบประวัติแชท");
    }
  } catch (error) {
    console.error("❌ โหลดประวัติล้มเหลว:", error);
    showError("โหลดประวัติไม่สำเร็จ: " + error.message);
  }
}




async function startNewChat() {
  if (isWaitingResponse) {
    console.warn("⚠️ ระบบกำลังทำงาน กรุณารอสักครู่");
    return;
  }

  try {
    disableInput(true);
    const res = await fetch('/new-chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    currentChatId = data.chatId;
    clearChat();
    addMessage("สวัสดีครับ/ค่ะ! ยินดีต้อนรับสู่ระบบแชท AI Softsquare Group", "ai");
    removeActiveHistoryHighlight();
    await loadAllChatHistories();
    highlightHistory(currentChatId);
  } catch (error) {
    showError("ไม่สามารถเริ่มแชทใหม่ได้: " + error.message);
    throw error;
  } finally {
    disableInput(false);
  }
}


  async function sendMessage() {
  const message = userInput.value.trim();
  const machine = machineModel.value.trim();
  if (!message) return showError("กรุณากรอกข้อความ");
  if (!currentChatId) {
    await startNewChat();
    await new Promise(resolve => setTimeout(resolve, 100));
  }

  addMessage(message, 'user');
  userInput.value = '';
  disableInput(true);
  isWaitingResponse = true;

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        chatId: currentChatId, 
        message: message, 
        sender: 'user',
        machine: machine
      })
    });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();

    addMessage(data.response, 'ai');
    await loadAllChatHistories();
    highlightHistory(currentChatId);
    await loadChat(currentChatId);

  } catch (error) {
    addMessage("ขออภัย เกิดข้อผิดพลาดในการเชื่อมต่อกับ AI", 'ai');
  } finally {
    isWaitingResponse = false;
    disableInput(false);
  }
}



  async function loadChat(chatId) {
    if (isWaitingResponse || !chatId) return;
    disableInput(true);
    setLoading(true);
    try {
      const res = await fetch(`/get-history/${chatId}`);
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      chatViewer.innerHTML = '';
      if (data.messages && data.messages.length > 0) {
        data.messages.forEach(msg => {
          const div = document.createElement('div');
          div.className = `message ${msg.sender}-message`;
          div.innerHTML = `<div class="message-content">${msg.text}</div>`;
          chatViewer.appendChild(div);
        });
      } else {
        chatViewer.innerHTML = '<div class="no-messages">ไม่พบข้อความในประวัตินี้</div>';
      }
      chatBox.style.display = 'none';
      chatViewer.style.display = 'flex';
      currentChatId = chatId;
      highlightHistory(chatId);
    } catch (error) {
      chatViewer.innerHTML = `<div class="error">โหลดประวัติไม่สำเร็จ: ${error.message}</div>`;
    } finally {
      setLoading(false);
      disableInput(false);
    }
  }

async function deleteChat(chatId) {
  setLoading(true); // ✅ แสดงโหลด

  try {
    const res = await fetch(`/delete-chat/${chatId}`, {
      method: 'DELETE',
    });

    if (!res.ok) {
      const errorText = await res.text();
      throw new Error(`ลบแชทไม่สำเร็จ: ${errorText}`);
    }

    console.log(`✅ ลบแชท ${chatId} สำเร็จ`);
  } catch (error) {
    console.error(error);
    alert('เกิดข้อผิดพลาดในการลบแชท: ' + error.message);
  } finally {
    setLoading(false); // ✅ ซ่อนโหลด
  }
}



  // ช่วยเพิ่มข้อความในกล่องแชท
function addMessage(text, sender) {
  const targetContainer = (chatViewer.style.display === 'flex') ? chatViewer : chatBox;
  const div = document.createElement('div');
  div.className = `message ${sender}-message`;

  const messageContent = document.createElement('div');
  messageContent.className = 'message-content';

  const messageText = document.createElement('p');
  messageText.className = 'message-text';
  messageContent.appendChild(messageText);
  div.appendChild(messageContent);
  targetContainer.appendChild(div);
  targetContainer.scrollTop = targetContainer.scrollHeight;

  if (sender === 'ai') {
    // 👉 แสดงข้อความแบบค่อยๆพิมพ์
    let i = 0;
    const typingSpeed = 20; // ความเร็วพิมพ์ (ms ต่อ 1 ตัว)
    const typeInterval = setInterval(() => {
      if (i < text.length) {
        messageText.textContent += text.charAt(i);
        i++;
        targetContainer.scrollTop = targetContainer.scrollHeight;
      } else {
        clearInterval(typeInterval);
      }
    }, typingSpeed);
  } else {
    // 🧑‍🦰 ฝั่งผู้ใช้ แสดงทันที
    messageText.textContent = text;
  }
}



  function clearChat() {
    chatBox.innerHTML = '';
    chatBox.style.display = 'flex';
    chatViewer.style.display = 'none';
  }

  function disableInput(disabled) {
    userInput.disabled = disabled;
    sendButton.disabled = disabled;
    sendButton.innerHTML = disabled 
      ? '<i class="fas fa-spinner fa-spin"></i>' 
      : '<i class="fas fa-paper-plane"></i>';
  }

  function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    chatBox.appendChild(errorDiv);
    setTimeout(() => errorDiv.remove(), 3000);
  }

  function highlightHistory(chatId) {
  document.querySelectorAll('#history-menu li span').forEach(span => {
    span.classList.toggle('active', span.parentElement.dataset.chatid === chatId);
  });
}

  function removeActiveHistoryHighlight() {
    document.querySelectorAll('#history-menu span').forEach(span => {
      span.classList.remove('active');
    });
  }

function setLoading(isLoading) {
  if (isLoading) {
    chatViewer.innerHTML = `
      <div class="loading-container">
        <i class="fa fa-spinner fa-spin fa-2x"></i>
        <div>Processing...</div>
      </div>
    `;
  } else {
    // ไม่ลบเนื้อหาอื่นอีก ถ้าโหลดเสร็จ ให้ปล่อยให้โค้ดอื่นจัดการ
  }
}

  sendButton.addEventListener('click', sendMessage);
  userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !isWaitingResponse) sendMessage();
  });
  newChatBtn.addEventListener('click', startNewChat);

  console.log("🔄 กำลังเริ่มแอปพลิเคชัน...");
  initializeApp().catch(error => {
    console.error("💥 ข้อผิดพลาดร้ายแรง:", error);
    showError("ระบบขัดข้อง: " + error.message);
  });
});
