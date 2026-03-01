import React from "react";
import { Link } from "react-router-dom";
import logo from "../assets/logo.svg";

const Header = () => {
    return (
        <header
            style={{
                padding: "15px 20px",
                backgroundColor: "#453F78",
                color: "white",
            }}
        >
            <Link
                to="/"
                style={{
                    display: "inline-flex",
                    alignItems: "center",
                    textDecoration: "none",
                    cursor: "pointer",
                }}
            >
                <img
                    src={logo}
                    alt="PoliCity Logo"
                    style={{
                        height: "70px",
                        width: "auto",
                        display: "block",
                    }}
                />
            </Link>
        </header>
    );
};

export default Header;
