import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [scenario, setScenario] = useState('');
  const [depth, setDepth] = useState('brief');
  const [timeline, setTimeline] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [pastTimelines, setPastTimelines] = useState([]);

  useEffect(() => {
    fetchPastTimelines();
  }, []);

  const fetchPastTimelines = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/timelines`);
      setPastTimelines(response.data.slice(0, 5)); // Show last 5 timelines
    } catch (err) {
      console.error('Failed to fetch past timelines:', err);
    }
  };

  const generateTimeline = async () => {
    if (!scenario.trim()) {
      setError('Please enter a scenario');
      return;
    }

    setLoading(true);
    setError('');
    setTimeline(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/generate-timeline`, {
        scenario: scenario,
        depth: depth
      });
      setTimeline(response.data);
      fetchPastTimelines(); // Refresh the list
    } catch (err) {
      setError('Failed to generate timeline. Please try again.');
      console.error('Timeline generation error:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadTimeline = async (timelineId) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/timeline/${timelineId}`);
      setTimeline(response.data);
      setScenario(response.data.original_scenario);
    } catch (err) {
      setError('Failed to load timeline');
      console.error('Timeline loading error:', err);
    }
  };

  const exampleScenarios = [
    "What if Gandhi had access to AI during the Indian freedom movement?",
    "What if the Library of Alexandria was never destroyed?",
    "What if the internet was invented in the 1950s?",
    "What if Einstein had collaborated with Tesla on wireless technology?",
    "What if the printing press was invented in ancient Rome?"
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-800">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-6xl font-bold text-white mb-4 bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-violet-400">
            ⏰ AI Time Machine
          </h1>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto">
            Explore alternate histories with AI-powered timeline generation. Ask "what if" and discover how different choices could have reshaped our world.
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Input Section */}
          <div className="lg:col-span-2">
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20">
              <h2 className="text-2xl font-bold text-white mb-6">Create Your Alternate Timeline</h2>
              
              {/* Scenario Input */}
              <div className="mb-6">
                <label className="block text-white text-lg font-medium mb-3">
                  What if...? 🤔
                </label>
                <textarea
                  value={scenario}
                  onChange={(e) => setScenario(e.target.value)}
                  placeholder="Enter your hypothetical historical scenario..."
                  className="w-full h-32 px-4 py-3 rounded-xl bg-white/20 text-white placeholder-gray-300 border border-white/30 focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/50 resize-none"
                />
              </div>

              {/* Depth Selection */}
              <div className="mb-6">
                <label className="block text-white text-lg font-medium mb-3">
                  Timeline Depth
                </label>
                <div className="flex gap-4">
                  <button
                    onClick={() => setDepth('brief')}
                    className={`px-6 py-3 rounded-xl font-medium transition-all ${
                      depth === 'brief'
                        ? 'bg-cyan-500 text-white shadow-lg shadow-cyan-500/25'
                        : 'bg-white/20 text-gray-300 hover:bg-white/30'
                    }`}
                  >
                    Brief (5 events)
                  </button>
                  <button
                    onClick={() => setDepth('detailed')}
                    className={`px-6 py-3 rounded-xl font-medium transition-all ${
                      depth === 'detailed'
                        ? 'bg-cyan-500 text-white shadow-lg shadow-cyan-500/25'
                        : 'bg-white/20 text-gray-300 hover:bg-white/30'
                    }`}
                  >
                    Detailed (10 events)
                  </button>
                </div>
              </div>

              {/* Generate Button */}
              <button
                onClick={generateTimeline}
                disabled={loading || !scenario.trim()}
                className="w-full bg-gradient-to-r from-cyan-500 to-violet-500 text-white font-bold py-4 px-8 rounded-xl hover:from-cyan-600 hover:to-violet-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:scale-105 shadow-lg shadow-violet-500/25"
              >
                {loading ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white mr-3"></div>
                    Generating Timeline...
                  </div>
                ) : (
                  '🚀 Generate Timeline'
                )}
              </button>

              {error && (
                <div className="mt-4 p-4 bg-red-500/20 border border-red-500/50 rounded-xl text-red-200">
                  {error}
                </div>
              )}

              {/* Example Scenarios */}
              <div className="mt-8">
                <h3 className="text-lg font-medium text-white mb-4">💡 Try these examples:</h3>
                <div className="space-y-2">
                  {exampleScenarios.map((example, index) => (
                    <button
                      key={index}
                      onClick={() => setScenario(example)}
                      className="block w-full text-left p-3 rounded-lg bg-white/10 hover:bg-white/20 text-gray-300 hover:text-white transition-all text-sm"
                    >
                      {example}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar - Past Timelines */}
          <div className="space-y-6">
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
              <h3 className="text-xl font-bold text-white mb-4">📚 Recent Timelines</h3>
              {pastTimelines.length > 0 ? (
                <div className="space-y-3">
                  {pastTimelines.map((t) => (
                    <button
                      key={t.id}
                      onClick={() => loadTimeline(t.id)}
                      className="block w-full text-left p-3 rounded-lg bg-white/10 hover:bg-white/20 transition-all text-sm"
                    >
                      <div className="text-white font-medium truncate">
                        {t.original_scenario}
                      </div>
                      <div className="text-gray-400 text-xs mt-1">
                        {new Date(t.created_at).toLocaleDateString()}
                      </div>
                    </button>
                  ))}
                </div>
              ) : (
                <p className="text-gray-400 text-sm">No timelines generated yet</p>
              )}
            </div>
          </div>
        </div>

        {/* Timeline Display */}
        {timeline && (
          <div className="mt-12">
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20">
              <div className="mb-8">
                <h2 className="text-3xl font-bold text-white mb-4">🌟 Alternate Timeline</h2>
                <div className="bg-gradient-to-r from-cyan-500/20 to-violet-500/20 rounded-xl p-6 border border-cyan-500/30">
                  <h3 className="text-xl font-bold text-cyan-400 mb-2">Scenario:</h3>
                  <p className="text-white text-lg">{timeline.original_scenario}</p>
                </div>
                <div className="mt-6 p-6 bg-white/10 rounded-xl">
                  <h3 className="text-lg font-bold text-white mb-2">Historical Analysis:</h3>
                  <p className="text-gray-300">{timeline.summary}</p>
                </div>
              </div>

              {/* Timeline Events */}
              <div className="space-y-6">
                <h3 className="text-2xl font-bold text-white mb-6">📅 Timeline of Events</h3>
                {timeline.timeline_events.map((event, index) => (
                  <div key={index} className="relative">
                    {/* Timeline Line */}
                    {index < timeline.timeline_events.length - 1 && (
                      <div className="absolute left-8 top-16 w-0.5 h-full bg-gradient-to-b from-cyan-400 to-violet-400"></div>
                    )}
                    
                    {/* Event Card */}
                    <div className="flex items-start space-x-6">
                      <div className="flex-shrink-0 w-16 h-16 bg-gradient-to-br from-cyan-400 to-violet-400 rounded-full flex items-center justify-center text-white font-bold text-lg shadow-lg shadow-cyan-400/25">
                        {event.year}
                      </div>
                      <div className="flex-1 bg-white/10 rounded-xl p-6 border border-white/20 hover:bg-white/15 transition-all">
                        <div className="flex flex-wrap items-center gap-4 mb-3">
                          <span className="text-cyan-400 font-bold text-lg">{event.date}</span>
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                            event.probability === 'High' ? 'bg-green-500/20 text-green-400' :
                            event.probability === 'Medium' ? 'bg-yellow-500/20 text-yellow-400' :
                            'bg-red-500/20 text-red-400'
                          }`}>
                            {event.probability} Probability
                          </span>
                        </div>
                        <h4 className="text-white font-bold text-xl mb-3">{event.event}</h4>
                        <p className="text-gray-300 leading-relaxed">{event.impact}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Historical Context */}
              {timeline.historical_context && timeline.historical_context.length > 0 && (
                <div className="mt-12">
                  <h3 className="text-xl font-bold text-white mb-4">📖 Historical Context</h3>
                  <div className="bg-white/10 rounded-xl p-6 border border-white/20">
                    <ul className="space-y-3">
                      {timeline.historical_context.map((context, index) => (
                        <li key={index} className="text-gray-300 text-sm leading-relaxed">
                          • {context}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;