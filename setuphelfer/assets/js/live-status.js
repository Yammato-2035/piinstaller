(function () {
  "use strict";

  var root = document.getElementById("setuphelfer-live-status");
  if (!root) return;

  var stateEl = root.querySelector("[data-live-state]");
  var cpuEl = root.querySelector("[data-live-cpu]");
  var ramEl = root.querySelector("[data-live-ram]");
  var diskEl = root.querySelector("[data-live-disk]");
  var hostEl = root.querySelector("[data-live-host]");
  var osEl = root.querySelector("[data-live-os]");
  var networkEl = root.querySelector("[data-live-network]");
  var uptimeEl = root.querySelector("[data-live-uptime]");
  var installEl = root.querySelector("[data-live-install]");
  var lastEl = root.querySelector("[data-live-last]");

  var pollTimer = null;
  var pollMs = 10000;
  var timeoutMs = 3000;

  function setText(el, text) {
    if (el) el.textContent = text;
  }

  function formatBytes(bytes) {
    if (!Number.isFinite(bytes) || bytes <= 0) return "-";
    var units = ["B", "KB", "MB", "GB", "TB"];
    var i = 0;
    var value = bytes;
    while (value >= 1024 && i < units.length - 1) {
      value /= 1024;
      i += 1;
    }
    return value.toFixed(i === 0 ? 0 : 1) + " " + units[i];
  }

  function setConnectionState(label) {
    setText(stateEl, label);
  }

  function clearMetrics() {
    setText(cpuEl, "-");
    setText(ramEl, "-");
    setText(diskEl, "-");
    setText(hostEl, "-");
    setText(osEl, "-");
    setText(networkEl, "-");
    setText(uptimeEl, "-");
    setText(installEl, "-");
    setText(lastEl, "-");
  }

  function requestJson(url) {
    var controller = new AbortController();
    var t = setTimeout(function () {
      controller.abort();
    }, timeoutMs);
    return fetch(url, { signal: controller.signal })
      .then(function (r) {
        clearTimeout(t);
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      })
      .catch(function (e) {
        clearTimeout(t);
        throw e;
      });
  }

  function candidates(path) {
    var origin = window.location.origin;
    return [
      origin + path,
      path,
      "http://localhost:8000" + path
    ];
  }

  function probeHealthy() {
    var urls = candidates("/health");
    var idx = 0;
    function next() {
      if (idx >= urls.length) return Promise.reject(new Error("no-backend"));
      var url = urls[idx++];
      return requestJson(url).then(function (data) {
        if (data && data.status === "ok") return url.replace(/\/health$/, "");
        throw new Error("bad-health");
      }).catch(next);
    }
    return next();
  }

  function loadSystem(baseUrl) {
    return requestJson(baseUrl + "/api/system-info?light=1");
  }

  function loadStatus(baseUrl) {
    return requestJson(baseUrl + "/api/status");
  }

  function loadNetwork(baseUrl) {
    return requestJson(baseUrl + "/api/system/network");
  }

  function updateMetrics(systemData, statusData, networkData) {
    var cpuUsage = systemData && systemData.cpu && typeof systemData.cpu.usage === "number" ? systemData.cpu.usage.toFixed(1) + " %" : "-";
    var memory = systemData && systemData.memory ? systemData.memory : null;
    var disk = systemData && systemData.disk ? systemData.disk : null;
    var hostname = "-";
    var uptime = systemData && systemData.uptime ? systemData.uptime : "-";
    var osName = systemData && systemData.os && systemData.os.name ? systemData.os.name : "-";
    var networkState = "Keine Daten";
    var installState = "Keine Daten";

    if (networkData && networkData.hostname) {
      hostname = networkData.hostname;
    } else if (statusData && statusData.hostname) {
      hostname = statusData.hostname;
    }

    if (networkData && Array.isArray(networkData.ips) && networkData.ips.length > 0) {
      networkState = "Online (" + networkData.ips.length + " IP)";
    } else if (statusData && statusData.network && Array.isArray(statusData.network.ips) && statusData.network.ips.length > 0) {
      networkState = "Online (" + statusData.network.ips.length + " IP)";
    } else if (statusData && statusData.network) {
      networkState = "Erreichbar";
    }

    if (statusData && statusData.status) {
      installState = statusData.status;
    }

    var ramText = "-";
    if (memory && Number.isFinite(memory.available) && Number.isFinite(memory.total)) {
      ramText = formatBytes(memory.available) + " frei von " + formatBytes(memory.total);
    }

    var diskText = "-";
    if (disk && Number.isFinite(disk.used) && Number.isFinite(disk.total)) {
      diskText = formatBytes(disk.used) + " genutzt von " + formatBytes(disk.total);
    }

    setText(cpuEl, cpuUsage);
    setText(ramEl, ramText);
    setText(diskEl, diskText);
    setText(hostEl, hostname);
    setText(osEl, osName);
    setText(networkEl, networkState);
    setText(uptimeEl, uptime);
    setText(installEl, installState);
    setText(lastEl, new Date().toLocaleTimeString());
  }

  function tick() {
    setConnectionState("Ladezustand");
    probeHealthy()
      .then(function (baseUrl) {
        setConnectionState("Backend verbunden");
        return Promise.allSettled([
          loadSystem(baseUrl),
          loadStatus(baseUrl),
          loadNetwork(baseUrl)
        ]).then(function (results) {
            var systemData = results[0].status === "fulfilled" ? results[0].value : null;
            var statusData = results[1].status === "fulfilled" ? results[1].value : null;
            var networkData = results[2].status === "fulfilled" ? results[2].value : null;
            if (!systemData && !statusData && !networkData) {
              throw new Error("no-data");
            }
            updateMetrics(systemData || {}, statusData || {}, networkData || {});
            setConnectionState("Setuphelfer laeuft lokal");
        });
      })
      .catch(function () {
        clearMetrics();
        setConnectionState("Backend nicht erreichbar");
      });
  }

  tick();
  pollTimer = window.setInterval(tick, pollMs);
  window.addEventListener("beforeunload", function () {
    if (pollTimer) window.clearInterval(pollTimer);
  });
})();
