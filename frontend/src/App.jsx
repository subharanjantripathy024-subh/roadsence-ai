import { useEffect, useState } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";

/* =========================================================
   GEOJSON UPLOAD COMPONENT
   ========================================================= */

function UploadGeoJSON({ onUpload }) {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");
  const [uploading, setUploading] = useState(false);

  const handleUpload = async () => {
    if (!file) {
      setMessage("Please select a GeoJSON file.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setUploading(true);
    setMessage("");

    try {
      const response = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Upload failed."
        );
      }

      setMessage(
        `GeoJSON uploaded successfully: ${
          data.filename || file.name
        }`
      );

      setFile(null);

      await onUpload();
    } catch (error) {
      console.error(error);

      setMessage(
        error.message || "Upload failed."
      );
    } finally {
      setUploading(false);
    }
  };

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Update Road Damage Data</h2>
        <span>M2 GeoJSON</span>
      </div>

      <input
        type="file"
        accept=".geojson,application/geo+json"
        onChange={(event) =>
          setFile(event.target.files[0] || null)
        }
      />

      {file && (
        <p className="message">
          Selected file: {file.name}
        </p>
      )}

      <button
        onClick={handleUpload}
        disabled={uploading}
      >
        {uploading
          ? "Uploading..."
          : "Upload GeoJSON"}
      </button>

      {message && (
        <p className="message">
          {message}
        </p>
      )}
    </section>
  );
}


/* =========================================================
   VIDEO UPLOAD COMPONENT
   ========================================================= */

function UploadVideo({ onProcessed }) {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");
  const [result, setResult] = useState(null);
  const [processing, setProcessing] = useState(false);

  const handleProcess = async () => {
    if (!file) {
      setMessage("Please select a road video.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setProcessing(true);
    setMessage("");
    setResult(null);

    try {
      const response = await fetch("/api/upload-video", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            data.message ||
            "Video processing failed."
        );
      }

      setResult(data);

      setMessage(
        "Video processed successfully. Dashboard updated."
      );

      setFile(null);

      await onProcessed();
    } catch (error) {
      console.error(error);

      setMessage(
        error.message ||
          "Video processing failed."
      );
    } finally {
      setProcessing(false);
    }
  };

  return (
    <section className="panel">

      <div className="panel-header">
        <h2>Process Road Video</h2>
        <span>M1 Vision Pipeline</span>
      </div>

      <input
        type="file"
        accept="video/mp4,video/avi,video/quicktime,video/x-matroska,.mp4,.avi,.mov,.mkv"
        onChange={(event) =>
          setFile(event.target.files[0] || null)
        }
      />

      {file && (
        <p className="message">
          Selected video: {file.name}
        </p>
      )}

      <button
        onClick={handleProcess}
        disabled={processing || !file}
      >
        {processing
          ? "Processing video..."
          : "Upload & Process Video"}
      </button>

      {processing && (
        <p className="message">
          Extracting frames and running road-damage
          detection. This may take some time on CPU.
        </p>
      )}

      {message && (
        <p className={result ? "message" : "error"}>
          {message}
        </p>
      )}

      {result && (
        <div className="message">

          <strong>
            Processing Result
          </strong>

          <p>
            Detections: {result.detections}
          </p>

          <p>
            Damage Instances: {result.damage_instances}
          </p>

          <p>
            Estimated Repair Cost: ₹
            {Number(
              result.total_estimated_cost || 0
            ).toLocaleString("en-IN")}
          </p>

          {result.gps_note && (
            <small>
              {result.gps_note}
            </small>
          )}

        </div>
      )}

    </section>
  );
}


/* =========================================================
   DAMAGE MAP
   ========================================================= */

function DamageMap({ damages }) {

  // Only use real GPS coordinates for the map.
  const mappedDamages = damages.filter(
    (item) =>
      item.latitude !== null &&
      item.latitude !== undefined &&
      item.longitude !== null &&
      item.longitude !== undefined &&
      Number(item.latitude) !== 0 &&
      Number(item.longitude) !== 0 &&
      Number.isFinite(Number(item.latitude)) &&
      Number.isFinite(Number(item.longitude))
  );

  // No GPS available.
  if (mappedDamages.length === 0) {
    return (
      <div className="message">
        No GPS coordinates are available for the
        processed video. Damage detection and
        prioritization are still available below.
      </div>
    );
  }

  const defaultPosition = [
    Number(mappedDamages[0].latitude),
    Number(mappedDamages[0].longitude),
  ];

  return (
    <MapContainer
      center={defaultPosition}
      zoom={13}
      style={{
        height: "450px",
        width: "100%",
        borderRadius: "12px",
      }}
    >

      <TileLayer
        attribution="&copy; OpenStreetMap contributors"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {mappedDamages.map((item) => (
        <Marker
          key={item.damage_id}
          position={[
            Number(item.latitude),
            Number(item.longitude),
          ]}
        >

          <Popup>

            <strong>
              {item.damage_type}
            </strong>

            <br />

            Severity: {item.severity}

            <br />

            Priority: {item.priority}

            <br />

            Repair Cost: ₹
            {Number(
              item.estimated_repair_cost || 0
            ).toLocaleString("en-IN")}

            <br />

            Status: {item.status}

            <br />

            Confidence:{" "}
            {(
              Number(item.confidence || 0) * 100
            ).toFixed(1)}
            %

          </Popup>

        </Marker>
      ))}

    </MapContainer>
  );
}


/* =========================================================
   AI AGENT CHAT COMPONENT
   ========================================================= */

function AgentChat() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [intent, setIntent] = useState("");
  const [loading, setLoading] = useState(false);

  const askAgent = async () => {
    if (!question.trim()) {
      return;
    }

    setLoading(true);
    setAnswer("");
    setIntent("");

    try {
      const response = await fetch(
        "/api/agent/ask",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            question: question.trim(),
            session_id: "demo",
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Agent request failed."
        );
      }

      setAnswer(
        data.answer ||
          "No answer returned."
      );

      setIntent(
        data.intent || ""
      );

    } catch (error) {
      console.error(error);

      setAnswer(
        "Unable to get a response from the RoadSense AI Agent."
      );

    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (event) => {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();
      askAgent();
    }
  };

  return (
    <section className="panel">

      <div className="panel-header">

        <h2>
          Ask RoadSense AI
        </h2>

        <span>
          AI Agent
        </span>

      </div>

      <input
        type="text"
        value={question}
        placeholder="Ask about detected road damage..."
        onChange={(event) =>
          setQuestion(event.target.value)
        }
        onKeyDown={handleKeyDown}
      />

      <button
        onClick={askAgent}
        disabled={loading}
      >
        {loading
          ? "Thinking..."
          : "Ask AI"}
      </button>

      {answer && (
        <div className="message">

          <strong>
            RoadSense AI:
          </strong>

          <p>
            {answer}
          </p>

          {intent && (
            <small>
              Intent: {intent}
            </small>
          )}

        </div>
      )}

    </section>
  );
}


