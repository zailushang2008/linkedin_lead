import Link from 'next/link';

export default function HomePage() {
  return (
    <main>
      <h1>LinkedIn Lead MVP</h1>
      <ul>
        <li><Link href="/login">/login</Link></li>
        <li><Link href="/search">/search</Link></li>
      </ul>
    </main>
  );
}
