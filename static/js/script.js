/* ==========================
   COMPLETE SCRIPT.JS
   All functionality in one file (No icons in theme button)
========================== */

/* ==========================
   INIT (RUN AFTER LOAD)
========================== */
document.addEventListener("DOMContentLoaded", () => {

  initMenu();
  initTheme();
  initSearch();
  initMap();
  initBudget();
  initToasts();
  initMobileNav();
  initSidebarActive();
  initMoreMenu();
  
  // Initialize Lucide icons
  if (typeof lucide !== 'undefined') {
    lucide.createIcons();
  }

});


/* ==========================
   MORE MENU FOR BOTTOM NAV
========================== */
function initMoreMenu() {
  const moreBtn = document.getElementById('moreMenuBtn');
  const moreMenu = document.getElementById('moreMenu');
  
  if (moreBtn && moreMenu) {
    moreBtn.removeEventListener('click', moreBtn.clickHandler);
    
    moreBtn.clickHandler = function(e) {
      e.stopPropagation();
      e.preventDefault();
      moreMenu.classList.toggle('active');
    };
    
    moreBtn.addEventListener('click', moreBtn.clickHandler);
    
    document.addEventListener('click', function(e) {
      if (moreMenu.classList.contains('active')) {
        if (!moreBtn.contains(e.target) && !moreMenu.contains(e.target)) {
          moreMenu.classList.remove('active');
        }
      }
    });
  }
}


/* ==========================
   MOBILE MENU
========================== */
function initMenu() {
  const toggle = document.getElementById("menuToggle");
  const nav = document.getElementById("navLinks");

  if (toggle && nav) {
    toggle.addEventListener("click", () => {
      nav.classList.toggle("active");
    });
  }
}


/* ==========================
   THEME TOGGLE (Simple text - No icons)
========================== */
function initTheme() {
  const toggle = document.getElementById("theme-toggle");
  const root = document.documentElement;

  if (!toggle) return;

  // Check saved theme
  const saved = localStorage.getItem("theme");
  
  if (saved === "dark") {
    root.classList.add("dark-mode");
    updateThemeText(true);
  } else {
    root.classList.remove("dark-mode");
    updateThemeText(false);
  }

  toggle.removeEventListener('click', toggle.clickHandler);
  
  toggle.clickHandler = function() {
    const isDark = root.classList.contains("dark-mode");
    
    if (isDark) {
      root.classList.remove("dark-mode");
      localStorage.setItem("theme", "light");
      updateThemeText(false);
    } else {
      root.classList.add("dark-mode");
      localStorage.setItem("theme", "dark");
      updateThemeText(true);
    }
  };
  
  toggle.addEventListener('click', toggle.clickHandler);
}

function updateThemeText(isDark) {
  const themeText = document.getElementById("theme-text");
  if (themeText) {
    themeText.textContent = isDark ? "Light Mode" : "Dark Mode";
  }
}


/* ==========================
   DESTINATION SEARCH
========================== */
function initSearch() {
  const input = document.getElementById("searchInput");

  if (input) {
    input.addEventListener("keyup", () => {
      const filter = input.value.toLowerCase();
      const cards = document.querySelectorAll(".destination-card");

      cards.forEach(card => {
        const text = card.innerText.toLowerCase();
        card.style.display = text.includes(filter) ? "block" : "none";
      });
    });
  }
}


/* ==========================
   MAP + SEARCH + WEATHER
========================== */
let map;
let currentMarker = null;

function initMap() {
  const mapEl = document.getElementById("map");
  if (!mapEl) return;

  if (typeof L === 'undefined') {
    console.log("Leaflet not loaded, waiting...");
    setTimeout(initMap, 500);
    return;
  }

  try {
    if (!map) {
      map = L.map('map').setView([20.5937, 78.9629], 5);

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
      }).addTo(map);
      
      console.log("Map initialized");
    }

    const searchBtn = document.getElementById("search-btn");
    const locationInput = document.getElementById("location-input");

    if (searchBtn && locationInput) {
      const newSearchBtn = searchBtn.cloneNode(true);
      searchBtn.parentNode.replaceChild(newSearchBtn, searchBtn);
      
      newSearchBtn.addEventListener("click", async () => {
        const location = locationInput.value.trim();
        if (!location) {
          alert("Please enter a location");
          return;
        }

        try {
          newSearchBtn.innerHTML = 'Loading...';
          newSearchBtn.disabled = true;
          
          const res = await fetch(
            `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(location)}&limit=1`
          );
          const data = await res.json();

          if (!data || data.length === 0) {
            alert("Location not found");
            return;
          }

          const lat = parseFloat(data[0].lat);
          const lon = parseFloat(data[0].lon);

          if (currentMarker) {
            map.removeLayer(currentMarker);
          }

          map.setView([lat, lon], 12);
          currentMarker = L.marker([lat, lon]).addTo(map)
            .bindPopup(`<b>${location}</b>`)
            .openPopup();

          loadWeather(lat, lon);

        } catch (err) {
          console.error(err);
          alert("Error fetching location");
        } finally {
          newSearchBtn.innerHTML = 'Search';
          newSearchBtn.disabled = false;
        }
      });
    }
  } catch (error) {
    console.error("Map error:", error);
  }
}


