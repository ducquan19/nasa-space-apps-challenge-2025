async function getForecast() {
  const place = document.getElementById("place").value;
  const date = document.getElementById("date").value;

  if (!place || !date) {
    alert("Vui lòng nhập địa điểm và ngày!");
    return;
  }

  try {
    const res = await fetch(
      `http://127.0.0.1:8000/forecast?place=${encodeURIComponent(
        place
      )}&date=${date}`
    );
    const data = await res.json();

    if (data.error) {
      alert(data.error);
      return;
    }

    // Hiển thị summary
    // let summaryHtml = `<h2>Kết quả cho ${data.place} (${data.coords.lat.toFixed(
    //   2
    // )}, ${data.coords.lon.toFixed(2)}) - ${data.date}</h2>`;
    // summaryHtml += `<h3>Daily Summary</h3><ul>`;
    // for (const [param, stats] of Object.entries(data.daily_summary)) {
    //   summaryHtml += `<li><b>${param}</b>: Mean=${stats.mean.toFixed(
    //     2
    //   )}, Min=${stats.min.toFixed(2)}, Max=${stats.max.toFixed(2)}</li>`;
    // }
    // summaryHtml += `</ul>`;
    // document.getElementById("summary").innerHTML = summaryHtml;

    // Vẽ biểu đồ
    const chartsDiv = document.getElementById("charts");
    chartsDiv.innerHTML = "";
    Object.keys(data.figures).forEach((param) => {
      const figData = JSON.parse(data.figures[param]); // parse lại string JSON
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
