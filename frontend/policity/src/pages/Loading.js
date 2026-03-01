import React, { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import "../animations.css";

const Loading = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const reportId = location.state?.reportId;

    const [statusText, setStatusText] = useState("Initializing workflow...");
    const [progress, setProgress] = useState(0);
    const [completedAgents, setCompletedAgents] = useState([]);
    const [currentAgent, setCurrentAgent] = useState(null);
    const [isComplete, setIsComplete] = useState(false);

    useEffect(() => {
        if (!reportId) {
            setStatusText(
                "Error: No Report ID found. Please go back to the map.",
            );
            return;
        }

        const intervalId = setInterval(async () => {
            try {
                const res = await fetch(
                    `http://localhost:8000/api/v1/workflow/infrastructure-report/${reportId}`,
                );
                if (res.ok) {
                    const data = await res.json();
                    const currentStatus = (data.status || "").toLowerCase();

                    setProgress(data.progress || 0);
                    setCompletedAgents(data.agents_completed || []);
                    setCurrentAgent(data.current_agent || null);

                    if (currentStatus === "complete") {
                        clearInterval(intervalId);
                        setIsComplete(true);

                        const finalId =
                            data.incident_id && data.incident_id !== "MULTIPLE"
                                ? data.incident_id
                                : reportId;

                        // Pass the direct API URL to the next page
                        const pdfUrl = `http://localhost:8000/api/v1/workflow/infrastructure-report/incident/${finalId}/pdf`;
                        navigate("/pdf", { state: { pdfUrl: pdfUrl } });
                    } else if (
                        currentStatus === "failed" ||
                        currentStatus === "error"
                    ) {
                        clearInterval(intervalId);
                        setStatusText(
                            `Report generation failed: ${data.error || "Unknown error"}`,
                        );
                    } else {
                        setStatusText(
                            "AI Agents are analyzing the infrastructure data...",
                        );
                    }
                }
            } catch (err) {
                console.error("Polling error:", err);
            }
        }, 3000);

        return () => clearInterval(intervalId);
    }, [navigate, reportId]);

    // Helper to determine the status of each agent step
    const getStepStatus = (agentName) => {
        if (
            completedAgents.includes(agentName) ||
            completedAgents.includes(`multi_${agentName}`)
        ) {
            return "done";
        }
        if (
            currentAgent === agentName ||
            currentAgent === `multi_${agentName}`
        ) {
            return "active";
        }
        return "pending";
    };

    // Sub-component for checklist items
    const StepItem = ({ label, status }) => {
        const isDone = status === "done";
        const isActive = status === "active";

        const color = isDone ? "#27ae60" : isActive ? "#b084cc" : "#bdc3c7";

        return (
            <div
                style={{
                    display: "flex",
                    alignItems: "center",
                    margin: "18px 0",
                    color: color,
                    fontWeight: isActive ? "bold" : "normal",
                }}
            >
                <span
                    style={{
                        marginRight: "15px",
                        fontSize: "22px",
                        display: "inline-block",
                        animation: isActive
                            ? "spin 2s linear infinite"
                            : "none",
                    }}
                >
                    {isDone ? "✅" : isActive ? "🔄" : "⏳"}
                </span>
                <span className={isActive ? "pulse-text" : ""}>{label}</span>
            </div>
        );
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
                className="slide-up-card"
                style={{
                    backgroundColor: "white",
                    padding: "40px",
                    borderRadius: "12px",
                    boxShadow: "0 4px 15px rgba(0,0,0,0.1)",
                    width: "100%",
                    maxWidth: "500px",
                    textAlign: "center",
                }}
            >
                <h2 style={{ color: "#2c3e50", marginTop: 0 }}>
                    Building Your Report
                </h2>

                {/* Status text display area */}
                <p
                    style={{
                        color: "#7f8c8d",
                        fontSize: "16px",
                        minHeight: "24px",
                        marginBottom: "20px",
                    }}
                >
                    {statusText}
                </p>

                {/* Progress Bar */}
                <div
                    style={{
                        width: "100%",
                        backgroundColor: "#ecf0f1",
                        height: "8px",
                        borderRadius: "8px",
                        overflow: "hidden",
                        marginBottom: "30px",
                    }}
                >
                    <div
                        style={{
                            height: "100%",
                            backgroundColor: "#b084cc",
                            width: `${progress}%`,
                            transition: "width 0.8s ease-out",
                        }}
                    ></div>
                </div>

                {/* Agent Checklist */}
                <div
                    style={{
                        textAlign: "left",
                        borderTop: "1px solid #eee",
                        paddingTop: "20px",
                    }}
                >
                    <StepItem
                        label="Data Compilation & Verification"
                        status={progress > 0 ? "done" : "active"}
                    />
                    <StepItem
                        label="Geospatial & Financial Analysis"
                        status={getStepStatus("thinking")}
                    />
                    <StepItem
                        label="Drafting Narrative & Recommendations"
                        status={getStepStatus("report")}
                    />
                    <StepItem
                        label="Finalizing Document File"
                        status={
                            isComplete
                                ? "done"
                                : progress >= 90
                                  ? "active"
                                  : "pending"
                        }
                    />
                </div>
            </div>
        </div>
    );
};

export default Loading;