/* ==========================
   WEATHER
========================== */
async function loadWeather(lat, lon) {
  try {
    const res = await fetch(`/weather?lat=${lat}&lon=${lon}`);
    const data = await res.json();

    if (!data || data.cod != 200) return;

    const weatherCity = document.getElementById("weather-city");
    const weatherTemp = document.getElementById("weather-temp");
    const weatherDesc = document.getElementById("weather-desc");
    const weatherBox = document.getElementById("weather-box");

    if (weatherCity) weatherCity.textContent = data.name;
    if (weatherTemp) weatherTemp.textContent = `🌡️ ${data.main.temp}°C`;
    if (weatherDesc) weatherDesc.textContent = data.weather[0].description;
    if (weatherBox) weatherBox.classList.remove("hidden");

  } catch (err) {
    console.error("Weather error:", err);
  }
}


/* ==========================
   BUDGET CALCULATOR
========================== */
function initBudget() {
  const fields = ["hotel", "flight", "food", "transport"];

  fields.forEach(id => {
    const element = document.getElementById(id);
    if (element) {
      element.addEventListener("input", calculateBudget);
    }
  });
}

function calculateBudget() {
  const get = id => parseFloat(document.getElementById(id)?.value) || 0;
  const total = get("hotel") + get("flight") + get("food") + get("transport");
  const output = document.getElementById("totalBudget");
  if (output) output.value = total;
}


/* ==========================
   TOAST AUTO DISMISS
========================== */
function initToasts() {
  setTimeout(() => {
    document.querySelectorAll(".toast").forEach(t => {
      t.style.opacity = "0";
      setTimeout(() => {
        if (t && t.parentNode) t.remove();
      }, 500);
    });
  }, 4000);
}


/* ==========================
   MOBILE BOTTOM NAVIGATION
========================== */
function initMobileNav() {
  const currentPath = window.location.pathname;
  const bottomNavItems = document.querySelectorAll('.bottom-nav-item:not(.more-btn)');
  
  bottomNavItems.forEach(item => {
    item.classList.remove('active');
  });
  
  bottomNavItems.forEach(item => {
    const href = item.getAttribute('href');
    if (href) {
      if (currentPath === href) {
        item.classList.add('active');
      }
      if (href === '/' || href === '/home') {
        if (currentPath === '/' || currentPath === '/home') {
          item.classList.add('active');
        }
      }
    }
  });
}


/* ==========================
   SIDEBAR ACTIVE STATE
========================== */
function initSidebarActive() {
  const currentPath = window.location.pathname;
  const sidebarItems = document.querySelectorAll('.sidebar .nav-item');
  
  sidebarItems.forEach(item => {
    item.classList.remove('active');
  });
  
  sidebarItems.forEach(item => {
    const href = item.getAttribute('href');
    if (href) {
      if (currentPath === href) {
        item.classList.add('active');
      }
      if (href === '/' || href === '/home') {
        if (currentPath === '/' || currentPath === '/home') {
          item.classList.add('active');
        }
      }
    }
  });
}


/* ==========================
   RESIZE HANDLER (Fix map)
========================== */
let resizeTimer;

window.addEventListener('resize', function() {
  if (resizeTimer) clearTimeout(resizeTimer);
  
  resizeTimer = setTimeout(function() {
    if (map && typeof map.invalidateSize === 'function') {
      map.invalidateSize();
    }
  }, 250);
});


/* ==========================
   RETRY MAP INITIALIZATION
========================== */
setTimeout(function() {
  if (!map && document.getElementById('map')) {
    initMap();
  }
}, 1000);