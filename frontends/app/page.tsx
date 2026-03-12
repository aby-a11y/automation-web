"use client";

import { useState } from "react";
import StatusTable from "@/components/StatusTable";

type Job = {
  id: string;
  url: string;
  status: "queued" | "running" | "success" | "failed" | "skipped";
  message: string;
};

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export default function Home() {
  const [urls, setUrls] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [message, setMessage] = useState("");
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async () => {
    // Validation
    const urlList = urls.split("\n").map((u) => u.trim()).filter(Boolean);
    if (urlList.length === 0) return setError("Kam se kam ek URL daalo!");
    if (!name || !email || !message) return setError("Naam, Email aur Message zaruri hain!");
    if (urlList.length > 50) return setError("Maximum 50 URLs allowed hain!");

    setError("");
    setLoading(true);
    setJobs([]);

    try {
      // Backend ko submit karo
      const res = await fetch(`${BACKEND_URL}/api/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          urls: urlList,
          name,
          email,
          phone,
          message,
        }),
      });

      const data = await res.json();
      const { batch_id } = data;

      // SSE se real-time updates lo
      const eventSource = new EventSource(
        `${BACKEND_URL}/api/status/${batch_id}`
      );

      eventSource.onmessage = (e) => {
        const updatedJobs: Job[] = JSON.parse(e.data);
        setJobs(updatedJobs);

        // Sab complete ho gaye?
        const allDone = updatedJobs.every((j) =>
          ["success", "failed", "skipped"].includes(j.status)
        );
        if (allDone) {
          eventSource.close();
          setLoading(false);
        }
      };

      eventSource.onerror = () => {
        eventSource.close();
        setLoading(false);
      };

    } catch (err) {
      setError("Backend se connect nahi ho paya. Server chal raha hai?");
      setLoading(false);
    }
  };

  const handleClear = () => {
    setUrls("");
    setName("");
    setEmail("");
    setPhone("");
    setMessage("");
    setJobs([]);
    setError("");
  };

  return (
    <main className="min-h-screen bg-gray-50 py-10 px-4">
      <div className="max-w-3xl mx-auto">

        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800">🤖 Contact Form Agent</h1>
          <p className="text-gray-500 mt-2">
            Multiple websites ki contact forms automatically fill karo
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">

          {/* URLs Input */}
          <div className="mb-5">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Website URLs{" "}
              <span className="text-gray-400 font-normal">(ek line mein ek, max 50)</span>
            </label>
            <textarea
              className="w-full border border-gray-300 rounded-xl p-3 text-sm h-36 
                         focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              placeholder={"https://agency1.com\nhttps://agency2.com\nhttps://agency3.com"}
              value={urls}
              onChange={(e) => setUrls(e.target.value)}
              disabled={loading}
            />
            <p className="text-xs text-gray-400 mt-1">
              {urls.split("\n").filter(Boolean).length} URLs entered
            </p>
          </div>

          {/* Your Details */}
          <div className="grid grid-cols-2 gap-4 mb-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Aapka Naam *
              </label>
              <input
                type="text"
                className="w-full border border-gray-300 rounded-xl p-3 text-sm
                           focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Rahul Sharma"
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={loading}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email *
              </label>
              <input
                type="email"
                className="w-full border border-gray-300 rounded-xl p-3 text-sm
                           focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="rahul@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={loading}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Phone Number
              </label>
              <input
                type="tel"
                className="w-full border border-gray-300 rounded-xl p-3 text-sm
                           focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="9999999999"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                disabled={loading}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Subject / Service
              </label>
              <input
                type="text"
                className="w-full border border-gray-300 rounded-xl p-3 text-sm
                           focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Web Development Services"
                disabled={loading}
              />
            </div>
          </div>

          {/* Message */}
          <div className="mb-5">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Message *
            </label>
            <textarea
              className="w-full border border-gray-300 rounded-xl p-3 text-sm h-28
                         focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              placeholder="Hello, main apni web development services offer karna chahta hoon..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              disabled={loading}
            />
          </div>

          {/* Error */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl 
                            text-red-600 text-sm">
              ⚠️ {error}
            </div>
          )}

          {/* Buttons */}
          <div className="flex gap-3">
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300
                         text-white font-medium py-3 rounded-xl transition-colors"
            >
              {loading ? "🔄 Agent Kaam Kar Raha Hai..." : "🚀 Start Agent"}
            </button>
            <button
              onClick={handleClear}
              disabled={loading}
              className="px-6 bg-gray-100 hover:bg-gray-200 disabled:opacity-50
                         text-gray-600 font-medium py-3 rounded-xl transition-colors"
            >
              Clear
            </button>
          </div>
        </div>

        {/* Results */}
        <StatusTable jobs={jobs} />

      </div>
    </main>
  );
}