/* =========================================================
   MAIN APP
   ========================================================= */

function App() {

  const [detections, setDetections] =
    useState([]);

  const [tracking, setTracking] =
    useState(null);

  const [damages, setDamages] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");


  /* -------------------------------------------------------
     LOAD DASHBOARD DATA
     ------------------------------------------------------- */

  const loadDashboardData = async () => {

    try {

      setError("");

      const [
        detectionsResponse,
        trackingResponse,
        damagesResponse,
      ] = await Promise.all([

        fetch(
          "/api/m1/detections"
        ),

        fetch(
          "/api/tracking/summary"
        ),

        fetch(
          "/api/damages"
        ),

      ]);

      if (
        !detectionsResponse.ok
      ) {
        throw new Error(
          "Failed to fetch detections."
        );
      }

      if (
        !trackingResponse.ok
      ) {
        throw new Error(
          "Failed to fetch tracking data."
        );
      }

      if (
        !damagesResponse.ok
      ) {
        throw new Error(
          "Failed to fetch M2 damage data."
        );
      }

      const detectionsData =
        await detectionsResponse.json();

      const trackingData =
        await trackingResponse.json();

      const damagesData =
        await damagesResponse.json();

      setDetections(
        detectionsData
      );

      setTracking(
        trackingData
      );

      setDamages(
        damagesData
      );

    } catch (err) {

      console.error(err);

      setError(
        "Unable to connect to RoadSense backend."
      );

    } finally {

      setLoading(false);

    }
  };


  useEffect(() => {
    loadDashboardData();
  }, []);


  /* -------------------------------------------------------
     CALCULATIONS
     ------------------------------------------------------- */

  const potholes =
    detections.filter(
      (item) =>
        item.damage_type?.toLowerCase() ===
        "pothole"
    ).length;


  const critical =
    detections.filter(
      (item) =>
        item.severity ===
        "critical"
    ).length;


  const high =
    detections.filter(
      (item) =>
        item.severity ===
        "high"
    ).length;


  const pendingRepairs =
    damages.filter(
      (item) =>
        item.status ===
        "pending"
    ).length;


  const priorityOne =
    damages.filter(
      (item) =>
        Number(item.priority) ===
        1
    ).length;


  const totalRepairCost =
    damages.reduce(
      (total, item) =>
        total +
        Number(
          item.estimated_repair_cost ||
            0
        ),
      0
    );


  // Count only damages which contain
  // actual GPS coordinates.
  const mappedDamageCount =
    damages.filter(
      (item) =>
        item.latitude !== null &&
        item.latitude !== undefined &&
        item.longitude !== null &&
        item.longitude !== undefined &&
        Number(item.latitude) !== 0 &&
        Number(item.longitude) !== 0 &&
        Number.isFinite(Number(item.latitude)) &&
        Number.isFinite(Number(item.longitude))
    ).length;


  /* =======================================================
     PAGE
     ======================================================= */

  return (
    <div className="app">

      {/* =================================================
          HEADER
          ================================================= */}

      <header className="header">

        <div>

          <h1>
            RoadSense AI
          </h1>

          <p>
            Intelligent Road Damage Detection
          </p>

        </div>

        <div className="status">
          ● Backend Connected
        </div>

      </header>


      <main className="dashboard">

        {/* =================================================
            GEOJSON UPLOAD
            ================================================= */}

        <UploadGeoJSON
          onUpload={
            loadDashboardData
          }
        />


        {/* =================================================
            VIDEO UPLOAD
            ================================================= */}

        <UploadVideo
          onProcessed={
            loadDashboardData
          }
        />


        {/* =================================================
            M1 SUMMARY
            ================================================= */}

        <section className="stats">

          <div className="card">

            <span>
              Total Detections
            </span>

            <strong>
              {detections.length}
            </strong>

          </div>


          <div className="card">

            <span>
              Potholes
            </span>

            <strong>
              {potholes}
            </strong>

          </div>


          <div className="card">

            <span>
              High Severity
            </span>

            <strong>
              {high}
            </strong>

          </div>


          <div className="card">

            <span>
              Critical
            </span>

            <strong>
              {critical}
            </strong>

          </div>

        </section>


        {/* =================================================
            ERROR
            ================================================= */}

        {error && (
          <section className="panel">

            <p className="error">
              {error}
            </p>

          </section>
        )}


        {/* =================================================
            TRACKING
            ================================================= */}

        <section className="panel">

          <div className="panel-header">

            <h2>
              Tracking Analysis
            </h2>

            <span>
              ByteTrack
            </span>

          </div>


          {tracking && (
            <div className="stats">

              <div className="card">

                <span>
                  Tracked Detections
                </span>

                <strong>
                  {
                    tracking.total_tracked_detections
                  }
                </strong>

              </div>


              <div className="card">

                <span>
                  Tracked Objects
                </span>

                <strong>
                  {
                    tracking.unique_tracked_objects
                  }
                </strong>

              </div>


              <div className="card">

                <span>
                  Pothole Tracks
                </span>

                <strong>
                  {
                    tracking.unique_pothole_tracks
                  }
                </strong>

              </div>

            </div>
          )}

        </section>


        {/* =================================================
            MAP
            ================================================= */}

        <section className="panel">

          <div className="panel-header">

            <h2>
              Road Damage Map
            </h2>

            <span>
              {mappedDamageCount} mapped instances
            </span>

          </div>


          {!loading &&
            !error &&
            damages.length > 0 && (

              <DamageMap
                damages={damages}
              />

            )}


          {!loading &&
            !error &&
            damages.length === 0 && (

              <p className="message">
                No damage instances available.
              </p>

            )}

        </section>


        {/* =================================================
            M2 DAMAGE PRIORITIZATION
            ================================================= */}

        <section className="panel">

          <div className="panel-header">

            <h2>
              M2 Damage Prioritization
            </h2>

            <span>
              {damages.length} instances
            </span>

          </div>


          <section className="stats">

            <div className="card">

              <span>
                Damage Instances
              </span>

              <strong>
                {damages.length}
              </strong>

            </div>


            <div className="card">

              <span>
                Pending Repairs
              </span>

              <strong>
                {pendingRepairs}
              </strong>

            </div>


            <div className="card">

              <span>
                Priority 1
              </span>

              <strong>
                {priorityOne}
              </strong>

            </div>


            <div className="card">

              <span>
                Estimated Repair Cost
              </span>

              <strong>
                ₹
                {totalRepairCost.toLocaleString(
                  "en-IN"
                )}
              </strong>

            </div>

          </section>


          {!loading &&
            !error &&
            damages.length > 0 && (

              <div className="table-container">

                <table>

                  <thead>

                    <tr>

                      <th>
                        Damage ID
                      </th>

                      <th>
                        Damage Type
                      </th>

                      <th>
                        Severity
                      </th>

                      <th>
                        Priority
                      </th>

                      <th>
                        Repair Cost
                      </th>

                      <th>
                        Status
                      </th>

                      <th>
                        Confidence
                      </th>

                    </tr>

                  </thead>


                  <tbody>

                    {damages.map(
                      (item) => (

                        <tr
                          key={
                            item.damage_id
                          }
                        >

                          <td>
                            {
                              item.damage_id
                            }
                          </td>

                          <td>
                            {
                              item.damage_type
                            }
                          </td>

                          <td>

                            <span
                              className={`severity ${item.severity}`}
                            >
                              {
                                item.severity
                              }
                            </span>

                          </td>

                          <td>
                            {
                              item.priority
                            }
                          </td>

                          <td>
                            ₹
                            {Number(
                              item.estimated_repair_cost ||
                                0
                            ).toLocaleString(
                              "en-IN"
                            )}
                          </td>

                          <td>
                            {
                              item.status
                            }
                          </td>

                          <td>
                            {(
                              Number(
                                item.confidence ||
                                  0
                              ) * 100
                            ).toFixed(1)}
                            %
                          </td>

                        </tr>

                      )
                    )}

                  </tbody>

                </table>

              </div>

            )}

        </section>


        {/* =================================================
            M1 DETECTIONS
            ================================================= */}

        <section className="panel">

          <div className="panel-header">

            <h2>
              Road Damage Detections
            </h2>

            <span>
              {detections.length} records
            </span>

          </div>


          {loading && (
            <p className="message">
              Loading detections...
            </p>
          )}


          {!loading &&
            !error &&
            detections.length === 0 && (

              <p className="message">
                No detections available.
              </p>

            )}


          {!loading &&
            !error &&
            detections.length > 0 && (

              <div className="table-container">

                <table>

                  <thead>

                    <tr>

                      <th>
                        Damage
                      </th>

                      <th>
                        Confidence
                      </th>

                      <th>
                        Severity
                      </th>

                      <th>
                        Priority
                      </th>

                      <th>
                        Latitude
                      </th>

                      <th>
                        Longitude
                      </th>

                      <th>
                        Frame
                      </th>

                    </tr>

                  </thead>


                  <tbody>

                    {detections.map(
                      (item) => (

                        <tr
                          key={
                            item.detection_id
                          }
                        >

                          <td>
                            {
                              item.damage_type
                            }
                          </td>

                          <td>
                            {(
                              Number(
                                item.confidence || 0
                              ) * 100
                            ).toFixed(1)}
                            %
                          </td>

                          <td>

                            <span
                              className={`severity ${item.severity}`}
                            >
                              {
                                item.severity
                              }
                            </span>

                          </td>

                          <td>
                            {
                              item.priority ??
                              "—"
                            }
                          </td>

                          <td>
                            {
                              item.latitude ??
                              "—"
                            }
                          </td>

                          <td>
                            {
                              item.longitude ??
                              "—"
                            }
                          </td>

                          <td>
                            {
                              item.frame_id
                            }
                          </td>

                        </tr>

                      )
                    )}

                  </tbody>

                </table>

              </div>

            )}

        </section>


        {/* =================================================
            AI AGENT
            ================================================= */}

        <AgentChat />

      </main>

    </div>
  );
}


export default App;