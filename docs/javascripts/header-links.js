/*
 * Adds header (top-bar) links on every page: a "GDocs Drive" link and a
 * "Photo Album/Scans" link, in that order, just left of the search box.
 * Re-runs on each instant navigation via Material's document$.
 */
(function () {
  var PHOTO_URL =
    "https://photos.google.com/share/AF1QipPZh0VSw9xNnSlLXymxUNTLKFUZMe3jHexgGj0MWOzPgkbCXOxvT4X256yFpPueDQ?key=SjQzRnZOVUh0UUhxQy1YV2d2aDNFek41TWo2RUJ3";
  var DRIVE_URL =
    "https://drive.google.com/drive/folders/1ijbCSIdNw8ovS7D-P8Z6L6IPu-dcvs44?usp=sharing";

  function makeLink(extraClass, href, title, label, iconPath) {
    var a = document.createElement("a");
    a.className = "md-header__extlink " + extraClass;
    a.href = href;
    a.target = "_blank";
    a.rel = "noopener";
    a.title = title;
    a.innerHTML =
      '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">' +
      '<path fill="currentColor" d="' + iconPath + '"/>' +
      "</svg><span>" + label + "</span>";
    return a;
  }

  function setup() {
    var inner = document.querySelector(".md-header__inner");
    if (!inner || inner.querySelector(".md-header__extlink")) return;

    var drive = makeLink(
      "md-header__drivelink",
      DRIVE_URL,
      "GDocs Drive",
      "GDocs Drive",
      // Google Drive triangle glyph
      "M7.71 3.5 1.15 15l3.43 5.5 6.56-11.5zm8.58 0H9.42l6.56 11.5h6.87zm-1.7 13H4.94L1.5 22h13.16l3.43-5.5z"
    );
    var photo = makeLink(
      "md-header__photolink",
      PHOTO_URL,
      "Photo Album / Scans",
      "Photo Album/Scans",
      // Picture/landscape glyph
      "M21 19V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2M8.5 13.5l2.5 3.01L14.5 12l4.5 6H5z"
    );

    var search = inner.querySelector(".md-search");
    if (search) {
      inner.insertBefore(drive, search);
      inner.insertBefore(photo, search);
    } else {
      inner.appendChild(drive);
      inner.appendChild(photo);
    }
  }

  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(setup);
  } else {
    document.addEventListener("DOMContentLoaded", setup);
  }
})();
