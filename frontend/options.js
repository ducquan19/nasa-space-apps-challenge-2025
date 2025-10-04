////// Weather for 10 days dùng openweather

import { apiKey } from "./config.js";

async function getForecast10days(lat, lon, cnt = 10) {
  const url = `https://api.openweathermap.org/data/2.5/forecast/daily?lat=${lat}&lon=${lon}&cnt=${cnt}&units=metric&appid=${apiKey}`;
  const response = await fetch(url);
  if (!response.ok) throw new Error("Could not fetch forecast data");
  return await response.json();
}

////// Hourly weather dùng mô hình dự đoán

document.addEventListener("DOMContentLoaded", () => {
  // Mặc định ngày hiện tại
  const today = new Date().toISOString().split("T")[0];
  document.getElementById("startDate").value = today;
  document.getElementById("endDate").value = today;
});

async function getForecastByModel() {
  const place = document.getElementById("locationInput").value;
  const date1 = document.getElementById("startDate").value;
  const date2 = document.getElementById("endDate").value;

  if (!place || !date1 || !date2) {
    alert("Vui lòng nhập địa điểm và ngày!");
    return;
  }

  // So sánh theo ngày/tháng/năm
  if (new Date(date1).toDateString() === new Date(date2).toDateString()) {
    ///////  Dự báo 1 ngày
    const date = date1;
    try {
      // Kiểm tra box-hourly
      let boxHourly = document.getElementById("box-hourly");
      if (!boxHourly) {
        const btnHourly = document.querySelector(".btn.btn--hourly");
        if (btnHourly) btnHourly.click();
        // chờ cho DOM render
        await new Promise((resolve) => setTimeout(resolve, 300));
        boxHourly = document.getElementById("box-hourly");
      }

      // Tạo hoặc reset chartsHourly
      let chartsDiv = document.getElementById("chartsHourly");
      if (!chartsDiv) {
        chartsDiv = document.createElement("div");
        chartsDiv.id = "chartsHourly";
        boxHourly.appendChild(chartsDiv);
      }
      chartsDiv.innerHTML = `<p style="text-align:center">Loading...</p>`;
      chartsDiv.scrollIntoView({ behavior: "smooth" });

      // Gọi API
      const res = await fetch(
        `http://127.0.0.1:8000/forecast_point_one_day?place=${encodeURIComponent(
          place
        )}&date=${date}`
      );

      const data = await res.json();

      // Xóa loading khi có dữ liệu
      chartsDiv.innerHTML = "";

      if (data.error) {
        alert(data.error);
        return;
      }

      //  Vẽ biểu đồ
      Object.keys(data.figures).forEach((param) => {
        const figData = JSON.parse(data.figures[param]);
        const container = document.createElement("div");
        container.className = "chart";
        container.id = "chart_" + param;
        chartsDiv.appendChild(container);

        Plotly.newPlot(container, figData.data, figData.layout);
      });
    } catch (err) {
      console.error(err);
      alert("Lỗi khi gọi API!");
    }
  } else {
    ///////  Dự báo nhiều ngày
    try {
      // Kiểm tra box-ten-days
      let boxTenDays = document.getElementById("box-ten-days");
      if (!boxTenDays) {
        const btnHourly = document.querySelector(".btn.btn--primary");
        if (btnHourly) btnHourly.click();
        // chờ cho DOM render
        await new Promise((resolve) => setTimeout(resolve, 300));
        boxTenDays = document.getElementById("box-ten-days");
      }

      // Tạo hoặc reset chartsHourly
      let chartsDiv = document.getElementById("chartsTenDays");
      if (!chartsDiv) {
        chartsDiv = document.createElement("div");
        chartsDiv.id = "chartsTenDays";
        boxTenDays.appendChild(chartsDiv);
      }
      chartsDiv.innerHTML = `<p style="text-align:center">Loading...</p>`;
      chartsDiv.scrollIntoView({ behavior: "smooth" });

      // Gọi API
      const res = await fetch(
        `http://127.0.0.1:8000/forecast_point_many_days?place=${encodeURIComponent(
          place
        )}&start_date=${date1}&end_date=${date2}`
      );

      const data = await res.json();

      // Xóa loading khi có dữ liệu
      chartsDiv.innerHTML = "";

      if (data.error) {
        alert(data.error);
        return;
      }

      //  Vẽ biểu đồ
      Object.keys(data.figures).forEach((param) => {
        const figData = JSON.parse(data.figures[param]);
        const container = document.createElement("div");
        container.className = "chart";
        container.id = "chart_" + param;
        chartsDiv.appendChild(container);

        Plotly.newPlot(container, figData.data, figData.layout);
      });
    } catch (err) {
      console.error(err);
      alert("Lỗi khi gọi API!");
    }
  }
}
window.getForecastByModel = getForecastByModel; // gán vào global để sử dụng trên button Get  Weather
const btnHourly = document.querySelector(".btn.btn--hourly");
btnHourly.onclick = getForecastByModel;

// C:\Python313\python.exe -m uvicorn main:app --reload
