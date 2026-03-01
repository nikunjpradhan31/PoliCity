import React, { useEffect, useCallback } from "react";
import { useLocation, useNavigate } from "react-router-dom";

const Download = () => {
    const location = useLocation();
    const navigate = useNavigate();
    
    const finalReportData = location.state?.report;

    const handleDownload = useCallback(() => {
        if (!finalReportData) return;

        const fileData = JSON.stringify(finalReportData, null, 2);
        
        const blob = new Blob([fileData], { type: "application/json" });
        const url = URL.createObjectURL(blob);

        const link = document.createElement("a");
        link.href = url;
        link.download = "PoliCity_Infrastructure_Report.json"; 
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }, [finalReportData]); 

    useEffect(() => {
        if (finalReportData) {
            handleDownload();
        }
    }, [finalReportData, handleDownload]);
    
    if (!finalReportData) {
        return (
            <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "80vh" }}>
                <button onClick={() => navigate("/")} style={{ padding: "12px 25px", fontSize: "16px", fontWeight: "bold", backgroundColor: "#3498db", color: "white", border: "none", borderRadius: "8px", cursor: "pointer" }}>
                    Return to Map
                </button>
            </div>
        );
    }

    return (
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "80vh", padding: "20px" }}>
            <div style={{ backgroundColor: "white", padding: "40px", borderRadius: "12px", boxShadow: "0 4px 15px rgba(0,0,0,0.1)", textAlign: "center", width: "100%", maxWidth: "500px" }}>
                <h2 style={{ color: "#2c3e50", marginTop: 0 }}>Report Generated Successfully!</h2>
                
                <p style={{ color: "#7f8c8d", marginBottom: "15px", fontSize: "16px" }}>
                    Your download should have started automatically.
                </p>
                <p style={{ color: "#95a5a6", marginBottom: "30px", fontSize: "14px" }}>
                    If it didn't, or if you need to download it again, click the button below:
                </p>
                
                <button
                    onClick={handleDownload}
                    style={{
                        padding: "12px 25px",
                        fontSize: "16px",
                        fontWeight: "bold",
                        backgroundColor: "#b084cc",
                        color: "white",
                        border: "none",
                        borderRadius: "8px",
                        cursor: "pointer",
                        width: "100%",
                        boxShadow: "0 4px 6px rgba(176, 132, 204, 0.3)",
                    }}
                >
                    Download Report Again
                </button>
            </div>
        </div>
    );
};

export default Download;