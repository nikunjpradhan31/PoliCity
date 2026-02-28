import React, { useEffect } from "react";

const Download = () => {
    const handleDownload = () => {
        const fileData =
            "This is your simulated PoliCity Report Data.\nEverything looks great!";
        const blob = new Blob([fileData], { type: "text/plain" });
        const url = URL.createObjectURL(blob);

        const link = document.createElement("a");
        link.href = url;
        link.download = "PoliCity_Report.txt";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    useEffect(() => {
        handleDownload();
    }, []);

    return (
        <div style={{ padding: "50px", textAlign: "center" }}>
            <h2>Report Generated Successfully!</h2>
            <p>Your download should have started automatically.</p>
            <p>
                If it didn't, or if you need to download it again, click the
                button below:
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
                    width: "250px",
                    boxShadow: "0 4px 6px #b084cc",
                }}
            >
                Download Report
            </button>
        </div>
    );
};

export default Download;
