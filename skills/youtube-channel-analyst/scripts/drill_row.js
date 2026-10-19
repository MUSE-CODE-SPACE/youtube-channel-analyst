// 표에서 제목이 __ROW__ 인 행을 클릭해 하위 분류(예: YouTube 검색 → 검색어)로 들어간다.
(function () {
  var want = "__ROW__";
  var rows = document.querySelectorAll("yta-explore-table-row");
  for (var i = 0; i < rows.length; i++) {
    var cell = rows[i].querySelector("yta-title-cell") || rows[i];
    if ((cell.innerText || "").trim() === want) {
      var target = cell.querySelector("#entity-title-value, #title-and-thumbnail") || cell;
      ["mousedown", "mouseup", "click"].forEach(function (t) {
        target.dispatchEvent(new MouseEvent(t, { bubbles: true, cancelable: true, view: window }));
      });
      return "clicked";
    }
  }
  return "not-found";
})();
