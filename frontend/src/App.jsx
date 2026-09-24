import { useState, useEffect } from "react";
import "./App.css";

import {
  uploadResume,
  getCandidates,
  getCandidate,
  requestDocuments,
  submitDocuments,
} from "./api.js";

const STATUS_LABELS = {
  parsed: "Parsed",
  documents_requested: "Documents requested",
  documents_submitted: "Documents submitted",
  parse_failed: "Parse failed",
};

function StatusBadge({ status }) {
  const known = STATUS_LABELS[status];
  return (
    <span className={`badge badge-${known ? status : "default"}`}>
      {known || status || "Unknown"}
    </span>
  );
}

function App() {
  const [candidates, setCandidates] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [selectedCandidate, setSelectedCandidate] = useState(null);

  const [uploading, setUploading] = useState(false);

  const [panFile, setPanFile] = useState(null);
  const [aadhaarFile, setAadhaarFile] = useState(null);

  const loadCandidates = async () => {
    const data = await getCandidates();
    setCandidates(data);
  };

  useEffect(() => {
    loadCandidates();
  }, []);

  // Upload resume
  const handleUpload = async (e) => {
    const file = e.target.files[0];

    if (!file) return;

    setUploading(true);

    try {
      await uploadResume(file);
      await loadCandidates();
    } catch (err) {
      alert("Upload failed: " + err.message);
    }

    setUploading(false);
  };

  // Open candidate details
  const openCandidate = async (id) => {
    setSelectedId(id);

    const data = await getCandidate(id);

    setSelectedCandidate(data);
  };

  // Request PAN/Aadhaar
  const handleRequestDocs = async () => {
    await requestDocuments(selectedId);

    await openCandidate(selectedId);
    await loadCandidates();
  };

  // Submit PAN/Aadhaar
  const handleSubmitDocs = async () => {
    if (!panFile && !aadhaarFile) {
      alert("Select at least one file");
      return;
    }

    await submitDocuments(selectedId, panFile, aadhaarFile);

    setPanFile(null);
    setAadhaarFile(null);

    await openCandidate(selectedId);
    await loadCandidates();
  };

  return (
    <div className="app">
      <header className="navbar">
        <span className="navbar-logo">TraqCheck AI</span>
        <span className="navbar-subtitle">AI-powered candidate onboarding</span>
      </header>

      <div className="page">
        <section className="hero">
          <span className="hero-badge">✦ AI-powered onboarding</span>
          <h1>
            <span className="hero-highlight">Candidate</span> Onboarding
          </h1>
          <p className="hero-desc">
            Upload a resume to parse candidate details automatically, then
            manage document verification from one place.
          </p>
          {candidates.length > 0 && (
            <span className="hero-stat">
              {candidates.length} candidate{candidates.length === 1 ? "" : "s"}
            </span>
          )}
        </section>

        {/* Upload */}
        <section className="upload-card">
          <div className="upload-icon" aria-hidden="true">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
              <path
                d="M12 16V4M12 4L7 9M12 4l5 5M5 20h14"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>

          <div className="upload-body">
            <div className="upload-title">Upload Candidate Resume</div>
            <div className="upload-hint">PDF or DOCX</div>
            {uploading && (
              <div className="upload-status">Uploading and parsing…</div>
            )}
          </div>

          <div className="upload-action">
            <div className="file-input-wrap">
              <button className="btn btn-primary" type="button" disabled={uploading}>
                {uploading ? "Uploading…" : "Choose Resume"}
              </button>
              <input
                type="file"
                accept=".pdf,.docx"
                onChange={handleUpload}
                disabled={uploading}
                aria-label="Upload candidate resume"
              />
            </div>
          </div>
        </section>

        <div className="content-grid">
          {/* Candidate list */}
          <section className="panel surface-box">
            <div className="panel-header">
              <h2>Candidates</h2>
            </div>

            <div className="panel-body">
              {candidates.length === 0 ? (
                <div className="empty-state">
                  <h3>No candidates yet</h3>
                  <p>Upload a resume to start the onboarding workflow.</p>
                </div>
              ) : (
                candidates.map((candidate) => (
                  <div
                    key={candidate.id}
                    role="button"
                    tabIndex={0}
                    className={`candidate-row${
                      candidate.id === selectedId ? " selected" : ""
                    }`}
                    onClick={() => openCandidate(candidate.id)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        openCandidate(candidate.id);
                      }
                    }}
                  >
                    <span className="candidate-name">
                      {candidate.name || "-"}
                    </span>
                    <span className="candidate-meta">
                      {candidate.email || "-"}
                    </span>
                    <span className="candidate-meta">
                      {candidate.company || "-"}
                    </span>
                    <StatusBadge status={candidate.status} />
                  </div>
                ))
              )}
            </div>
          </section>

          {/* Candidate details */}
          {selectedCandidate && (
            <section className="panel surface-box">
              <div className="details-section">
                <div className="details-name">
                  {selectedCandidate.name || "Unnamed"}
                </div>
                {selectedCandidate.designation && (
                  <div className="details-role">
                    {selectedCandidate.designation}
                  </div>
                )}
                <div style={{ marginTop: 10 }}>
                  <StatusBadge status={selectedCandidate.status} />
                </div>
              </div>

              <div className="details-section">
                <h3>Contact</h3>
                <div className="field-list">
                  <span className="field-label">Email</span>
                  <span className="field-value">
                    {selectedCandidate.email || "-"}
                  </span>
                  <span className="field-label">Phone</span>
                  <span className="field-value">
                    {selectedCandidate.phone || "-"}
                  </span>
                  <span className="field-label">Company</span>
                  <span className="field-value">
                    {selectedCandidate.company || "-"}
                  </span>
                </div>
              </div>

              {(selectedCandidate.skills || []).length > 0 && (
                <div className="details-section">
                  <h3>Skills</h3>
                  <div className="skills-wrap">
                    {selectedCandidate.skills.map((skill, i) => (
                      <span className="skill-chip" key={i}>
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="details-section">
                <h3>Document verification</h3>

                <div className="section-actions">
                  <button className="btn btn-primary" onClick={handleRequestDocs}>
                    Request Documents
                  </button>
                </div>

                {selectedCandidate.document_request_text && (
                  <div className="doc-request-msg">
                    {selectedCandidate.document_request_text}
                  </div>
                )}

                <div className="doc-uploads">
                  <div className="doc-upload-box surface-box">
                    <label htmlFor="pan-upload">PAN</label>
                    <input
                      id="pan-upload"
                      type="file"
                      onChange={(e) => setPanFile(e.target.files[0])}
                    />
                    {panFile && (
                      <div className="filename">{panFile.name}</div>
                    )}
                  </div>

                  <div className="doc-upload-box surface-box">
                    <label htmlFor="aadhaar-upload">Aadhaar</label>
                    <input
                      id="aadhaar-upload"
                      type="file"
                      onChange={(e) => setAadhaarFile(e.target.files[0])}
                    />
                    {aadhaarFile && (
                      <div className="filename">{aadhaarFile.name}</div>
                    )}
                  </div>
                </div>

                <div className="section-actions">
                  <button className="btn btn-secondary" onClick={handleSubmitDocs}>
                    Submit Documents
                  </button>
                </div>

                {(selectedCandidate.documents || []).length > 0 && (
                  <ul className="doc-list">
                    {selectedCandidate.documents.map((document, index) => (
                      <li key={index}>{document.type}</li>
                    ))}
                  </ul>
                )}
              </div>
            </section>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;