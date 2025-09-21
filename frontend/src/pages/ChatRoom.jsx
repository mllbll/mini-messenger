import React, { useEffect, useState } from "react";

export default function ChatRoom({ chatId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  let socket;

  useEffect(() => {
    socket = new WebSocket(`ws://localhost:8000/ws/chat/${chatId}`);
    socket.onmessage = (event) => {
      setMessages((prev) => [...prev, event.data]);
    };
    return () => socket.close();
  }, [chatId]);

  const sendMessage = () => {
    if (input.trim()) {
      socket.send(input);
      setMessages([...messages, input]);
      setInput("");
    }
  };

  return (
    <div>
      <h2>Чат {chatId}</h2>
      <div style={{ border: "1px solid gray", height: "200px", overflowY: "scroll" }}>
        {messages.map((msg, i) => (
          <div key={i}>{msg}</div>
        ))}
      </div>
      <input value={input} onChange={(e) => setInput(e.target.value)} />
      <button onClick={sendMessage}>Отправить</button>
    </div>
  );
}
