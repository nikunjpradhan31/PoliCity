import React, { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import "../animations.css";

const Loading = () => {
    const navigate = useNavigate();
    const location = useLocation();

    // Grab the ID handed to us by the Map page!
    const reportId = location.state?.reportId;

    const [statusText, setStatusText] = useState(
        "Analyzing infrastructure data...",
    );

    useEffect(() => {
        if (!reportId) {
            setStatusText(
                "Error: No Report ID found. Please go back to the map.",
            );
            return;
        }

        const intervalId = setInterval(async () => {
            try {
                const statusRes = await fetch(
                    `http://localhost:8000/api/v1/workflow/infrastructure-report/${reportId}`,
                );

                if (statusRes.ok) {
                    const statusData = await statusRes.json();
                    const currentStatus = (
                        statusData.status || ""
                    ).toLowerCase();

                    if (
                        currentStatus === "complete" ||
                        currentStatus === "completed" ||
                        currentStatus === "done"
                    ) {
                        clearInterval(intervalId); // Stop polling immediately!
                        setStatusText("Finalizing report... fetching details.");

                        try {
                            // Check if the backend gave us a real incident ID, otherwise fallback to the reportId!
                            const finalIdToFetch =
                                statusData.incident_id &&
                                statusData.incident_id !== "MULTIPLE"
                                    ? statusData.incident_id
                                    : reportId;

                            if (!finalIdToFetch) {
                                throw new Error(
                                    "Backend finished, but no valid ID was provided to fetch the final data.",
                                );
                            }

                            // Fetch the final data using our safely calculated ID
                            const finalReportRes = await fetch(
                                `http://localhost:8000/api/v1/workflow/infrastructure-report/incident/${finalIdToFetch}`,
                            );

                            if (!finalReportRes.ok) {
                                throw new Error(
                                    `HTTP error! status: ${finalReportRes.status}`,
                                );
                            }

                            const finalReportData = await finalReportRes.json();

                            navigate("/download", {
                                state: { report: finalReportData },
                            });
                        } catch (fetchError) {
                            console.error(
                                "Failed to fetch final incident details:",
                                fetchError,
                            );
                            setStatusText(
                                "Report finished, but failed to retrieve final data.",
                            );
                        }
                    } else if (
                        currentStatus === "failed" ||
                        currentStatus === "error"
                    ) {
                        clearInterval(intervalId);
                        setStatusText(
                            `Report generation failed: ${statusData.error || "Unknown error on server."}`,
                        );
                    } else {
                        setStatusText(
                            `Analyzing... ${currentStatus} (${statusData.progress || 0}%)`,
                        );
                    }
                }
            } catch (error) {
                console.error("Polling error:", error);
            }
        }, 3000);

        return () => clearInterval(intervalId);
    }, [navigate, reportId]);

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
            {/* Added slide-up-card class */}
            <div
                className="slide-up-card"
                style={{
                    backgroundColor: "white",
                    padding: "50px",
                    borderRadius: "12px",
                    boxShadow: "0 4px 15px rgba(0,0,0,0.1)",
                    textAlign: "center",
                    width: "100%",
                    maxWidth: "500px",
                }}
            >
                <div className="spinner"></div>

                <h2 style={{ color: "#2c3e50", marginTop: 0 }}>
                    Generating your PoliCity report...
                </h2>

                <p
                    className="pulse-text"
                    style={{
                        fontSize: "18px",
                        color: "#7f8c8d",
                        marginTop: "20px",
                        fontWeight: "500",
                    }}
                >
                    {statusText}
                </p>
            </div>
        </div>
    );
};

export default Loading;
