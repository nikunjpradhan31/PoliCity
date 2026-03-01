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

        // Poll the GET endpoint every 3 seconds
        const intervalId = setInterval(async () => {
            try {
                const statusRes = await fetch(
                    `http://localhost:8000/api/v1/workflow/infrastructure-report/${reportId}`,
                );

                if (statusRes.ok) {
                    const statusData = await statusRes.json();

                    // If the backend says the report is ready:
                    if (
                        statusData.status === "completed" ||
                        statusData.status === "done"
                    ) {
                        clearInterval(intervalId);
                        // Send them to Download, passing the final data!
                        navigate("/download", {
                            state: { report: statusData },
                        });
                    }
                    // If the backend says the workflow crashed:
                    else if (statusData.status === "failed") {
                        clearInterval(intervalId);
                        setStatusText(
                            "Report generation failed on the server. Please try again.",
                        );
                    }
                    // Otherwise, just keep waiting!
                    else {
                        setStatusText(
                            statusData.message ||
                                "Still analyzing... please wait.",
                        );
                    }
                }
            } catch (error) {
                console.error("Polling error:", error);
            }
        }, 3000);

        return () => clearInterval(intervalId); // Cleanup if user leaves page
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
