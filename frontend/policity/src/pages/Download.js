import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import "../animations.css"; 

const Download = () => {
    const location = useLocation();
    const navigate = useNavigate();
    
    const finalReportData = location.state?.report;
    
    const reportUrlPath = finalReportData?.result?.report_url || finalReportData?.report_url;

    const [pdfUrl, setPdfUrl] = useState(null);
    const [isLoadingPdf, setIsLoadingPdf] = useState(true);

    useEffect(() => {
        if (!reportUrlPath) {
            setIsLoadingPdf(false);
            return;
        }

        const fetchPdf = async () => {
            try {
                const fullUrl = reportUrlPath.startsWith("http") 
                    ? reportUrlPath 
                    : `http://localhost:8000${reportUrlPath}`;

                const response = await fetch(fullUrl);
                if (!response.ok) throw new Error("Failed to fetch PDF document");

                const blob = await response.blob();
                
                const objectUrl = URL.createObjectURL(blob);
                setPdfUrl(objectUrl);

            } catch (error) {
                console.error("Error loading PDF:", error);
            } finally {
                setIsLoadingPdf(false);
            }
        };

        fetchPdf();

        return () => {
            if (pdfUrl) URL.revokeObjectURL(pdfUrl);
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [reportUrlPath]);

    const handleDownload = () => {
        if (!pdfUrl) return;
        
        const link = document.createElement("a");
        link.href = pdfUrl;
        link.download = `PoliCity_Infrastructure_Report.pdf`; 
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    if (!finalReportData) {
        return (
            <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "80vh" }}>
                <button onClick={() => navigate("/")} className="btn-hover" style={{ padding: "12px 25px", fontSize: "16px", fontWeight: "bold", backgroundColor: "#3498db", color: "white", border: "none", borderRadius: "8px", cursor: "pointer" }}>
                    Return to Map
                </button>
            </div>
        );
    }

    return (
        <div className="slide-up-card" style={{ display: "flex", flexDirection: "column", alignItems: "center", minHeight: "80vh", padding: "30px 20px" }}>
            
            <div style={{ width: "100%", maxWidth: "850px", display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px", backgroundColor: "white", padding: "20px 30px", borderRadius: "12px", boxShadow: "0 4px 15px rgba(0,0,0,0.05)" }}>
                <div>
                    <h2 style={{ color: "#2c3e50", margin: "0 0 5px 0" }}>Report Generated</h2>
                    <p style={{ color: "#7f8c8d", margin: 0, fontSize: "14px" }}>Review the AI analysis below</p>
                </div>
                
                <div style={{ display: "flex", gap: "15px" }}>
                    <button 
                        onClick={() => navigate("/")}
                        className="btn-hover"
                        style={{ padding: "10px 20px", fontSize: "14px", fontWeight: "bold", backgroundColor: "#ecf0f1", color: "#2c3e50", border: "none", borderRadius: "8px", cursor: "pointer" }}
                    >
                        Back to Map
                    </button>
                    <button
                        onClick={handleDownload}
                        disabled={!pdfUrl}
                        className="btn-hover"
                        style={{ padding: "10px 20px", fontSize: "14px", fontWeight: "bold", backgroundColor: pdfUrl ? "#b084cc" : "#bdc3c7", color: "white", border: "none", borderRadius: "8px", cursor: pdfUrl ? "pointer" : "not-allowed", boxShadow: pdfUrl ? "0 4px 6px rgba(176, 132, 204, 0.3)" : "none" }}
                    >
                        Download PDF
                    </button>
                </div>
            </div>

            <div style={{ width: "100%", maxWidth: "850px", height: "75vh", backgroundColor: "#e0e0e0", borderRadius: "8px", overflow: "hidden", display: "flex", justifyContent: "center", alignItems: "center", boxShadow: "0 10px 25px rgba(0,0,0,0.15)" }}>
                {isLoadingPdf ? (
                    <div style={{ textAlign: "center" }}>
                        <div className="spinner"></div>
                        <p className="pulse-text" style={{ color: "#7f8c8d", fontWeight: "500" }}>Loading document viewer...</p>
                    </div>
                ) : pdfUrl ? (
                    <iframe 
                        src={`${pdfUrl}#toolbar=0&navpanes=0&scrollbar=1`}
                        title="PoliCity Report"
                        style={{ width: "100%", height: "100%", border: "none", backgroundColor: "white" }}
                    />
                ) : (
                    <div style={{ textAlign: "center", color: "#e74c3c", padding: "20px" }}>
                        <h3>Failed to load PDF</h3>
                        <p>We couldn't locate the document. It may have failed to generate.</p>
                    </div>
                )}
            </div>

        </div>
    );
};

export default Download;