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
            setStatusText("Error: No Report ID found. Please go back to the map.");
            return;
        }

        const intervalId = setInterval(async () => {
            try {
                const statusRes = await fetch(`http://localhost:8000/api/v1/workflow/infrastructure-report/${reportId}`);

                if (statusRes.ok) {
                    const statusData = await statusRes.json();
                    const currentStatus = (statusData.status || "").toLowerCase();

                    setProgress(statusData.progress || 0);
                    setCompletedAgents(statusData.agents_completed || []);
                    setCurrentAgent(statusData.current_agent || null);

                    if (currentStatus === "complete" || currentStatus === "completed" || currentStatus === "done") {
                        clearInterval(intervalId);
                        setIsComplete(true);
                        setStatusText("Finalizing report... fetching details.");

                        try {
                            const finalIdToFetch = (statusData.incident_id && statusData.incident_id !== "MULTIPLE")
                                ? statusData.incident_id
                                : reportId;

                            const finalReportRes = await fetch(`http://localhost:8000/api/v1/workflow/infrastructure-report/incident/${finalIdToFetch}`);
                            if (!finalReportRes.ok) throw new Error(`HTTP error! status: ${finalReportRes.status}`);

                            const finalReportData = await finalReportRes.json();
                            navigate("/download", { state: { report: finalReportData } });
                        } catch (fetchError) {
                            console.error("Failed to fetch final details:", fetchError);
                            setStatusText("Report finished, but failed to retrieve final data.");
                        }
                    }
                    else if (currentStatus === "failed" || currentStatus === "error") {
                        clearInterval(intervalId);
                        setStatusText(`Report generation failed: ${statusData.error || "Unknown server error."}`);
                    }
                    else {
                        setStatusText(`AI Agents are analyzing the infrastructure data...`);
                    }
                }
            } catch (error) {
                console.error("Polling error:", error);
            }
        }, 3000);

        return () => clearInterval(intervalId);
    }, [navigate, reportId]);

    const getStepStatus = (baseAgentName) => {
        const isComplete = completedAgents.includes(baseAgentName) || completedAgents.includes(`multi_${baseAgentName}`);
        const isActive = currentAgent === baseAgentName || currentAgent === `multi_${baseAgentName}`;

        if (isComplete || isComplete) return "done";
        if (isActive) return "active";
        return "pending";
    };

    const StepItem = ({ label, status }) => {
        let icon, color, textClass;

        if (status === "done") {
            icon = "✅";
            color = "#27ae60";
            textClass = "";
        } else if (status === "active") {
            icon = "🔄";
            color = "#b084cc"; 
            textClass = "pulse-text"; 
        } else {
            icon = "⏳";
            color = "#bdc3c7";
            textClass = "";
        }

        return (
            <div style={{ display: "flex", alignItems: "center", margin: "18px 0", fontSize: "18px", color: color, fontWeight: status === "active" ? "bold" : "normal", transition: "all 0.3s ease" }}>
                <span style={{ marginRight: "15px", fontSize: "22px", display: "inline-block", animation: status === "active" ? "spin 2s linear infinite" : "none" }}>
                    {icon}
                </span>
                <span className={textClass}>{label}</span>
            </div>
        );
    };

    return (
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "80vh", padding: "20px" }}>
            <div className="slide-up-card" style={{ backgroundColor: "white", padding: "40px", borderRadius: "12px", boxShadow: "0 4px 15px rgba(0,0,0,0.1)", width: "100%", maxWidth: "500px" }}>
                
                <div style={{ textAlign: "center", marginBottom: "30px" }}>
                    <h2 style={{ color: "#2c3e50", marginTop: 0 }}>Building Your Report</h2>
                    <p style={{ color: "#7f8c8d", fontSize: "16px", minHeight: "24px" }}>{statusText}</p>

                    <div style={{ width: "100%", backgroundColor: "#ecf0f1", borderRadius: "8px", height: "8px", marginTop: "20px", overflow: "hidden" }}>
                        <div style={{ height: "100%", backgroundColor: "#b084cc", width: `${progress}%`, transition: "width 0.8s ease-out" }}></div>
                    </div>
                </div>

                <div style={{ borderTop: "1px solid #eee", paddingTop: "20px", paddingLeft: "10px" }}>
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
                        status={isComplete ? "done" : (progress >= 90 ? "active" : "pending")} 
                    />
                </div>

            </div>
        </div>
    );
};

export default Loading;