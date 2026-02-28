import React, { useState, useEffect, useCallback } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
    MapContainer,
    TileLayer,
    useMap,
    useMapEvents,
    CircleMarker,
    Popup,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";

const MapPoint = ({ position, summary, type }) => {
    const GOOGLE_API_KEY = process.env.REACT_APP_GOOGLE_MAPS_API_KEY;
    const [lat, lng] = position;
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
            center={position}
            radius={8}
            pathOptions={{
                color: getColor(type),
                fillColor: getColor(type),
                fillOpacity: 0.7,
                weight: 2,
            }}
        >
            <Popup autoPan={true} minWidth={340} maxWidth={400} minHeight={200} maxHeight={400}>
                <div
                    style={{
                        textAlign: "center",
                        fontFamily: "sans-serif",
                        padding: "5px",
                    }}
                >
                    <strong style={{ color: getColor(type), fontSize: "16px" }}>
                        {type ? type.toUpperCase() : "UNKNOWN"}
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
                        {summary || "No description provided."}
                    </p>
                    <div
                        style={{
                            borderRadius: "8px",
                            overflow: "hidden",
                            border: "1px solid #ccc",
                        }}
                    >
                        <iframe
                            width="400"
                            height="220"
                            style={{ border: 0, display: "block" }}
                            loading="lazy"
                            allowFullScreen
                            src={streetViewUrl}
                            title={`Street view of ${type}`}
                        ></iframe>
                    </div>
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

    // Wrap the map movement in a useEffect so it doesn't cause an infinite loop!
    useEffect(() => {
        if (center) {
            // Pro-tip: flyTo adds a really smooth panning animation instead of a hard jump
            map.flyTo(center, 13);
        }
    }, [center, map]); // Only re-run this if 'center' coordinates change

    return null;
};

const CityMap = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const city = location.state?.city || "London";

    const [coords, setCoords] = useState(null);
    const [reportData, setReportData] = useState([]);

    // Fetch coordinates for the searched city
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

    // Fetch data from FastAPI when map moves
    const fetchMapData = useCallback(async (bounds) => {
        const params = new URLSearchParams({
            long_1: bounds.leftLng,
            lat_1: bounds.bottomLat,
            long_2: bounds.rightLng,
            lat_2: bounds.topLat,
            count: 150, 
        });

        try {
            // NOTE: Ensure your FastAPI server is running on port 8000!
            const response = await fetch(
                `http://localhost:8000/api/v1/issues/bounds?${params.toString()}`,
            );

            if (!response.ok)
                throw new Error(`HTTP error! status: ${response.status}`);

            const rawBackendData = await response.json();

            // Map the Python variables to the React component variables
            const formattedPoints = rawBackendData.map((issue) => ({
                id: issue.id,
                type: issue.classification,
                position: [issue.latitude, issue.longitude], // Leaflet needs this as an array
                summary: issue.description || issue.address, // Fallback to address if no description
            }));

            setReportData(formattedPoints);
        } catch (error) {
            console.error("Error fetching map data:", error);
        }
    }, []);

    // Handle Generate Report Button
    const handleGenerateReport = () => {
        if (reportData.length === 0) {
            alert(
                "There are no issues currently visible on the map to generate a report for!",
            );
            return;
        }
        const payload = {
            city,
            totalIssues: reportData.length,
            issues: reportData,
        };
        navigate("/loading", { state: payload });
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
                        {/* If coords are null, show a loading message. If they exist, draw the map! */}
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
                                <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

                                <MapBoundsTracker
                                    onBoundsChange={fetchMapData}
                                />

                                {reportData.map((point) => (
                                    <MapPoint
                                        key={point.id}
                                        position={point.position}
                                        summary={point.summary}
                                        type={point.type}
                                    />
                                ))}
                            </MapContainer>
                        )}
                    </div>
                </div>

                <button
                    onClick={handleGenerateReport}
                    style={{
                        padding: "12px 25px",
                        fontSize: "16px",
                        fontWeight: "bold",
                        backgroundColor: "#b084cc",
                        color: "white",
                        border: "none",
                        borderRadius: "8px",
                        cursor: "pointer",
                        width: "250px",
                        boxShadow: "0 4px 6px #b084cc",
                    }}
                >
                    Generate Report
                </button>
            </div>
        </div>
    );
};

export default CityMap;
