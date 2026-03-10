'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { getJson, postJson } from '@/lib/api';

type JobCreateResponse = { job_id: string; status: string; job_type: string };
type JobStatusResponse = {
  id: string;
  status: string;
  job_type: string;
  error_message?: string;
  result?: { search_request_id?: string; results_count?: number; profile_id?: string };
};
type SearchResultItem = { id: string; profile_url: string; full_name?: string; headline?: string; location?: string };
type ProfileFetchResponse = { cached: boolean; profile?: { id: string }; job_id?: string; status?: string };

export default function SearchPage() {
  const router = useRouter();
  const [keywords, setKeywords] = useState('software engineer');
  const [page, setPage] = useState(1);
  const [job, setJob] = useState<JobStatusResponse | null>(null);
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const pollJob = async (jobId: string): Promise<JobStatusResponse> => {
    for (let i = 0; i < 20; i += 1) {
      const data = await getJson<JobStatusResponse>(`/api/jobs/${jobId}`);
      if (data.status === 'succeeded' || data.status === 'failed') return data;
      await new Promise((r) => setTimeout(r, 1000));
    }
    throw new Error('Job polling timeout');
  };

  const createSearch = async () => {
    setLoading(true);
    setError('');
    setResults([]);
    try {
      const created = await postJson<JobCreateResponse>('/api/search/people', { keywords, page });
      const polled = await pollJob(created.job_id);
      setJob(polled);
      if (polled.result?.search_request_id) {
        const list = await getJson<SearchResultItem[]>(`/api/search/results/${polled.result.search_request_id}`);
        setResults(list);
      }
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  const handleResultClick = async (profileUrl: string) => {
    setLoading(true);
    try {
      const res = await postJson<ProfileFetchResponse>('/api/profiles/fetch', { profile_url: profileUrl });
      if (res.cached && res.profile?.id) {
        router.push(`/profiles/${res.profile.id}`);
        return;
      }
      if (!res.job_id) throw new Error('missing job id for profile fetch');
      const profileJob = await pollJob(res.job_id);
      if (profileJob.result?.profile_id) router.push(`/profiles/${profileJob.result.profile_id}`);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <main>
      <h1>People Search</h1>
      <div style={{ display: 'flex', gap: 8 }}>
        <input value={keywords} onChange={(e) => setKeywords(e.target.value)} placeholder="keywords" />
        <input type="number" value={page} onChange={(e) => setPage(Number(e.target.value))} min={1} />
        <button onClick={createSearch} disabled={loading}>Run Search</button>
      </div>
      {loading && <p>Loading...</p>}
      {job && <pre>{JSON.stringify(job, null, 2)}</pre>}

      {results.length > 0 && (
        <ul>
          {results.map((item) => (
            <li key={item.id}>
              <button onClick={() => handleResultClick(item.profile_url)}>
                {item.full_name || item.profile_url} - {item.headline || 'N/A'} - {item.location || 'N/A'}
              </button>
            </li>
          ))}
        </ul>
      )}

      {error && <p style={{ color: 'red' }}>{error}</p>}
    </main>
  );
}
