'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { getJson } from '@/lib/api';

type ProfileResponse = {
  id: string;
  profile_url: string;
  full_name?: string;
  headline?: string;
  location?: string;
  about?: string;
  experiences?: Array<Record<string, string>>;
  education?: Array<Record<string, string>>;
};

export default function ProfileDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [profile, setProfile] = useState<ProfileResponse | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const run = async () => {
      try {
        const data = await getJson<ProfileResponse>(`/api/profiles/${id}`);
        setProfile(data);
      } catch (err) {
        setError(String(err));
      }
    };
    run();
  }, [id]);

  return (
    <main>
      <h1>Profile Detail</h1>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {profile && <pre>{JSON.stringify(profile, null, 2)}</pre>}
    </main>
  );
}
