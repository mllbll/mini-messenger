import React, { useEffect, useState } from "react";

export default function ChatList() {
  const [chats, setChats] = useState([]);

  useEffect(() => {
    fetch("http://localhost:8000/api/chats")
      .then((res) => res.json())
      .then(setChats);
  }, []);

  return (
    <div>
      <h2>Список чатов</h2>
      <ul>
        {chats.map((chat) => (
          <li key={chat.id}>{chat.name}</li>
        ))}
      </ul>
    </div>
  );
}
