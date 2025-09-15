import React, { useState, useEffect } from 'react';

function Explanation({ topic, category }) {
  // State to store the AI-generated summary
  const [summary, setSummary] = useState('');
  // State to handle the loading status
  const [isLoading, setIsLoading] = useState(false);
  // State to store any potential errors
  const [error, setError] = useState(null);

  // useEffect hook runs when the 'topic' or 'category' props change
  useEffect(() => {
    // We don't want to fetch if there's no topic
    if (!topic) {
      return;
    }

    const fetchSummary = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch('http://127.0.0.1:5000/generate-summaries-batch', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          // The backend expects an array of objects
          body: JSON.stringify([{ topic, category, status: 'learning' }]),
        });

        if (!response.ok) {
          throw new Error(`API request failed with status: ${response.status}`);
        }

        const data = await response.json();
        // The backend returns an object with a 'summaries' array
        setSummary(data.summaries[0] || 'No summary was returned.');

      } catch (err) {
        setError(err.message);
        console.error("Failed to fetch summary:", err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSummary();
  }, [topic, category]); // This effect re-runs if 'topic' or 'category' changes

  // --- Render Logic ---
  if (isLoading) {
    return <div>🧠 Generating explanation...</div>;
  }

  if (error) {
    return <div style={{ color: 'red' }}>Error: {error}</div>;
  }
  
  // If a summary has been loaded, display it
  if (summary) {
    return (
      <div>
        <h4>Explanation of {topic}</h4>
        <p>{summary}</p>
      </div>
    );
  }

  // Default state before anything is loaded
  return <div>Please provide a topic to get an explanation.</div>;
}

export default Explanation;