import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

const Home = () => {
    const [city, setCity] = useState("");
    const navigate = useNavigate();

    const handleSubmit = (e) => {
        e.preventDefault();

        if (city.trim() !== "") {
            const formattedCity = city
                .trim()
                .split(/\s+/) // Splits the string by one or more spaces
                .map(
                    (word) =>
                        word.charAt(0).toUpperCase() +
                        word.toLowerCase().slice(1),
                )
                .join(" "); // Joins the words back together with a single space

            navigate("/map", { state: { city: formattedCity } });
        }
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
                style={{
                    backgroundColor: "white",
                    padding: "40px",
                    borderRadius: "12px",
                    boxShadow: "0 4px 15px rgba(0,0,0,0.1)",
                    textAlign: "center",
                }}
            >
                <h2
                    style={{
                        marginTop: 0,
                        marginBottom: "20px",
                        color: "#2c3e50",
                    }}
                >
                    Enter a City
                </h2>

                <form
                    onSubmit={handleSubmit}
                    style={{
                        display: "flex",
                        flexDirection: "column",
                        gap: "15px",
                        alignItems: "center",
                    }}
                >
                    <input
                        type="text"
                        value={city}
                        onChange={(e) => setCity(e.target.value)}
                        placeholder="e.g., Chicago, Seattle, Dallas"
                        style={{
                            padding: "12px 15px",
                            fontSize: "16px",
                            borderRadius: "8px",
                            border: "1px solid #ddd",
                            outline: "none",
                            width: "450px",
                            boxSizing: "border-box",
                        }}
                    />
                    <button
                        type="submit"
                        style={{
                            padding: "12px 15px",
                            fontSize: "16px",
                            fontWeight: "bold",
                            backgroundColor: "#b084cc",
                            color: "white",
                            border: "none",
                            borderRadius: "8px",
                            cursor: "pointer",
                            width: "450px",
                            boxSizing: "border-box",
                            boxShadow: "0 4px 6px #b084cc",
                        }}
                    >
                        Submit
                    </button>
                </form>
            </div>
        </div>
    );
};

export default Home;
