(function () {
  'use strict';

  var BULAN_ID = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember"];

  var DATA = JSON.parse(document.getElementById('dashboard-data').textContent);
  var INDONESIA_BOUNDS = [[-11.4, 94.7], [6.4, 141.5]];
  var GEOJSON_URL = document.body.getAttribute('data-geojson-url');

  var currentView = 'dashboard';
  var map = null;
  var mapBuilt = false;
  var provinceBounds = null;
  var echartInstances = [];

  // ---------------- clock ----------------
  function tick() {
    var now = new Date();
    var dateLabel = document.getElementById('date-label');
    var timeLabel = document.getElementById('time-label');
    if (dateLabel) dateLabel.textContent = now.getDate() + ' ' + BULAN_ID[now.getMonth() + 1] + ' ' + now.getFullYear();
    if (timeLabel) {
      var pad = function (n) { return String(n).padStart(2, '0'); };
      timeLabel.textContent = pad(now.getHours()) + ':' + pad(now.getMinutes()) + ':' + pad(now.getSeconds());
    }
  }
  tick();
  setInterval(tick, 1000);

  // ---------------- sidebar toggle ----------------
  var sidebarEl = document.querySelector('.sidebar');
  var sidebarToggleIcon = document.getElementById('sidebar-toggle-icon');
  var isMobile = window.matchMedia && window.matchMedia('(max-width: 760px)').matches;
  if (isMobile && sidebarEl && sidebarToggleIcon) {
    sidebarEl.classList.add('hidden');
    sidebarToggleIcon.textContent = 'menu';
  }
  if (sidebarToggleIcon) {
    sidebarToggleIcon.addEventListener('click', function () {
      var show = sidebarEl.classList.contains('hidden');
      sidebarEl.classList.toggle('hidden', !show);
      sidebarToggleIcon.textContent = show ? 'menu_open' : 'menu';
    });
  }
  // On mobile the sidebar opens as an overlay (see CSS) — tapping a menu
  // item should close it again instead of leaving it covering the view.
  document.querySelectorAll('.menu-item[data-view]').forEach(function (row) {
    row.addEventListener('click', function () {
      if (isMobile && sidebarEl && !sidebarEl.classList.contains('hidden')) {
        sidebarEl.classList.add('hidden');
        if (sidebarToggleIcon) sidebarToggleIcon.textContent = 'menu';
      }
    });
  });

  // ---------------- echarts ----------------
  function renderEchart(el) {
    if (!window.echarts || !el || el.dataset.echartsRendered) return;
    var optionId = el.getAttribute('data-option-id');
    var option = optionId ? getByPath(DATA, optionId) : null;
    if (!option) return;
    var inst = echarts.init(el);
    inst.setOption(option);
    el.dataset.echartsRendered = '1';
    echartInstances.push(inst);
  }

  function getByPath(obj, path) {
    return path.split('.').reduce(function (acc, key) {
      return acc && acc[key] !== undefined ? acc[key] : undefined;
    }, obj);
  }

  function renderEchartsIn(container) {
    var nodes = container.querySelectorAll('[data-echart]');
    nodes.forEach(renderEchart);
  }

  window.addEventListener('resize', function () {
    echartInstances.forEach(function (inst) { inst.resize(); });
    if (currentView === 'peta') refreshMap();
  });

  // ---------------- leaflet map ----------------
  function buildMap() {
    if (mapBuilt || !window.L) return;
    mapBuilt = true;
    map = L.map('regional-map', {
      center: [-2.5, 117.5], zoom: 5,
      zoomControl: false, attributionControl: false, dragging: false,
      scrollWheelZoom: false, doubleClickZoom: false, boxZoom: false,
      touchZoom: false, keyboard: false, tap: false, worldCopyJump: false,
    });

    // Dedicated pane above the geojson overlay pane so location markers
    // always render on top, even though the province geojson loads async
    // and can otherwise land in the DOM after the markers.
    map.createPane('regionalMarkerPane');
    map.getPane('regionalMarkerPane').style.zIndex = 650;

    if (GEOJSON_URL) {
      fetch(GEOJSON_URL).then(function (r) { return r.json(); }).then(function (geojson) {
        var layer = L.geoJSON(geojson, {
          style: function (feature) {
            var p = feature.properties || {};
            return { color: p.border || '#2FA84F', weight: 1, fillColor: p.fill || '#3F8F52', fillOpacity: 0.95, opacity: 0.95 };
          },
        }).addTo(map);
        provinceBounds = layer.getBounds();
        map.invalidateSize();
        map.fitBounds(provinceBounds, { padding: [10, 10] });
      }).catch(function () { /* map still usable without base layer */ });
    }

    (DATA.regional_locations || []).forEach(function (loc) {
      var marker = L.circleMarker([loc.lat, loc.lng], {
        radius: 12, color: '#0B1220', weight: 3, fillColor: loc.color, fillOpacity: 0.95,
        pane: 'regionalMarkerPane',
      }).addTo(map);
      var info = '<b>' + loc.no + '. ' + escapeHtml(loc.provinsi) + '</b><br>' + escapeHtml(loc.kota) + '<br>' +
        '<span style="color:#8FC9FF">' + escapeHtml(loc.proyek) + '</span><br>' +
        '<span style="color:' + loc.color + ';font-weight:700">● Pekerjaan: ' + escapeHtml(loc.status) + '</span><br>' +
        '<span style="color:' + loc.furniture_color + ';font-weight:700">● Furniture: ' + escapeHtml(loc.furniture_status) + '</span>' +
        (loc.keterangan && loc.keterangan !== '-'
          ? '<br><span style="color:#93B4CE;font-size:11px">' + escapeHtml(loc.keterangan) + '</span>' : '');
      marker.bindPopup(info, { closeButton: false });
      marker.on('mouseover', function () { marker.openPopup(); });
      marker.on('mouseout', function () { marker.closePopup(); });
    });
  }

  function escapeHtml(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function refreshMap() {
    if (!map) return;
    setTimeout(function () {
      map.invalidateSize();
      map.fitBounds(provinceBounds || INDONESIA_BOUNDS, { padding: [10, 10] });
    }, 100);
  }

  // ---------------- view switching ----------------
  function switchView(key) {
    currentView = key;
    document.querySelectorAll('.view-panel').forEach(function (panel) {
      panel.classList.toggle('active', panel.getAttribute('data-view') === key);
    });
    document.querySelectorAll('.menu-item[data-view]').forEach(function (row) {
      row.classList.toggle('active', row.getAttribute('data-view') === key);
    });
    var activePanel = document.querySelector('.view-panel[data-view="' + key + '"]');
    if (activePanel) renderEchartsIn(activePanel);

    if (key === 'peta') {
      buildMap();
      refreshMap();
    }

    document.documentElement.dataset.activeView = key;
    setTimeout(function () {
      if (document.documentElement.classList.contains('app-fullscreen')) fitFullscreenDashboard();
    }, 150);
  }

  document.querySelectorAll('.menu-item[data-view]').forEach(function (row) {
    row.addEventListener('click', function () { switchView(row.getAttribute('data-view')); });
  });

  // ---------------- fullscreen ----------------
  function fitFullscreenDashboard() {
    var shell = document.querySelector('.dash-shell');
    if (!shell) return;
    shell.style.transform = 'none';
    if (document.documentElement.dataset.activeView === 'peta') {
      shell.style.width = '100%';
      refreshMap();
      return;
    }
    shell.style.width = '';
    var naturalW = shell.scrollWidth;
    var naturalH = shell.scrollHeight;
    if (!naturalW || !naturalH) return;
    var scale = Math.min(window.innerWidth / naturalW, window.innerHeight / naturalH);
    shell.style.transform = 'scale(' + scale + ')';
    shell.style.width = (100 / scale) + '%';
    // Changing shell width just now resized every chart's container, but
    // echarts only redraws on a native window resize, so force it here too.
    echartInstances.forEach(function (inst) { inst.resize(); });
  }

  function resetFullscreenDashboard() {
    var shell = document.querySelector('.dash-shell');
    if (!shell) return;
    shell.style.transform = '';
    shell.style.width = '100%';
    echartInstances.forEach(function (inst) { inst.resize(); });
    if (currentView === 'peta') refreshMap();
  }

  function onFullscreenChange() {
    var active = !!(document.fullscreenElement || document.webkitFullscreenElement);
    document.documentElement.classList.toggle('app-fullscreen', active);
    if (active) {
      setTimeout(fitFullscreenDashboard, 60);
    } else {
      resetFullscreenDashboard();
    }
  }
  ['fullscreenchange', 'webkitfullscreenchange'].forEach(function (evt) {
    document.addEventListener(evt, onFullscreenChange);
  });
  window.addEventListener('resize', function () {
    if (document.documentElement.classList.contains('app-fullscreen')) fitFullscreenDashboard();
  });

  var fullscreenBtn = document.getElementById('fullscreen-toggle');
  if (fullscreenBtn) {
    fullscreenBtn.addEventListener('click', function () {
      if (document.fullscreenElement) {
        document.exitFullscreen();
      } else {
        document.documentElement.requestFullscreen();
      }
    });
  }

  // ---------------- init ----------------
  document.documentElement.dataset.activeView = 'dashboard';
  switchView('dashboard');
})();
