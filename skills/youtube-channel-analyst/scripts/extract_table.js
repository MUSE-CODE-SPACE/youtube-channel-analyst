// YouTube Studio 분석 '고급 모드' 표를 JSON으로 추출. Safari do JavaScript 로 실행.
(function () {
  var clean = function (s) { return (s || "").replace(/\s+/g, " ").trim(); };
  var header = document.querySelector("yta-explore-table-header");
  if (!header) return JSON.stringify({ error: "no-table" });
  var cols = [].map.call(header.querySelectorAll(".metric-column"), function (c) { return clean(c.innerText); });
  var dimName = clean((header.querySelector(".dimension-column") || {}).innerText);
  var rows = [];
  document.querySelectorAll("yta-explore-table-row").forEach(function (r) {
    var dimCell = r.querySelector(".dimension-column");
    var title = clean(((dimCell && dimCell.querySelector("yta-title-cell")) || dimCell || {}).innerText);
    var html = dimCell ? dimCell.innerHTML : "";
    var vid = (html.match(/(?:vi(?:_webp)?\/|video\/)([A-Za-z0-9_-]{11})/) || [])[1] || null;
    var vals = [].map.call(r.querySelectorAll(".metric-column"), function (c) {
      var v = c.querySelector(".value");
      return clean(v ? v.innerText : c.innerText);
    });
    rows.push({ title: title, video_id: vid, values: vals });
  });
  var period = ((document.body.innerText.match(/\d{4}\. ?\d{1,2}\. ?\d{1,2}\. ?~ ?(?:\d{4}\. ?\d{1,2}\. ?\d{1,2}\.|현재)/) || [""])[0]);
  return JSON.stringify({ dimension: dimName, columns: cols, rows: rows, url: location.href, period: period });
})();
