// frontend/src/api.js
const API = (import.meta.env.VITE_API_URL) || "http://localhost:8000";

export async function register(username, password) {
  const r = await fetch(`${API}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password })
  });
  return r.json();
}

export async function login(username, password) {
  const r = await fetch(`${API}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password })
  });
  return r.json();
}

export async function listGroups() {
  const r = await fetch(`${API}/chat/groups`);
  return r.json();
}

export async function createGroup(name) {
  const r = await fetch(`${API}/chat/groups`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name })
  });
  return r.json();
}

export async function getGroupMessages(groupId) {
  const r = await fetch(`${API}/chat/groups/${groupId}/messages`);
  return r.json();
}
