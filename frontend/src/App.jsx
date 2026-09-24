import { useState, useEffect } from "react";

import {
  uploadResume,
  getCandidates,
  getCandidate,
  requestDocuments,
  submitDocuments,
} from "./api.js";

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

    await submitDocuments(
      selectedId,
      panFile,
      aadhaarFile
    );

    setPanFile(null);
    setAadhaarFile(null);

    await openCandidate(selectedId);
    await loadCandidates();
  };

  return (
    <div
      style={{
        padding: "2rem",
        fontFamily: "Arial, sans-serif",
      }}
    >
      <h1>Candidate AI System</h1>

      {/* Upload */}
      <section style={{ marginBottom: "2rem" }}>
        <h2>Upload Resume</h2>

        <input
          type="file"
          accept=".pdf,.docx"
          onChange={handleUpload}
          disabled={uploading}
        />

        {uploading && <p>Uploading and parsing...</p>}
      </section>

      <div
        style={{
          display: "flex",
          gap: "2rem",
        }}
      >
        {/* Candidate list */}
        <section style={{ flex: 1 }}>
          <h2>Candidates</h2>

          <table
            border="1"
            cellPadding="8"
            style={{
              borderCollapse: "collapse",
              width: "100%",
            }}
          >
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Company</th>
                <th>Status</th>
              </tr>
            </thead>

            <tbody>
              {candidates.map((candidate) => (
                <tr
                  key={candidate.id}
                  onClick={() =>
                    openCandidate(candidate.id)
                  }
                  style={{ cursor: "pointer" }}
                >
                  <td>{candidate.name || "-"}</td>

                  <td>{candidate.email || "-"}</td>

                  <td>{candidate.company || "-"}</td>

                  <td>{candidate.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        {/* Candidate details */}
        {selectedCandidate && (
          <section
            style={{
              flex: 1,
              border: "1px solid #ccc",
              padding: "1rem",
            }}
          >
            <h2>
              {selectedCandidate.name || "Unnamed"}
            </h2>

            <p>
              Email: {selectedCandidate.email || "-"}
            </p>

            <p>
              Phone: {selectedCandidate.phone || "-"}
            </p>

            <p>
              Company: {selectedCandidate.company || "-"}
            </p>

            <p>
              Designation:{" "}
              {selectedCandidate.designation || "-"}
            </p>

            <p>
              Status: {selectedCandidate.status}
            </p>

            <p>
              Skills:{" "}
              {(selectedCandidate.skills || []).join(", ")}
            </p>

            <hr />

            {/* Request documents */}
            <h3>Documents</h3>

            <button onClick={handleRequestDocs}>
              Request Documents
            </button>

            {selectedCandidate.document_request_text && (
              <p>
                <em>
                  {selectedCandidate.document_request_text}
                </em>
              </p>
            )}

            {/* Submit documents */}
            <h3>Submit Documents</h3>

            <div>
              <label>
                PAN:
                <input
                  type="file"
                  onChange={(e) =>
                    setPanFile(e.target.files[0])
                  }
                />
              </label>
            </div>

            <br />

            <div>
              <label>
                Aadhaar:
                <input
                  type="file"
                  onChange={(e) =>
                    setAadhaarFile(e.target.files[0])
                  }
                />
              </label>
            </div>

            <br />

            <button onClick={handleSubmitDocs}>
              Submit Documents
            </button>

            <ul>
              {(selectedCandidate.documents || []).map(
                (document, index) => (
                  <li key={index}>
                    {document.type}
                  </li>
                )
              )}
            </ul>
          </section>
        )}
      </div>
    </div>
  );
}

export default App;