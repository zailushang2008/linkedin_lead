'use client';

import { FormEvent, useState } from 'react';
import { useRouter } from 'next/navigation';
import { postJson } from '@/lib/api';

type LoginResponse = { access_token: string; token_type: string };

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('demo@example.com');
  const [password, setPassword] = useState('demo123');
  const [error, setError] = useState('');

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      const data = await postJson<LoginResponse>('/api/auth/login', { email, password });
      localStorage.setItem('token', data.access_token);
      router.push('/search');
    } catch (err) {
      setError(String(err));
    }
  };

  return (
    <main>
      <h1>Login (MVP)</h1>
      <form onSubmit={onSubmit} style={{ display: 'grid', gap: 8, maxWidth: 360 }}>
        <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" />
        <input value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" type="password" />
        <button type="submit">Login</button>
      </form>
      {error && <p style={{ color: 'red' }}>{error}</p>}
    </main>
  );
}
