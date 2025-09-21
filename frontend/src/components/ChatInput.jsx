import React from "react";

export default function ChatInput({ value, setValue, onSend }) {
  return (
    <div>
      <input value={value} onChange={(e) => setValue(e.target.value)} />
      <button onClick={onSend}>Отправить</button>
    </div>
  );
}
