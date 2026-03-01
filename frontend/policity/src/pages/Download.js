import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import "../animations.css";

const Download = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const pdfUrl = location.state?.pdfUrl;

    const [blobUrl, setBlobUrl] = useState(null);

    useEffect(() => {
    if (!pdfUrl) return;

    let objectUrl;

    const loadPdf = async () => {
        try {
            const response = await fetch(pdfUrl);
            if (!response.ok) throw new Error("PDF Fetch Failed");
            const blob = await response.blob();
            objectUrl = URL.createObjectURL(blob);
            setBlobUrl(objectUrl);
        } catch (err) {
            console.error("Error loading PDF:", err);
        }
    };

    loadPdf();

    return () => {
        if (objectUrl) {
            URL.revokeObjectURL(objectUrl);
        }
    };
}, [pdfUrl]);

    return (
        <div
            className="slide-up-card"
            style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                height: "90vh",
                padding: "20px",
            }}
        >
            <div
                style={{
                    width: "100%",
                    maxWidth: "900px",
                    display: "flex",
                    justifyContent: "space-between",
                    marginBottom: "15px",
                }}
            >
                <button
                    onClick={() => navigate("/")}
                    className="btn-hover"
                    style={{
                        padding: "10px 20px",
                        borderRadius: "8px",
                        border: "none",
                    }}
                >
                    Back to Map
                </button>
                <a
                    href={blobUrl}
                    download="PoliCity_Report.pdf"
                    style={{ textDecoration: "none" }}
                >
                    <button
                        className="btn-hover"
                        style={{
                            padding: "10px 20px",
                            borderRadius: "8px",
                            border: "none",
                            backgroundColor: "#b084cc",
                            color: "white",
                        }}
                    >
                        Download PDF
                    </button>
                </a>
            </div>
            <div
                style={{
                    width: "100%",
                    maxWidth: "900px",
                    flex: 1,
                    backgroundColor: "#525659",
                    borderRadius: "8px",
                    overflow: "hidden",
                    boxShadow: "0 10px 30px rgba(0,0,0,0.2)",
                }}
            >
                {blobUrl ? (
                    <iframe
                        src={`${blobUrl}#toolbar=0`}
                        style={{
                            width: "100%",
                            height: "100%",
                            border: "none",
                        }}
                        title="PDF"
                    />
                ) : (
                    <div
                        style={{
                            display: "flex",
                            justifyContent: "center",
                            alignItems: "center",
                            height: "100%",
                            color: "white",
                        }}
                    >
                        <div className="spinner"></div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Download;
