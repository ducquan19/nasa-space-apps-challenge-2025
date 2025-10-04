////// Tìm kiếm tọa độ dùng API

import { apiKey } from "./config.js";

export async function getCoordinates(city) {
  // Return 1 result
  const url = `http://api.openweathermap.org/geo/1.0/direct?q=${city}&limit=1&appid=${apiKey}`;
  const response = await fetch(url);
  if (!response.ok) throw new Error("City not found");
  const data = await response.json();
  if (data.length === 0) throw new Error("City not found");
  return {
    lat: data[0].lat,
    lon: data[0].lon,
    local_name: data[0].local_names,
    country: data[0].country,
  };
}

export async function getNameByCoordinates(lat, lon) {
  const url = `https://api.openweathermap.org/geo/1.0/reverse?lat=${lat}&lon=${lon}&limit=1&appid=${apiKey}`;
  const response = await fetch(url);
  const data = await response.json();
  let placeName = "Unknown place";
  if (data && data.length > 0) {
    placeName = data[0].name;
  }
  return { place_name: placeName, country: data[0].country };
}

////// Hàm lấy thông tin độ cao và khí hậu

// Lấy độ cao từ Open-Elevation API
export async function getElevation(lat, lon) {
  let elevation = null;
  try {
    const url = `https://api.open-elevation.com/api/v1/lookup?locations=${lat},${lon}`;
    //const url = `https://api.opentopodata.org/v1/test-dataset?locations=${lat},${lon}`;
    const res = await fetch(url);
    const data = await res.json();
    if (data && data.results && data.results.length > 0) {
      elevation = data.results[0].elevation; // mét
    }
  } catch (err) {
    console.error("Lỗi lấy độ cao:", err);
  }
  return elevation;
}

// Lấy vùng khí hậu từ GeoTIFF

import { koppenClasses } from "./map.js";

export function getClimate(lat, lon, georaster) {
  let climateCode = null;
  let climateType = "Unknown";

  try {
    if (georaster) {
      // Lấy thông tin từ georaster
      const xmin = georaster.xmin;
      const ymax = georaster.ymax;
      const pixelWidth = georaster.pixelWidth;
      const pixelHeight = georaster.pixelHeight;

      // Tính chỉ số pixel (col, row)
      const xPixel = Math.floor((lon - xmin) / pixelWidth);
      const yPixel = Math.floor((ymax - lat) / pixelHeight);

      // Đọc giá trị từ band 0
      if (
        yPixel >= 0 &&
        yPixel < georaster.height &&
        xPixel >= 0 &&
        xPixel < georaster.width
      ) {
        const value = georaster.values[0][yPixel][xPixel];
        if (koppenClasses[value]) {
          climateType = `${koppenClasses[value].name}`;
          climateCode = `${koppenClasses[value].code}`;
        }
      }
    }
  } catch (err) {
    console.error("Lỗi đọc dữ liệu khí hậu:", err);
  }

  return { climateCode, climateType };
}

////// Hàm Lấy thời tiết hiện tại

