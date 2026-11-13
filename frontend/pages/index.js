import { useState } from "react";
import Head from "next/head";

export default function Home() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState("");

  async function handleSearch(event) {
    if (event) event.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setSearched(true);
    setError("");
    try {
      const response = await fetch(`/api/search?q=${encodeURIComponent(query.trim())}`);
      const data = await response.json();
      setResults(data.results || []);
      setAnswer(data.answer || null);
      if (data.error) setError(data.error);
    } catch (err) {
      setError("ROOTEX could not reach the search API.");
      setResults([]);
    }
    setLoading(false);
  }

  return (
    <div className="container">
      <Head>
        <title>ROOTEX | SmartNETWORK One</title>
        <meta name="description" content="ROOTEX by SmartNETWORK One. Instant index of the real web." />
      </Head>

      <main>
        <div className={`search-header ${searched ? "searched" : ""}`}>
          <p className="brand">SmartNETWORK One</p>
          <h1 className="logo">ROOTEX</h1>
          <form onSubmit={handleSearch} className="search-box">
            <input
              type="text"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search the real internet..."
              aria-label="Search"
            />
            <button type="submit">Search</button>
          </form>
        </div>

        {searched && (
          <section className="results-container">
            {loading && <p>Checking the live index...</p>}
            {!loading && error && <p className="error">{error}</p>}
            {!loading && answer && (
              <article className="answer">
                <span>Instant answer</span>
                <p>{answer}</p>
              </article>
            )}
            {!loading && (
              <div>
                <p className="results-count">
                  {results.length} results for “{query}”
                </p>
                {results.map((result) => (
                  <article key={result.url} className="result-item">
                    <a href={result.url} target="_blank" rel="noreferrer">
                      <span className="result-url">{result.hostname}</span>
                      <h3 className="result-title">{result.title}</h3>
                    </a>
                    <p className="result-snippet">{result.snippet}</p>
                    <p className="result-meta">
                      RSR {result.rsr_score} · semantic {result.semantic} · trust {result.trust} · fresh {result.freshness}
                    </p>
                  </article>
                ))}
              </div>
            )}
          </section>
        )}
      </main>

      <style jsx>{`
        .container { min-height: 100vh; background: #07090c; color: #ededed; font-family: Inter, ui-sans-serif, system-ui, sans-serif; }
        main { display: flex; flex-direction: column; align-items: center; padding: 2rem 1rem 4rem; }
        .search-header { width: min(720px, 100%); margin-top: 18vh; text-align: center; transition: margin 0.3s ease; }
        .search-header.searched { margin-top: 0.5rem; }
        .brand { letter-spacing: 0.18em; text-transform: uppercase; color: #8d97a5; font-size: 0.75rem; }
        .logo { margin: 0.2rem 0 1.2rem; font-size: clamp(3rem, 8vw, 5rem); letter-spacing: -0.06em; }
        .search-box { display: flex; gap: 0.5rem; background: #12161c; border: 1px solid #2a313b; border-radius: 999px; padding: 0.4rem 0.4rem 0.4rem 1rem; }
        input { flex: 1; min-width: 0; background: transparent; border: 0; color: white; font-size: 1.05rem; outline: none; }
        button { border: 0; border-radius: 999px; background: #f4f7fb; color: #111; font-weight: 700; padding: 0.75rem 1rem; cursor: pointer; }
        .results-container { width: min(820px, 100%); margin-top: 2rem; }
        .answer { background: #101820; border: 1px solid #243041; border-radius: 16px; padding: 1rem 1.1rem; margin-bottom: 1.5rem; }
        .answer span { color: #7dffa2; font-size: 0.75rem; letter-spacing: 0.08em; text-transform: uppercase; }
        .result-item { margin: 0 0 1.7rem; }
        .result-url { color: #8b95a3; font-size: 0.85rem; }
        .result-title { color: #9dc1ff; margin: 0.15rem 0; font-size: 1.25rem; font-weight: 600; }
        .result-snippet { color: #c5ccd6; line-height: 1.5; }
        .result-meta, .results-count, .error { color: #8b95a3; font-size: 0.85rem; }
        .error { color: #ffb4a8; }
        a { color: inherit; text-decoration: none; }
      `}</style>
    </div>
  );
}
