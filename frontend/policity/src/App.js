import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

// Import components and pages
import Header from "./components/Header.js";
import Home from "./pages/Home";
import CityMap from "./pages/CityMap";
import Loading from "./pages/Loading";
import Download from "./pages/Download";

export default function App() {
    return (
        <Router>
            <div
                style={{
                    fontFamily: "sans-serif",
                    minHeight: "100vh",
                    backgroundColor: "#F0F7EE",
                }}
            >
                <Header />
                <Routes>
                    <Route path="/" element={<Home />} />
                    <Route path="/map" element={<CityMap />} />
                    <Route path="/loading" element={<Loading />} />
                    <Route path="/download" element={<Download />} />
                </Routes>
            </div>
        </Router>
    );
}
