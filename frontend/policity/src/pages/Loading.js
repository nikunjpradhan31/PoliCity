import React, { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";

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
                // 1. POLL THE STATUS ENDPOINT
                const statusRes = await fetch(
                    `http://localhost:8000/api/v1/workflow/infrastructure-report/${reportId}`,
                );

                if (statusRes.ok) {
                    const statusData = await statusRes.json();
                    const currentStatus = (
                        statusData.status || ""
                    ).toLowerCase();

                    // 2. IF IT IS FINISHED...
                    if (
                        currentStatus === "complete" ||
                        currentStatus === "completed" ||
                        currentStatus === "done"
                    ) {
                        clearInterval(intervalId); // Stop polling immediately!
                        setStatusText("Finalizing report... fetching details.");

                        // 3. FETCH THE ACTUAL FINAL REPORT DATA
                        try {
                            const incidentId = statusData.incident_id;

                            if (!incidentId) {
                                throw new Error(
                                    "Backend finished, but no incident_id was provided.",
                                );
                            }

                            const finalReportRes = await fetch(
                                `http://localhost:8000/api/v1/workflow/infrastructure-report/incident/${incidentId}`,
                            );

                            if (!finalReportRes.ok) {
                                throw new Error(
                                    `HTTP error! status: ${finalReportRes.status}`,
                                );
                            }

                            const finalReportData = await finalReportRes.json();

                            // 4. HAND THE FINAL DATA OFF TO THE DOWNLOAD PAGE
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
            <div
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
                <h2 style={{ color: "#2c3e50", marginTop: 0 }}>
                    Generating your PoliCity report...
                </h2>
                <p
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
