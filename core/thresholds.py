PARAM_THRESHOLDS = {
    "WS2M": [  # gió (m/s)
        {
            "label": "Light breeze",
            "y0": 0.0,
            "y1": 5.4,
            "color": "rgba(173,216,230,0.3)",
        },
        {
            "label": "Moderate breeze",
            "y0": 5.5,
            "y1": 10.7,
            "color": "rgba(144,238,144,0.3)",
        },
        {
            "label": "Strong breeze",
            "y0": 10.8,
            "y1": 17.1,
            "color": "rgba(255,165,0,0.3)",
        },
        {"label": "Gale", "y0": 17.2, "y1": 1000000000, "color": "rgba(255,0,0,0.3)"},
    ],
    "T2M": [  # nhiệt độ (°C)
        {"label": "Very Cold", "y0": -50, "y1": 0, "color": "rgba(135,206,250,0.3)"},
        {"label": "Cold", "y0": 0, "y1": 15, "color": "rgba(135,206,250,0.3)"},
        {"label": "Cool", "y0": 15, "y1": 25, "color": "rgba(144,238,144,0.3)"},
        {"label": "Hot", "y0": 25, "y1": 35, "color": "rgba(255,165,0,0.3)"},
        {
            "label": "Very hot",
            "y0": 35,
            "y1": 1000000000,
            "color": "rgba(255,69,0,0.3)",
        },
    ],
    "RH2M": [  # độ ẩm (%)
        {"label": "Low", "y0": 0, "y1": 50, "color": "rgba(255,228,181,0.3)"},
        {"label": "High", "y0": 50, "y1": 80, "color": "rgba(173,216,230,0.3)"},
        {
            "label": "Very high",
            "y0": 80,
            "y1": 1000000000,
            "color": "rgba(30,144,255,0.3)",
        },
    ],
    "PRECTOTCORR": [  # lượng mưa (mm/h)
        {
            "label": "Light intensity",
            "y0": 0,
            "y1": 2.5,
            "color": "rgba(211,211,211,0.3)",
        },
        {"label": "Moderate", "y0": 2.5, "y1": 10, "color": "rgba(30,144,255,0.3)"},
        {"label": "Heavy", "y0": 10, "y1": 1000000000, "color": "rgba(75,0,130,0.3)"},
    ],
    "ALLSKY_SFC_SW_DWN": [  # bức xạ mặt trời (W/m²)
        {"label": "Weak", "y0": 0, "y1": 200, "color": "rgba(211,211,211,0.3)"},
        {"label": "Average", "y0": 200, "y1": 600, "color": "rgba(255,255,0,0.3)"},
        {"label": "Strong", "y0": 600, "y1": 1000, "color": "rgba(255,165,0,0.3)"},
        {
            "label": "Very strong",
            "y0": 1000,
            "y1": 1000000000,
            "color": "rgba(255,69,0,0.3)",
        },
    ],
}
