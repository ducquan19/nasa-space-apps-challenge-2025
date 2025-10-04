import {
  getClimate,
  getCoordinates,
  getElevation,
  getNameByCoordinates,
  updateInfo,
} from "./script.js";

////// Cấu hình bản đồ cơ bản

const map = L.map("map", { preferCanvas: true }).setView([20, 0], 2);
const osm = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: "© OpenStreetMap",
}).addTo(map);
const topo = L.tileLayer("https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png", {
  maxZoom: 17,
  attribution: "© OpenTopoMap",
});

// Nhóm chứa các đối tượng vẽ
const drawnItems = new L.FeatureGroup();
map.addLayer(drawnItems);

// Thêm control để vẽ polygon
const drawControl = new L.Control.Draw({
  edit: { featureGroup: drawnItems },
  draw: {
    polygon: true,
    polyline: false,
    rectangle: false,
    circle: false,
    marker: false,
    circlemarker: false,
  },
});
map.addControl(drawControl);

// Khi vẽ xong 1 đa giác
map.on(L.Draw.Event.CREATED, function (e) {
  const layer = e.layer;
  drawnItems.addLayer(layer);

  // Lấy mảng tọa độ (lat, lng)
  const coords = layer.getLatLngs()[0].map((pt) => [pt.lat, pt.lng]);
  console.log("Tọa độ đa giác vừa vẽ:", coords);
});

// Khi edit hoặc delete thì log lại toàn bộ
map.on("draw:edited draw:deleted", function () {
  drawnItems.eachLayer((layer) => {
    const coords = layer.getLatLngs()[0].map((pt) => [pt.lat, pt.lng]);
    console.log("Tọa độ sau chỉnh sửa:", coords);
  });
});

// Mask che phủ text Biển Đông
var mask1 = L.circle([16.4045, 111.8198], {
  radius: 150000,
  color: "rgb(170, 211, 223)",
  fillColor: "rgb(170, 211, 223)",
  fillOpacity: 1.0,
}).addTo(map);

var mask2 = L.circle([10.2794, 114.0521], {
  radius: 200000,
  color: "rgb(170, 211, 223)",
  fillColor: "rgb(170, 211, 223)",
  fillOpacity: 1.0,
}).addTo(map);

// GeoJSON overlay Biển Đông
var islands = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      geometry: { type: "Point", coordinates: [112.3, 16.5] },
      properties: { name: "Hoàng Sa" },
    },
    {
      type: "Feature",
      geometry: { type: "Point", coordinates: [114.3, 10.0] },
      properties: { name: "Trường Sa" },
    },
    {
      type: "Feature",
      geometry: { type: "Point", coordinates: [115.0, 14.0] },
      properties: { name: "Biển Đông" },
    },
  ],
};

// Label overlay cho Biển Đông
var labelLayer = L.geoJSON(islands, {
  pointToLayer: function (feature, latlng) {
    return L.marker(latlng, {
      icon: L.divIcon({
        className: "custom-label",
        html: feature.properties.name,
      }),
    });
  },
}).addTo(map);

// Thêm label Biển Đông khi zoom gần :V
map.on("zoomend", function () {
  var currentZoom = map.getZoom();
  if (currentZoom >= 5) {
    if (!map.hasLayer(labelLayer)) {
      map.addLayer(labelLayer);
    }
  } else {
    if (map.hasLayer(labelLayer)) {
      map.removeLayer(labelLayer);
    }
  }
});

