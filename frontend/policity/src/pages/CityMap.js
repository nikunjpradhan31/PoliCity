import React, { useState, useEffect, useCallback } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import "../animations.css";
import {
    MapContainer,
    TileLayer,
    useMap,
    useMapEvents,
    CircleMarker,
    Popup,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";

const MapPoint = ({ point, onGenerate }) => {
    const GOOGLE_API_KEY = process.env.REACT_APP_GOOGLE_MAPS_API_KEY;
    const [lat, lng] = point.position;
    const streetViewUrl = `https://www.google.com/maps/embed/v1/streetview?key=${GOOGLE_API_KEY}&location=${lat},${lng}`;

    const getColor = (classification) => {
        switch (classification?.toLowerCase()) {
            case "parking":
                return "#42c3cf";
            case "pothole":
                return "#e74c3c";
            case "trash":
                return "#9b59b6";
            case "water & santitation":
                return "#3498db";
            case "street lighting":
                return "#6be346";
            case "traffic sign":
                return "#f1c40f";
            default:
                return "#ed3ef0";
        }
    };

    return (
        <CircleMarker
            center={point.position}
            radius={8}
            pathOptions={{
                color: getColor(point.type),
                fillColor: getColor(point.type),
                fillOpacity: 0.7,
                weight: 2,
            }}
        >
            <Popup
                autoPan={true}
                minWidth={340}
                maxWidth={400}
                minHeight={200}
                maxHeight={450}
            >
                <div
                    style={{
                        textAlign: "center",
                        fontFamily: "sans-serif",
                        padding: "5px",
                    }}
                >
                    <strong
                        style={{
                            color: getColor(point.type),
                            fontSize: "16px",
                        }}
                    >
                        {point.type ? point.type.toUpperCase() : "UNKNOWN"}
                    </strong>
                    <p
                        style={{
                            margin: "8px 0 15px 0",
                            fontSize: "14px",
                            maxHeight: "80px",
                            overflowY: "auto",
                            textAlign: "left",
                            padding: "0 10px",
                        }}
                    >
                        {point.summary || "No description provided."}
                    </p>
                    <div
                        style={{
                            borderRadius: "8px",
                            overflow: "hidden",
                            border: "1px solid #ccc",
                            marginBottom: "10px",
                        }}
                    >
                        <iframe
                            width="400"
                            height="220"
                            style={{ border: 0, display: "block" }}
                            loading="lazy"
                            allowFullScreen
                            src={streetViewUrl}
                            title={`Street view of ${point.type}`}
                        ></iframe>
                    </div>

                    <button
                        onClick={() => onGenerate(point)}
                        className="btn-hover"
                        style={{
                            padding: "8px 15px",
                            fontSize: "14px",
                            fontWeight: "bold",
                            backgroundColor: getColor(point.type),
                            color: "white",
                            border: "none",
                            borderRadius: "6px",
                            cursor: "pointer",
                            width: "100%",
                            boxShadow: "0 2px 4px rgba(0,0,0,0.2)",
                        }}
                    >
                        Generate Report for this {point.type}
                    </button>
                </div>
            </Popup>
        </CircleMarker>
    );
};

const MapBoundsTracker = ({ onBoundsChange }) => {
    const map = useMapEvents({
        moveend: () => {
            const bounds = map.getBounds();
            onBoundsChange({
                topLat: bounds.getNorth(),
                bottomLat: bounds.getSouth(),
                leftLng: bounds.getWest(),
                rightLng: bounds.getEast(),
            });
        },
    });
    return null;
};

const ChangeMapView = ({ center }) => {
    const map = useMap();

    useEffect(() => {
        if (center) {
            map.flyTo(center, 13);
        }
    }, [center, map]);

    return null;
};

const CityMap = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const city = location.state?.city || "London";

    const [coords, setCoords] = useState(null);
    const [reportData, setReportData] = useState([]);

    const [isGenerating, setIsGenerating] = useState(false);

    useEffect(() => {
        fetch(
            `https://nominatim.openstreetmap.org/search?format=json&q=${city}`,
        )
            .then((res) => res.json())
            .then((data) => {
                if (data && data.length > 0) {
                    setCoords([
                        parseFloat(data[0].lat),
                        parseFloat(data[0].lon),
                    ]);
                } else {
                    alert("City not found. Showing default map.");
                }
            })
            .catch((err) => console.error("Error fetching city data:", err));
    }, [city]);

    const fetchMapData = useCallback(async (bounds) => {
        const params = new URLSearchParams({
            long_1: bounds.leftLng,
            lat_1: bounds.bottomLat,
            long_2: bounds.rightLng,
            lat_2: bounds.topLat,
            count: 150,
        });

        try {
            const response = await fetch(
                `http://localhost:8000/api/v1/issues/bounds?${params.toString()}`,
            );

            if (!response.ok)
                throw new Error(`HTTP error! status: ${response.status}`);

            const rawBackendData = await response.json();

            const formattedPoints = rawBackendData.map((issue) => ({
                id: issue.id,
                type: issue.classification,
                position: [issue.latitude, issue.longitude],
                summary: issue.description || issue.address,
            }));

            setReportData(formattedPoints);
        } catch (error) {
            console.error("Error fetching map data:", error);
        }
    }, []);

    const handleGenerateReport = async () => {
        if (reportData.length === 0) {
            alert(
                "There are no issues currently visible on the map to generate a report for!",
            );
            return;
        }

        setIsGenerating(true);

        try {
            const visibleIncidentIds = reportData.map((point) => point.id);

            const response = await fetch(
                "http://localhost:8000/api/v1/workflow/infrastructure-report/bulk",
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        incident_ids: visibleIncidentIds,
                        fiscal_year: new Date().getFullYear(),
                    }),
                },
            );

            if (!response.ok) throw new Error("Failed to start bulk workflow");

            const data = await response.json();

            navigate("/loading", {
                state: { reportId: data.report_id || data.id },
            });
        } catch (error) {
            console.error("Error starting bulk report:", error);
            alert(
                "Could not start the report generation. Check if the backend is running!",
            );
        } finally {
            setIsGenerating(false);
        }
    };

    const handleGenerateSingleReport = async (point) => {
        setIsGenerating(true);

        try {
            const response = await fetch(
                "http://localhost:8000/api/v1/workflow/infrastructure-report",
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        location: city,
                        issue_type: point.type || "General Infrastructure",
                        fiscal_year: new Date().getFullYear(),
                        issues: [point],
                    }),
                },
            );

            if (!response.ok)
                throw new Error("Failed to start single workflow");

            const data = await response.json();

            navigate("/loading", {
                state: { reportId: data.report_id || data.id },
            });
        } catch (error) {
            console.error("Error starting single report:", error);
            alert(
                "Could not start the report generation. Check if the backend is running!",
            );
        } finally {
            setIsGenerating(false);
        }
    };

    return (
        <div
            style={{
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                minHeight: "80vh",
                padding: "20px",
            }}
        >
            <div
                style={{
                    backgroundColor: "white",
                    padding: "30px",
                    borderRadius: "12px",
                    boxShadow: "0 4px 15px rgba(0,0,0,0.1)",
                    textAlign: "center",
                    width: "100%",
                    maxWidth: "700px",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                }}
            >
                <h2
                    style={{
                        marginTop: 0,
                        marginBottom: "20px",
                        color: "#2c3e50",
                    }}
                >
                    Map of {city}
                </h2>

                <div
                    style={{
                        height: "450px",
                        width: "100%",
                        marginBottom: "25px",
                        borderRadius: "8px",
                        overflow: "hidden",
                        boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
                    }}
                >
                    <div
                        style={{
                            height: "450px",
                            width: "100%",
                            marginBottom: "25px",
                            borderRadius: "8px",
                            overflow: "hidden",
                            boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
                        }}
                    >
                        {!coords ? (
                            <div
                                style={{
                                    display: "flex",
                                    justifyContent: "center",
                                    alignItems: "center",
                                    height: "100%",
                                    backgroundColor: "#f8f9fa",
                                }}
                            >
                                <p
                                    style={{
                                        fontSize: "18px",
                                        color: "#7f8c8d",
                                        fontWeight: "bold",
                                    }}
                                >
                                    Locating {city}...
                                </p>
                            </div>
                        ) : (
                            <MapContainer
                                center={coords}
                                zoom={13}
                                style={{ height: "100%", width: "100%" }}
                            >
                                <ChangeMapView center={coords} />
                                <TileLayer
                                    url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
                                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
                                />

                                <MapBoundsTracker
                                    onBoundsChange={fetchMapData}
                                />

                                {reportData.map((point) => (
                                    <MapPoint
                                        key={point.id}
                                        point={point}
                                        onGenerate={handleGenerateSingleReport}
                                    />
                                ))}
                            </MapContainer>
                        )}
                    </div>
                </div>

                <button
                    onClick={handleGenerateReport}
                    disabled={isGenerating}
                    className="btn-hover"
                    style={{
                        padding: "12px 25px",
                        fontSize: "16px",
                        fontWeight: "bold",
                        backgroundColor: isGenerating ? "#bdc3c7" : "#b084cc",
                        color: "white",
                        border: "none",
                        borderRadius: "8px",
                        cursor: isGenerating ? "wait" : "pointer",
                        width: "250px",
                        boxShadow: isGenerating
                            ? "none"
                            : "0 4px 6px rgba(176, 132, 204, 0.4)",
                    }}
                >
                    {isGenerating ? "Starting Job..." : "Generate Report"}
                </button>
            </div>
        </div>
    );
};

export default CityMap;
