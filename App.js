import React, { useState } from "react";
import axios from "axios";

function App() {
  const [file, setFile] = useState(null);
  const [reviewer, setReviewer] = useState("");
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => setFile(e.target.files[0]);

  const handleUpload = async () => {
    if (!file) return alert("Please select a file");
    setLoading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post(
        "http://127.0.0.1:8000/generate-reviewer",
        formData
      );
      setReviewer(res.data.reviewer);
    } catch (err) {
      console.error(err);
      alert(err.response?.data?.error || "Error generating reviewer");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: "50px" }}>
      <h1>Reviewer Generator</h1>
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleUpload} disabled={loading} style={{ marginLeft: "10px" }}>
        {loading ? "Generating..." : "Generate Reviewer"}
      </button>
      <div style={{ marginTop: "20px", whiteSpace: "pre-wrap" }}>
        {reviewer}
      </div>
    </div>
  );
}

export default App;