const koppen_geiger = "data/koppen_geiger_0p1.tif"; //"data/koppen_geiger_0p00833333.tif"; // file tiff
// Bảng mapping Köppen-Geiger từ Beck et al. (2023)
export const koppenClasses = {
  1: { code: "Af", name: "Tropical, rainforest", color: "rgb(0,0,255)" },
  2: { code: "Am", name: "Tropical, monsoon", color: "rgb(0,120,255)" },
  3: { code: "Aw", name: "Tropical, savannah", color: "rgb(70,170,250)" },
  4: { code: "BWh", name: "Arid, desert, hot", color: "rgb(255,0,0)" },
  5: { code: "BWk", name: "Arid, desert, cold", color: "rgb(255,150,150)" },
  6: { code: "BSh", name: "Arid, steppe, hot", color: "rgb(245,165,0)" },
  7: { code: "BSk", name: "Arid, steppe, cold", color: "rgb(255,220,100)" },
  8: {
    code: "Csa",
    name: "Temperate, dry summer, hot summer",
    color: "rgb(255,255,0)",
  },
  9: {
    code: "Csb",
    name: "Temperate, dry summer, warm summer",
    color: "rgb(200,200,0)",
  },
  10: {
    code: "Csc",
    name: "Temperate, dry summer, cold summer",
    color: "rgb(150,150,0)",
  },
  11: {
    code: "Cwa",
    name: "Temperate, dry winter, hot summer",
    color: "rgb(150,255,150)",
  },
  12: {
    code: "Cwb",
    name: "Temperate, dry winter, warm summer",
    color: "rgb(100,200,100)",
  },
  13: {
    code: "Cwc",
    name: "Temperate, dry winter, cold summer",
    color: "rgb(50,150,50)",
  },
  14: {
    code: "Cfa",
    name: "Temperate, no dry season, hot summer",
    color: "rgb(200,255,80)",
  },
  15: {
    code: "Cfb",
    name: "Temperate, no dry season, warm summer",
    color: "rgb(100,255,80)",
  },
  16: {
    code: "Cfc",
    name: "Temperate, no dry season, cold summer",
    color: "rgb(50,200,0)",
  },
  17: {
    code: "Dsa",
    name: "Cold, dry summer, hot summer",
    color: "rgb(255,0,255)",
  },
  18: {
    code: "Dsb",
    name: "Cold, dry summer, warm summer",
    color: "rgb(200,0,200)",
  },
  19: {
    code: "Dsc",
    name: "Cold, dry summer, cold summer",
    color: "rgb(150,50,150)",
  },
  20: {
    code: "Dsd",
    name: "Cold, dry summer, very cold winter",
    color: "rgb(150,100,150)",
  },
  21: {
    code: "Dwa",
    name: "Cold, dry winter, hot summer",
    color: "rgb(170,175,255)",
  },
  22: {
    code: "Dwb",
    name: "Cold, dry winter, warm summer",
    color: "rgb(90,120,220)",
  },
  23: {
    code: "Dwc",
    name: "Cold, dry winter, cold summer",
    color: "rgb(75,80,180)",
  },
  24: {
    code: "Dwd",
    name: "Cold, dry winter, very cold winter",
    color: "rgb(50,0,135)",
  },
  25: {
    code: "Dfa",
    name: "Cold, no dry season, hot summer",
    color: "rgb(0,255,255)",
  },
  26: {
    code: "Dfb",
    name: "Cold, no dry season, warm summer",
    color: "rgb(55,200,255)",
  },
  27: {
    code: "Dfc",
    name: "Cold, no dry season, cold summer",
    color: "rgb(0,125,125)",
  },
  28: {
    code: "Dfd",
    name: "Cold, no dry season, very cold winter",
    color: "rgb(0,70,95)",
  },
  29: { code: "ET", name: "Polar, tundra", color: "rgb(178,178,178)" },
  30: { code: "EF", name: "Polar, frost", color: "rgb(102,102,102)" },
};

let georaster = null;

fetch(koppen_geiger)
  .then((response) => response.arrayBuffer())
  .then((arrayBuffer) => parseGeoraster(arrayBuffer))
  .then((result) => {
    georaster = result; // Gán để dùng sau

    // Tạo layer hiển thị Köppen-Geiger
    const Koppen_Geiger = new GeoRasterLayer({
      georaster,
      opacity: 0.6,
      pixelValuesToColorFn: (values) => {
        const val = values[0];
        if (val === -9999 || val === null) return null;
        return koppenClasses[val] ? koppenClasses[val].color : null;
      },
      resolution: 256,
    });
    // Thêm mặc định layer vào bản đồ
    Koppen_Geiger.addTo(map);

    // Bảng chọn layer
    L.control
      .layers({ OSM: osm, Topo: topo }, { "Köppen-Geiger": Koppen_Geiger })
      .addTo(map);
  })
  .catch((err) => console.error("Lỗi load GeoTIFF:", err));

// Tạo một layer group để chứa marker
const markersLayer = L.layerGroup().addTo(map);

////// Search form => mark on map + cập nhật

document.querySelector(".search-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const city = document.getElementById("locationInput").value.trim();
  if (!city) return;

  const coords = await getCoordinates(city);
  const elevation = await getElevation(coords.lat, coords.lon);
  const climate = await getClimate(coords.lat, coords.lon, georaster);
  if (coords) {
    map.setView([coords.lat, coords.lon], 8);
    markersLayer.clearLayers(); // Xóa toàn bộ marker cũ

    const marker = L.marker([coords.lat, coords.lon])
      .bindPopup(
        `${city}<br>Lat: ${coords.lat.toFixed(4)}, Lon: ${coords.lon.toFixed(
          4
        )}`
      )
      .openPopup();

    markersLayer.addLayer(marker); // Thêm marker vào layer group
    // Cập nhật
    updateInfo(
      coords.lat,
      coords.lon,
      climate.climateCode,
      climate.climateType,
      elevation,
      coords.local_name["en"],
      coords.country
    );
  }
});

////// Mark on map => cập nhật

map.on("click", async function (e) {
  // Xóa các marker cũ
  markersLayer.clearLayers();

  const lat = e.latlng.lat;
  const lon = e.latlng.lng;
  const elevation = await getElevation(lat, lon);
  const climate = await getClimate(lat, lon, georaster);

  try {
    let data = await getNameByCoordinates(lat, lon);

    // Cắm marker tại vị trí click
    const marker = L.marker([lat, lon])
      .bindPopup(
        `${data.place_name}<br>Lat: ${lat.toFixed(4)}, Lon: ${lon.toFixed(4)}`
      )
      .openPopup();

    markersLayer.addLayer(marker);

    console.log("Clicked:", lat, lon, data.place_name);
    // Cập nhật
    updateInfo(
      lat,
      lon,
      climate.climateCode,
      climate.climateType,
      elevation,
      data.place_name,
      data.country
    );
  } catch (error) {
    console.error("Error fetching location:", error);
  }
});

// Mặc định Ho Chi Minh - Lat: 10.7758, Lon: 106.7018
