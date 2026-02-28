import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";

const Loading = () => {
    const navigate = useNavigate();

    useEffect(() => {
        // Simulate a backend API call taking 3 seconds
        const timer = setTimeout(() => {
            navigate("/download");
        }, 3000);

        return () => clearTimeout(timer);
    }, [navigate]);

    return (
        <div style={{ padding: "50px", textAlign: "center" }}>
            <h2>Generating your PoliCity report...</h2>
            <p>Please wait while we gather the data from our servers.</p>
        </div>
    );
};

export default Loading;
