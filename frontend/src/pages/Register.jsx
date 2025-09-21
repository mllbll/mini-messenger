import React, { useState } from "react";

export default function Register() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleRegister = async () => {
    const res = await fetch("http://localhost:8000/api/users/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    const data = await res.json();
    console.log(data);
  };

  return (
    <div>
      <h2>Регистрация</h2>
      <input placeholder="Логин" onChange={(e) => setUsername(e.target.value)} />
      <input type="password" placeholder="Пароль" onChange={(e) => setPassword(e.target.value)} />
      <button onClick={handleRegister}>Зарегистрироваться</button>
    </div>
  );
}
