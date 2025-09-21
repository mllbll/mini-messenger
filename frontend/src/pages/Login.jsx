import React, { useState } from "react";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = async () => {
    const res = await fetch("http://localhost:8000/api/users/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    const data = await res.json();
    console.log(data);
  };

  return (
    <div>
      <h2>Вход</h2>
      <input placeholder="Логин" onChange={(e) => setUsername(e.target.value)} />
      <input type="password" placeholder="Пароль" onChange={(e) => setPassword(e.target.value)} />
      <button onClick={handleLogin}>Войти</button>
    </div>
  );
}