async function getCurrentWeather(lat, lon) {
  const url = `https://api.openweathermap.org/data/2.5/weather?lat=${lat}&lon=${lon}&appid=${apiKey}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error("Could not fetch weather data");
  }
  return await response.json();
}

////// Cấu hình các option button: mở và đóng

const titles = {
  "ten-days": "Weather for 10 days",
  hourly: "Hourly Weather",
  planning: "For planning",
  self: "Self forecasting",
};

document.querySelectorAll("button[data-target]").forEach((btn) => {
  btn.addEventListener("click", () => {
    const key = btn.getAttribute("data-target");
    const existingBox = document.getElementById("box-" + key);
    const main = document.querySelector("main");

    if (existingBox) {
      // Nếu tồn tại rồi thì remove div
      existingBox.remove();
    } else {
      // Nếu chưa thì tạo mới div
      const div = document.createElement("div");
      div.className = "info-box";
      div.id = "box-" + key;
      div.innerHTML = `<div class="info-title">${titles[key]}</div>
                        <p>Nội dung hiển thị cho ${titles[key]}...</p>`;

      main.insertAdjacentElement("afterend", div); // Thêm bên cạnh main

      // Scroll xuống div vừa tạo
      // div.scrollIntoView({ behavior: "smooth" });
    }
  });
});

//Hàm cập nhật background theo vị trí
function updateBacground(description) {
  const info = document.getElementById("info");
  if (!info) return;

  info.classList.remove(
    "clear",
    "cloud",
    "rain",
    "snow",
    "thunderstorm",
    "mist",
    "sunny"
  );

  const desc = description.toLowerCase();
  if (desc.includes("clear")) {
    info.classList.add("clear");
  } else if (desc.includes("cloud")) {
    info.classList.add("cloud");
  } else if (desc.includes("rain") || desc.includes("drizzle")) {
    info.classList.add("rain");
  } else if (desc.includes("snow")) {
    info.classList.add("snow");
  } else if (desc.includes("thunder")) {
    info.classList.add("thunderstorm");
  } else if (
    desc.includes("mist") ||
    desc.includes("fog") ||
    desc.includes("haze")
  ) {
    info.classList.add("mist");
  } else info.classList.add("sunny");
}

////// Hàm cập nhật tất cả thông tin

export async function updateInfo(
  lat,
  lon,
  climateCode,
  climateType,
  elevation,
  place_name,
  country
) {
  document.getElementById("location_name").innerHTML =
    place_name + ", " + country;
  document.getElementById("elevation").innerHTML =
    "Leviation: " + elevation + "m";
  const containerClimate = document.getElementById("climate_type");
  containerClimate.innerHTML = `Climate: <a class="climate-link" data-code="${climateCode}">${climateType}</a>`;
  // click khí hậu
  const link = containerClimate.querySelector(".climate-link");
  link.onclick = function () {
    showClimatePopup(climateCode, climateType);
  };

  try {
    const current = await getCurrentWeather(lat, lon);
    // Thông tin chính
    const tempC = (current.main.temp - 273.15).toFixed(1);
    const feelsC = (current.main.feels_like - 273.15).toFixed(1);

    document.getElementById("temperature").innerHTML = `${tempC}°C`;
    document.getElementById("weather_desc").innerHTML =
      current.weather[0].description;
    document.getElementById("feels_like").innerHTML = `Feels like: ${feelsC}°C`;
    const description = current.weather[0].main;
    updateBacground(description);
    // Icon thời tiết
    document.getElementById(
      "weather_icon"
    ).src = `http://openweathermap.org/img/wn/${current.weather[0].icon}@2x.png`;

    // Min/Max
    const minC = (current.main.temp_min - 273.15).toFixed(1);
    const maxC = (current.main.temp_max - 273.15).toFixed(1);
    document.getElementById(
      "temp_range"
    ).innerHTML = `Min ${minC}°C / Max ${maxC}°C`;

    // Humidity
    const humidity = current.main.humidity;
    document.getElementById("humidity_value").innerHTML = `${humidity}%`;
    document.getElementById("humidity_bar").style.width = humidity + "%";

    // Wind
    const wind_ms = current.wind.speed;
    const wind_kmh = (wind_ms * 3.6).toFixed(1);
    document.getElementById(
      "wind_value"
    ).innerHTML = `${wind_ms} m/s (${wind_kmh} km/h)`;

    // Precipitation
    let precip = 0;
    if (current.rain && current.rain["1h"]) precip = current.rain["1h"];
    if (current.snow && current.snow["1h"]) precip = current.snow["1h"];
    document.getElementById("precip_value").innerHTML = `${precip} mm`;

    // UV Index (OpenWeather cần API riêng, tạm để mock)
    let uv = "Moderate";
    document.getElementById("uv_index").innerHTML = uv;

    // Comfort level (demo: cấp 2/5)
    const bars = document.querySelectorAll(".comfort_bar");
    bars.forEach((b, i) => {
      b.style.background = i < 2 ? "#4caf50" : "#ddd"; // tô màu 2 ô
    });
  } catch (err) {
    console.error("Error updating info:", err);
  }
}

////// Modal popup cho thông tin khí hậu

function showClimatePopup(climateCode, climateType) {
  const modal = document.getElementById("climate_modal");
  const title = document.getElementById("climate_title");
  const desc = document.getElementById("climate_description");

  title.textContent = `${climateCode} - ${climateType}`;
  // Đọc file txt có tên trùng với climateCode
  fetch(`./data/climate/desc-en/${climateCode}.txt`)
    .then((response) => {
      if (!response.ok) {
        throw new Error("Không tìm thấy file " + climateCode + ".txt");
      }
      return response.text();
    })
    .then((text) => {
      // Giữ xuống dòng trong file txt khi hiển thị
      desc.innerHTML = text.replace(/\n/g, "<br>");
    })
    .catch((err) => {
      desc.textContent = "Không có dữ liệu mô tả cho khí hậu này.";
      console.error(err);
    });

  // Load ảnh
  for (let i = 1; i <= 4; i++) {
    const imgEl = document.getElementById(`img${i}`);
    imgEl.src = `./data/climate/img/${climateCode}-${i}.jpg`;
    imgEl.alt = `${climateType} - Ảnh ${i}`;
  }
  modal.style.display = "block";
}

// Đóng modal khi bấm dấu X
document.querySelector(".modal .close").onclick = function () {
  document.getElementById("climate_modal").style.display = "none";
};

// Đóng modal khi click ra ngoài
window.onclick = function (event) {
  const modal = document.getElementById("climate_modal");
  if (event.target === modal) {
    modal.style.display = "none";
  }
};
