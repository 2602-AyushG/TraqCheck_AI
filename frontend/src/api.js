const BASE_URL = "http://127.0.0.1:5000";
export async function uploadResume(file) {
  const formData = new FormData();
  formData.append("resume", file);

  const res = await fetch(`${BASE_URL}/candidates/upload`, {
    method: "POST",
    body: formData,
  });

  return res.json();
}

export async function getCandidates() {
  const res = await fetch(`${BASE_URL}/candidates`);
  return res.json();
}

export async function getCandidate(id) {
  const res = await fetch(`${BASE_URL}/candidates/${id}`);
  return res.json();
}

export async function requestDocuments(id) {
  const res = await fetch(
    `${BASE_URL}/candidates/${id}/request-documents`,
    {
      method: "POST",
    }
  );

  return res.json();
}

export async function submitDocuments(id, panFile, aadhaarFile) {
  const formData = new FormData();

  if (panFile) {
    formData.append("pan", panFile);
  }

  if (aadhaarFile) {
    formData.append("aadhaar", aadhaarFile);
  }

  const res = await fetch(
    `${BASE_URL}/candidates/${id}/submit-documents`,
    {
      method: "POST",
      body: formData,
    }
  );

  return res.json();
}