// Drishyamitra AI - Command Center Front-End Logic

let token = localStorage.getItem("drishyamitra_token");
let username = localStorage.getItem("drishyamitra_username");

// DOM Cache
const authScreen = document.getElementById("auth-screen");
const appDashboard = document.getElementById("app-dashboard");
const loginForm = document.getElementById("login-form");
const loginError = document.getElementById("login-error");
const logoutBtn = document.getElementById("logout-btn");

// Navigation Items & View Sections
const navItems = document.querySelectorAll(".nav-item");
const views = document.querySelectorAll(".view-section");

// Metrics
const metricTotalPhotos = document.getElementById("metric-total-photos");
const metricTotalPeople = document.getElementById("metric-total-people");
const metricSharedDeliveries = document.getElementById("metric-shared-deliveries");
const metricUntaggedFaces = document.getElementById("metric-untagged-faces");
const metricEmails = document.getElementById("metric-emails");
const metricWhatsapp = document.getElementById("metric-whatsapp");

// Top Search
const topSearch = document.getElementById("top-search");

// Gallery & Filters
const galleryGrid = document.getElementById("gallery-grid");
const filterPerson = document.getElementById("filter-person");
const filterDate = document.getElementById("filter-date");
const clearFiltersBtn = document.getElementById("clear-filters-btn");

// Uploader
const uploadZone = document.getElementById("upload-zone");
const fileInput = document.getElementById("file-input");
const progressContainer = document.getElementById("upload-progress-container");
const progressFill = document.getElementById("upload-progress-fill");
const statusText = document.getElementById("upload-status-text");

// Contacts
const contactForm = document.getElementById("contact-form");
const contactsList = document.getElementById("contacts-list");
const clustersList = document.getElementById("clusters-list");
const btnRunClustering = document.getElementById("btn-run-clustering");
const btnOrganizePhotos = document.getElementById("btn-organize-photos");
const faceSearchBtn = document.getElementById("face-search-btn");
const faceSearchFile = document.getElementById("face-search-file");
const faceMatchStatus = document.getElementById("face-match-status");
const clearFaceSearchBtn = document.getElementById("clear-face-search-btn");


// Chat Agent
const chatThread = document.getElementById("chat-thread");
const chatInput = document.getElementById("chat-input");
const chatSendBtn = document.getElementById("chat-send-btn");
const logsContainer = document.getElementById("agent-logs-container");
const logsTerminal = document.getElementById("logs-terminal");

// Modals
const labelModal = document.getElementById("label-modal");
const modalFaceId = document.getElementById("modal-face-id");
const modalLabelInput = document.getElementById("modal-label-input");
const closeModalBtn = document.getElementById("close-modal-btn");
const submitLabelBtn = document.getElementById("submit-label-btn");

const analyticsModal = document.getElementById("analytics-modal");
const closeAnalyticsBtn = document.getElementById("close-analytics-btn");
const storageDetailsBtn = document.getElementById("storage-details-btn");

// Initialize Screen State
updateScreenVisibility();

function updateScreenVisibility() {
  if (token) {
    authScreen.style.display = "none";
    appDashboard.style.display = "grid";
    initializeDashboard();
  } else {
    authScreen.style.display = "flex";
    appDashboard.style.display = "none";
  }
}

// ----------------- AUTHENTICATION -----------------
let authMode = "login";
const authTitle = document.getElementById("auth-title");
const authSubmitBtn = document.getElementById("auth-submit-btn");
const loginSuccess = document.getElementById("login-success");
const authToggleMsg = document.getElementById("auth-toggle-msg");
const authToggleLink = document.getElementById("auth-toggle-link");

if (authToggleLink) {
  authToggleLink.addEventListener("click", (e) => {
    e.preventDefault();
    loginError.style.display = "none";
    loginSuccess.style.display = "none";
    
    if (authMode === "login") {
      authMode = "register";
      authTitle.innerText = "AI Photo Command Center Register";
      authSubmitBtn.innerText = "Register";
      authToggleMsg.innerText = "Already have an account?";
      authToggleLink.innerText = "Sign In";
    } else {
      authMode = "login";
      authTitle.innerText = "AI Photo Command Center Login";
      authSubmitBtn.innerText = "Sign In";
      authToggleMsg.innerText = "Don't have an account?";
      authToggleLink.innerText = "Register";
    }
  });
}

loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  loginError.style.display = "none";
  loginSuccess.style.display = "none";
  
  const user = document.getElementById("username").value.trim();
  const pass = document.getElementById("password").value.trim();
  
  try {
    const url = authMode === "login" ? "/api/auth/login" : "/api/auth/register";
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: user, password: pass })
    });
    
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || "Authentication failed");
    }
    
    if (authMode === "login") {
      token = data.token;
      username = data.username;
      localStorage.setItem("drishyamitra_token", token);
      localStorage.setItem("drishyamitra_username", username);
      updateScreenVisibility();
    } else {
      loginSuccess.innerText = data.message || "Registration successful! Please login.";
      loginSuccess.style.display = "block";
      
      // Reset input fields
      document.getElementById("username").value = "";
      document.getElementById("password").value = "";
      
      // Toggle back to login state
      authMode = "login";
      authTitle.innerText = "AI Photo Command Center Login";
      authSubmitBtn.innerText = "Sign In";
      authToggleMsg.innerText = "Don't have an account?";
      authToggleLink.innerText = "Register";
    }
  } catch (err) {
    loginError.innerText = err.message;
    loginError.style.display = "block";
  }
});

logoutBtn.addEventListener("click", () => {
  token = null;
  username = null;
  localStorage.removeItem("drishyamitra_token");
  localStorage.removeItem("drishyamitra_username");
  updateScreenVisibility();
});

// Helper for authenticated fetch API requests
async function authFetch(url, options = {}) {
  options.headers = options.headers || {};
  options.headers["Authorization"] = `Bearer ${token}`;
  
  const res = await fetch(url, options);
  if (res.status === 401) {
    // Session expired or invalid
    token = null;
    localStorage.removeItem("drishyamitra_token");
    updateScreenVisibility();
    return null;
  }
  return res;
}

// ----------------- TAB NAVIGATION LOGIC -----------------
navItems.forEach(item => {
  item.addEventListener("click", () => {
    const viewName = item.getAttribute("data-view");
    switchView(viewName);
  });
});

function switchView(viewName) {
  // Update nav active styles
  navItems.forEach(nav => {
    if (nav.getAttribute("data-view") === viewName) {
      nav.classList.add("active");
    } else {
      nav.classList.remove("active");
    }
  });

  // Switch view displays
  views.forEach(v => {
    if (v.id === `view-${viewName}`) {
      v.style.display = "flex";
    } else {
      v.style.display = "none";
    }
  });
  
  // Refresh contents dynamically on view change
  if (viewName === "photos") {
    fetchPhotos(filterPerson.value.trim(), filterDate.value);
  } else if (viewName === "people") {
    fetchContacts();
    fetchPeopleClusters();
  } else if (viewName === "share") {
    fetchHistory();
  } else if (viewName === "home") {
    fetchMetrics();
    // Cache smart album counts by retrieving all photos
    fetchAllPhotosForAlbums();
  }
}

// ----------------- DASHBOARD INITIALIZATION -----------------
function initializeDashboard() {
  switchView("home");
  fetchMetrics();
  fetchAllPhotosForAlbums();
  fetchContacts();
  fetchPeopleClusters();
  fetchHistory();
}


async function fetchMetrics() {
  const res = await authFetch("/api/dashboard/metrics");
  if (!res) return;
  const data = await res.json();
  
  if (metricTotalPhotos) metricTotalPhotos.innerText = data.total_photos;
  if (metricTotalPeople) metricTotalPeople.innerText = data.total_people;
  if (metricSharedDeliveries) metricSharedDeliveries.innerText = data.total_delivered;
  if (metricUntaggedFaces) metricUntaggedFaces.innerText = data.untagged_faces || 0;
  
  // Update hidden binds to prevent error
  if (metricEmails) metricEmails.innerText = data.emails_sent;
  if (metricWhatsapp) metricWhatsapp.innerText = data.whatsapp_deliveries;
}

// ----------------- PHOTO GALLERY & FACE LABELS -----------------
async function fetchPhotos(person = "", date = "") {
  let url = "/api/photos";
  const params = [];
  if (person) params.push(`person=${encodeURIComponent(person)}`);
  if (date) params.push(`date=${encodeURIComponent(date)}`);
  if (params.length > 0) url += "?" + params.join("&");
  
  const res = await authFetch(url);
  if (!res) return;
  const photos = await res.json();
  
  galleryGrid.innerHTML = "";
  if (photos.length === 0) {
    galleryGrid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--text-secondary); padding: 3rem;">No photos match the selected filters.</div>`;
    return;
  }
  
  photos.forEach(photo => {
    const card = document.createElement("div");
    card.className = "photo-card";
    
    // Draw photo layout and face overlays
    let facesHtml = "";
    photo.faces.forEach(face => {
      // Bounding box percentages coordinates overlay
      const labelText = `${face.label}${face.confidence && face.confidence < 1 ? ' (' + Math.round(face.confidence * 100) + '%)' : ''}`;
      facesHtml += `
        <div class="face-box" 
             style="left: calc(${face.x}% / 5.5); top: calc(${face.y}% / 4.5); width: calc(${face.w}% / 5.5); height: calc(${face.h}% / 4.5);"
             data-label="${labelText}"
             onclick="openLabelModal(${face.id}, '${face.label === 'Unknown' ? '' : face.label}')">
        </div>
      `;
    });
    
    card.innerHTML = `
      <div class="img-container">
        <button class="delete-photo-btn" onclick="deletePhoto(${photo.id})" title="Delete Photo">&times;</button>
        <img src="${photo.secure_url}" alt="${photo.original_filename}" loading="lazy">
        ${facesHtml}
      </div>
      <div class="photo-meta">
        <div class="photo-meta-title" title="${photo.original_filename}">${photo.original_filename}</div>
        <div style="font-size: 0.7rem; color: var(--text-muted); margin-top: 0.15rem;">Uploaded: ${photo.upload_date}</div>
        <div class="photo-labels-container">
          ${photo.faces.map(f => `<span class="face-tag">${f.label}${f.confidence && f.confidence < 1 ? ' (' + Math.round(f.confidence * 100) + '%)' : ''}</span>`).join("")}
        </div>
      </div>
    `;
    galleryGrid.appendChild(card);
  });
}

async function deletePhoto(photoId) {
  if (!confirm("Are you sure you want to delete this photo from Cloudinary and the database?")) return;
  
  const res = await authFetch(`/api/photos/${photoId}`, { method: "DELETE" });
  if (!res) return;
  
  fetchPhotos(filterPerson.value.trim(), filterDate.value);
  fetchMetrics();
}

// ----------------- DRAG & DROP PHOTO UPLOADER -----------------
uploadZone.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", () => {
  handleFilesUpload(fileInput.files);
});

uploadZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  uploadZone.classList.add("dragover");
});

uploadZone.addEventListener("dragleave", () => {
  uploadZone.classList.remove("dragover");
});

uploadZone.addEventListener("drop", (e) => {
  e.preventDefault();
  uploadZone.classList.remove("dragover");
  handleFilesUpload(e.dataTransfer.files);
});

async function handleFilesUpload(files) {
  if (files.length === 0) return;
  
  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append("photos", files[i]);
  }
  
  progressContainer.style.display = "block";
  progressFill.style.width = "20%";
  progressFill.style.backgroundColor = "var(--accent-blue)";
  statusText.innerText = `Uploading ${files.length} file(s) to Cloudinary...`;
  
  try {
    const res = await authFetch("/api/upload", {
      method: "POST",
      body: formData
    });
    
    if (!res) return;
    
    if (!res.ok) {
      let errMsg = "Upload failed";
      try {
        const data = await res.json();
        errMsg = data.error || errMsg;
      } catch (e) {
        try {
          const text = await res.text();
          if (text) errMsg = text.substring(0, 100);
        } catch (inner) {}
      }
      throw new Error(errMsg);
    }
    
    const data = await res.json();
    
    progressFill.style.width = "100%";
    statusText.innerText = "Upload and facial analysis completed successfully!";
    setTimeout(() => {
      progressContainer.style.display = "none";
    }, 2000);
    
    initializeDashboard();
  } catch (err) {
    statusText.innerText = `Error: ${err.message}`;
    progressFill.style.backgroundColor = "var(--color-error)";
  }
}

// ----------------- FILTER GALLERIES -----------------
let filterTimeout;
function debounceFilter() {
  clearTimeout(filterTimeout);
  filterTimeout = setTimeout(() => {
    fetchPhotos(filterPerson.value.trim(), filterDate.value);
  }, 400);
}

filterPerson.addEventListener("input", debounceFilter);
filterDate.addEventListener("change", debounceFilter);

clearFiltersBtn.addEventListener("click", () => {
  filterPerson.value = "";
  filterDate.value = "";
  fetchPhotos();
});

// ----------------- TOP BAR SEARCH FILTER ROUTING -----------------
if (topSearch) {
  topSearch.addEventListener("input", (e) => {
    const val = e.target.value.trim();
    if (val) {
      // Sync with gallery search input
      filterPerson.value = val;
      // Switch view to photos
      if (document.getElementById("view-photos").style.display === "none") {
        switchView("photos");
      }
      fetchPhotos(val, filterDate.value);
    }
  });
}

// ----------------- FACE LABELS MODAL -----------------
window.openLabelModal = function(faceId, currentLabel) {
  event.stopPropagation();
  
  modalFaceId.value = faceId;
  modalLabelInput.value = currentLabel;
  labelModal.style.display = "flex";
  modalLabelInput.focus();
};

closeModalBtn.addEventListener("click", () => {
  labelModal.style.display = "none";
});

submitLabelBtn.addEventListener("click", async () => {
  const faceId = modalFaceId.value;
  const label = modalLabelInput.value.trim();
  
  if (!label) return;
  
  const res = await authFetch(`/api/faces/${faceId}/label`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ label })
  });
  
  if (!res) return;
  const data = await res.json();
  
  labelModal.style.display = "none";
  alert(`Face labeled as '${label}'. Auto-recognizer mapped ${data.propagated_count} other faces!`);
  
  initializeDashboard();
});

// ----------------- CONTACT MANAGEMENT -----------------
contactForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  
  const name = document.getElementById("contact-name").value.trim();
  const email = document.getElementById("contact-email").value.trim();
  const wa = document.getElementById("contact-whatsapp").value.trim();
  
  const res = await authFetch("/api/contacts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email, whatsapp_number: wa })
  });
  
  if (!res) return;
  
  contactForm.reset();
  fetchContacts();
  fetchMetrics();
});

async function fetchContacts() {
  const res = await authFetch("/api/contacts");
  if (!res) return;
  const contacts = await res.json();
  
  contactsList.innerHTML = "";
  if (contacts.length === 0) {
    contactsList.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 1.5rem;">No contacts saved yet.</div>`;
    return;
  }
  
  contacts.forEach(c => {
    const item = document.createElement("div");
    item.className = "contact-item";
    item.innerHTML = `
      <div class="contact-name">${c.name}</div>
      <div class="contact-details">✉️ ${c.email || 'N/A'}</div>
      <div class="contact-details">💬 ${c.whatsapp_number || 'N/A'}</div>
    `;
    contactsList.appendChild(item);
  });
}

// ----------------- DELIVERY HISTORY -----------------
async function fetchHistory() {
  const res = await authFetch("/api/delivery/history");
  if (!res) return;
  const history = await res.json();
  
  const tbody = document.getElementById("delivery-history-rows");
  tbody.innerHTML = "";
  
  if (history.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-secondary);">No deliveries recorded yet.</td></tr>`;
    return;
  }
  
  history.forEach(row => {
    const tr = document.createElement("tr");
    const photoIds = JSON.parse(row.photo_ids || "[]");
    
    tr.innerHTML = `
      <td style="white-space: nowrap; color: var(--text-secondary);">${row.timestamp}</td>
      <td style="text-transform: uppercase; font-family: monospace; font-size: 0.75rem; font-weight: 600; color: var(--accent-purple);">${row.delivery_method}</td>
      <td>${row.recipient}</td>
      <td>${photoIds.length} photo(s)</td>
      <td><span class="status-badge ${row.status}">${row.status.toUpperCase()}</span></td>
      <td style="font-size: 0.78rem; color: var(--text-secondary);">${row.details}</td>
    `;
    tbody.appendChild(tr);
  });
}

// ----------------- AI CHAT BOT state machine -----------------
chatSendBtn.addEventListener("click", sendChatMessage);
chatInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") sendChatMessage();
});

async function sendChatMessage() {
  const text = chatInput.value.trim();
  if (!text) return;
  
  appendChatBubble(text, "user");
  chatInput.value = "";
  
  try {
    const res = await authFetch("/api/agent", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: text })
    });
    
    if (!res) return;
    const data = await res.json();
    
    appendChatBubble(data.reply, "agent", data.photos);
    
    if (data.logs && data.logs.length > 0) {
      logsContainer.style.display = "block";
      logsTerminal.innerHTML = data.logs.map(log => `<div>> ${log}</div>`).join("");
      logsTerminal.scrollTop = logsTerminal.scrollHeight;
    }
    
    if (data.action_type === "delivery_success") {
      initializeDashboard();
    }
  } catch (err) {
    appendChatBubble(`Error: ${err.message}`, "agent");
  }
}

function appendChatBubble(message, sender, photos = []) {
  const bubble = document.createElement("div");
  bubble.className = `chat-msg ${sender}`;
  
  let html = `<div style="white-space: pre-wrap;">${escapeHtml(message)}</div>`;
  
  if (photos && photos.length > 0) {
    html += `
      <div style="display: flex; gap: 0.35rem; margin-top: 0.5rem; overflow-x: auto; padding-bottom: 0.25rem;">
        ${photos.map(p => `
          <img src="${p.secure_url}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 6px; border: 1px solid var(--border-color);" alt="Thumbnail">
        `).join("")}
      </div>
    `;
  }
  
  bubble.innerHTML = html;
  chatThread.appendChild(bubble);
  chatThread.scrollTop = chatThread.scrollHeight;
}

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// ----------------- SMART ALBUMS & ALUM CLICKS -----------------
async function fetchAllPhotosForAlbums() {
  const res = await authFetch("/api/photos");
  if (!res) return;
  const photos = await res.json();
  
  let birthdays = 0;
  let events = 0;
  let trips = 0;
  let festivals = 0;
  let weddings = 0;

  photos.forEach(photo => {
    const text = (photo.original_filename + " " + (photo.recognized_person || "") + " " + (photo.labels || []).join(" ")).toLowerCase();
    if (text.includes("birthday") || text.includes("cake") || text.includes("bday")) birthdays++;
    if (text.includes("event") || text.includes("party") || text.includes("gathering")) events++;
    if (text.includes("trip") || text.includes("travel") || text.includes("vacation") || text.includes("tour") || text.includes("manali")) trips++;
    if (text.includes("diwali") || text.includes("festival") || text.includes("holi") || text.includes("eid") || text.includes("diya")) festivals++;
    if (text.includes("wedding") || text.includes("marriage") || text.includes("bride") || text.includes("groom") || text.includes("shaadi") || text.includes("priya")) weddings++;
  });

  const albumTags = document.querySelectorAll(".album-tag");
  albumTags.forEach(tag => {
    const type = tag.getAttribute("data-search");
    const countSpan = tag.querySelector(".tag-count");
    if (countSpan) {
      if (type === "birthday") countSpan.innerText = birthdays;
      if (type === "event") countSpan.innerText = events;
      if (type === "trip") countSpan.innerText = trips;
      if (type === "diwali") countSpan.innerText = festivals;
      if (type === "wedding") countSpan.innerText = weddings;
    }
  });
}

// Bind Smart Album Clicks
document.querySelectorAll(".album-tag").forEach(tag => {
  tag.addEventListener("click", () => {
    const searchVal = tag.getAttribute("data-search");
    let filterTerm = "";
    if (searchVal === "birthday") filterTerm = "birthday";
    else if (searchVal === "event") filterTerm = "event";
    else if (searchVal === "trip") filterTerm = "trip";
    else if (searchVal === "diwali") filterTerm = "diwali";
    else if (searchVal === "wedding") filterTerm = "wedding";
    
    if (topSearch) topSearch.value = filterTerm;
    filterPerson.value = filterTerm;
    
    switchView("photos");
    fetchPhotos(filterTerm);
  });
});




// ----------------- QUICK ACTIONS BINDINGS -----------------
const qaUpload = document.getElementById("qa-upload");
const qaSearch = document.getElementById("qa-search");
const qaAsk = document.getElementById("qa-ask");
const qaAnalytics = document.getElementById("qa-analytics");

if (qaUpload) {
  qaUpload.addEventListener("click", () => {
    switchView("photos");
    // Trigger uploader click
    setTimeout(() => fileInput.click(), 100);
  });
}

if (qaSearch) {
  qaSearch.addEventListener("click", () => {
    switchView("photos");
    setTimeout(() => faceSearchFile.click(), 150);
  });
}

if (qaAsk) {
  qaAsk.addEventListener("click", () => {
    switchView("chat");
    setTimeout(() => chatInput.focus(), 100);
  });
}

if (qaAnalytics) {
  qaAnalytics.addEventListener("click", () => {
    analyticsModal.style.display = "flex";
  });
}

// ----------------- ANALYTICS INSIGHTS MODAL -----------------
if (closeAnalyticsBtn) {
  closeAnalyticsBtn.addEventListener("click", () => {
    analyticsModal.style.display = "none";
  });
}

if (storageDetailsBtn) {
  storageDetailsBtn.addEventListener("click", () => {
    analyticsModal.style.display = "flex";
  });
}




// ----------------- FACE CLUSTERING & CROP LOGIC -----------------
async function fetchPeopleClusters() {
  if (!clustersList) return;
  const res = await authFetch("/api/people/clusters");
  if (!res) return;
  const clusters = await res.json();
  
  clustersList.innerHTML = "";
  if (clusters.length === 0) {
    clustersList.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 1.5rem;">No face groups identified yet.</div>`;
    return;
  }
  
  clusters.forEach(c => {
    const card = document.createElement("div");
    card.className = "cluster-card";
    const confidenceText = c.avg_confidence && c.avg_confidence < 1 ? ` • ${Math.round(c.avg_confidence * 100)}% match` : '';
    card.innerHTML = `
      <div class="cluster-avatar">
        <img src="${c.secure_url}" alt="${c.label}">
      </div>
      <div class="cluster-name">${escapeHtml(c.label)}</div>
      <div class="cluster-count">${c.photo_count} photo(s)${confidenceText}</div>
    `;
    
    const img = card.querySelector("img");
    styleFaceAvatar(img, c.x, c.y, c.w, c.h);
    
    card.addEventListener("click", () => {
      // Filter main gallery by this person
      filterPerson.value = c.label;
      switchView("photos");
      fetchPhotos(c.label);
    });
    
    clustersList.appendChild(card);
  });
}

function styleFaceAvatar(img, x, y, w, h) {
  const applyStyles = () => {
    const naturalWidth = img.naturalWidth;
    if (naturalWidth && w) {
      img.style.width = `calc(100% * (${naturalWidth} / ${w}))`;
      img.style.left = `calc(-100% * (${x} / ${w}))`;
      img.style.top = `calc(-100% * (${y} / ${w}))`;
    }
  };
  if (img.complete) {
    applyStyles();
  } else {
    img.onload = applyStyles;
  }
}

// ----------------- FACE SEARCH ENGINE -----------------
if (faceSearchBtn && faceSearchFile) {
  faceSearchBtn.addEventListener("click", () => faceSearchFile.click());
  
  faceSearchFile.addEventListener("change", async () => {
    const file = faceSearchFile.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append("face_image", file);
    
    // Toggle loader styles on gallery
    galleryGrid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--text-secondary); padding: 3rem;">Scanning face embedding and searching matches...</div>`;
    
    try {
      const res = await authFetch("/api/search-by-face", {
        method: "POST",
        body: formData
      });
      
      if (!res) return;
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || "Search by face failed");
      }
      
      const matchingPhotos = await res.json();
      renderMatchingPhotos(matchingPhotos);
      
      if (faceMatchStatus) {
        faceMatchStatus.style.display = "flex";
      }
    } catch (err) {
      alert(`Error searching by face: ${err.message}`);
      fetchPhotos();
    } finally {
      faceSearchFile.value = ""; // Clear input file picker selection
    }
  });
}

if (clearFaceSearchBtn) {
  clearFaceSearchBtn.addEventListener("click", () => {
    if (faceMatchStatus) faceMatchStatus.style.display = "none";
    filterPerson.value = "";
    fetchPhotos();
  });
}

function renderMatchingPhotos(photos) {
  galleryGrid.innerHTML = "";
  if (photos.length === 0) {
    galleryGrid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--text-secondary); padding: 3rem;">No matching faces found in database (similarity distance threshold >= 0.40).</div>`;
    return;
  }
  
  photos.forEach(photo => {
    const card = document.createElement("div");
    card.className = "photo-card";
    
    let facesHtml = "";
    photo.faces.forEach(face => {
      const labelText = `${face.label}${face.confidence && face.confidence < 1 ? ' (' + Math.round(face.confidence * 100) + '%)' : ''}`;
      facesHtml += `
        <div class="face-box" 
             style="left: calc(${face.x}% / 5.5); top: calc(${face.y}% / 4.5); width: calc(${face.w}% / 5.5); height: calc(${face.h}% / 4.5);"
             data-label="${labelText}"
             onclick="openLabelModal(${face.id}, '${face.label === 'Unknown' ? '' : face.label}')">
        </div>
      `;
    });
    
    card.innerHTML = `
      <div class="img-container">
        <button class="delete-photo-btn" onclick="deletePhoto(${photo.id})" title="Delete Photo">&times;</button>
        <img src="${photo.secure_url}" alt="${photo.original_filename}" loading="lazy">
        ${facesHtml}
      </div>
      <div class="photo-meta">
        <div class="photo-meta-title" title="${photo.original_filename}">${photo.original_filename}</div>
        <div style="font-size: 0.7rem; color: var(--text-muted); margin-top: 0.15rem;">Uploaded: ${photo.upload_date}</div>
        <div class="photo-labels-container">
          ${photo.faces.map(f => `<span class="face-tag">${f.label}${f.confidence && f.confidence < 1 ? ' (' + Math.round(f.confidence * 100) + '%)' : ''}</span>`).join("")}
        </div>
      </div>
    `;
    galleryGrid.appendChild(card);
  });
}

// ----------------- FOLDER ORGANIZATION TRIGGER -----------------
if (btnOrganizePhotos) {
  btnOrganizePhotos.addEventListener("click", async () => {
    btnOrganizePhotos.disabled = true;
    const originalText = btnOrganizePhotos.innerText;
    btnOrganizePhotos.innerText = "Organizing...";
    
    try {
      const res = await authFetch("/api/organize-photos", {
        method: "POST"
      });
      if (!res) return;
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.error || "Organization failed");
      }
      
      let msg = `${data.message}\n\nFolders created:\n`;
      data.folders.forEach(f => {
        msg += `- organized_photos/${f}\n`;
      });
      alert(msg);
    } catch (err) {
      alert(`Error organizing photos: ${err.message}`);
    } finally {
      btnOrganizePhotos.disabled = false;
      btnOrganizePhotos.innerText = originalText;
    }
  });
}

// ----------------- DBSCAN CLUSTERING TRIGGER -----------------
if (btnRunClustering) {
  btnRunClustering.addEventListener("click", async () => {
    btnRunClustering.disabled = true;
    const originalText = btnRunClustering.innerText;
    btnRunClustering.innerText = "Clustering...";
    
    try {
      const res = await authFetch("/api/people/cluster-dbscan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ algorithm: "auto" })
      });
      if (!res) return;
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.error || "Clustering failed");
      }
      
      alert(data.message);
      initializeDashboard();
    } catch (err) {
      alert(`Error running clustering: ${err.message}`);
    } finally {
      btnRunClustering.disabled = false;
      btnRunClustering.innerText = originalText;
    }
  });
}

// ----------------- ACCURACY & MERGE/SPLIT WORKFLOWS -----------------
const btnShowEvaluation = document.getElementById("btn-show-evaluation");
const btnManageClusters = document.getElementById("btn-manage-clusters");
const evaluationModal = document.getElementById("evaluation-modal");
const closeEvaluationBtn = document.getElementById("close-evaluation-btn");
const containerEvaluationContent = document.getElementById("evaluation-content");

const mergeSplitModal = document.getElementById("merge-split-modal");
const closeMergeSplitBtn = document.getElementById("close-merge-split-btn");

const tabMergeBtn = document.getElementById("tab-merge-btn");
const tabSplitBtn = document.getElementById("tab-split-btn");
const sectionMergeCluster = document.getElementById("section-merge-cluster");
const sectionSplitCluster = document.getElementById("section-split-cluster");

const selectMergeSrc = document.getElementById("merge-src");
const selectMergeDest = document.getElementById("merge-dest");
const btnSubmitMerge = document.getElementById("submit-merge-btn");

const containerSplitCheckboxes = document.getElementById("split-faces-checkboxes");
const inputSplitNewName = document.getElementById("split-new-name");
const btnSubmitSplit = document.getElementById("submit-split-btn");

// 1. Evaluation Handler
if (btnShowEvaluation) {
  btnShowEvaluation.addEventListener("click", async () => {
    containerEvaluationContent.innerHTML = "<p>Retrieving clustering evaluation metrics from backend...</p>";
    evaluationModal.style.display = "flex";
    
    try {
      const res = await authFetch("/api/people/clustering-evaluation");
      if (!res) return;
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.error || "Evaluation failed");
      }
      
      if (data.silhouette_score === undefined) {
        containerEvaluationContent.innerHTML = `
          <div style="padding: 1rem; border-left: 4px solid var(--accent-blue); background: var(--bg-card);">
            <p><strong>Status:</strong> ${data.message}</p>
            <p>Please upload more faces and run clustering first to generate silhouette accuracy evaluation scores.</p>
          </div>
        `;
        return;
      }
      
      let clusterSizesHtml = "";
      for (const [name, size] of Object.entries(data.cluster_sizes)) {
        const cohesion = data.cluster_cohesions[name] !== undefined ? ` (Cohesion: ${Math.round(data.cluster_cohesions[name] * 100)}%)` : '';
        clusterSizesHtml += `<li><strong>${name}:</strong> ${size} face(s)${cohesion}</li>`;
      }
      
      containerEvaluationContent.innerHTML = `
        <div style="display: flex; flex-direction: column; gap: 0.75rem;">
          <p><strong>Total Classified Faces:</strong> ${data.total_faces}</p>
          <p><strong>Total Clusters Found:</strong> ${data.clusters_count}</p>
          <hr style="border: 0; border-top: 1px solid var(--border-color); margin: 0.25rem 0;">
          <p>💡 <strong>Silhouette Coefficient:</strong> <span style="font-weight: 700; color: var(--accent-blue);">${data.silhouette_score.toFixed(4)}</span></p>
          <p style="font-size: 0.78rem; color: var(--text-muted); margin-top: -0.5rem;">Values close to 1.0 indicate highly cohesive and well-separated face clusters. Values close to 0 indicate overlapping groups.</p>
          <p><strong>Davies-Bouldin Index:</strong> <span>${data.davies_bouldin_index.toFixed(4)}</span></p>
          <p><strong>Calinski-Harabasz Score:</strong> <span>${data.calinski_harabasz_index.toFixed(1)}</span></p>
          <hr style="border: 0; border-top: 1px solid var(--border-color); margin: 0.25rem 0;">
          <p><strong>Cluster Groups & Pairwise Cohesion:</strong></p>
          <ul style="padding-left: 1.25rem; font-size: 0.85rem; display: flex; flex-direction: column; gap: 0.25rem;">
            ${clusterSizesHtml}
          </ul>
        </div>
      `;
    } catch (err) {
      containerEvaluationContent.innerHTML = `<p style="color: var(--color-error);">Error: ${err.message}</p>`;
    }
  });
}

if (closeEvaluationBtn) {
  closeEvaluationBtn.addEventListener("click", () => {
    evaluationModal.style.display = "none";
  });
}

// 2. Manage Clusters Handler (Populates selects & split checkboxes)
if (btnManageClusters) {
  btnManageClusters.addEventListener("click", async () => {
    // Reset inputs
    inputSplitNewName.value = "";
    containerSplitCheckboxes.innerHTML = "<p>Loading face database...</p>";
    
    // Open modal
    mergeSplitModal.style.display = "flex";
    
    // Switch to default tab (Merge)
    switchManageTab("merge");
    
    // Fetch clusters
    const res = await authFetch("/api/people/clusters");
    if (!res) return;
    const clusters = await res.json();
    
    // Populate dropdowns
    selectMergeSrc.innerHTML = '<option value="">-- Select Source Cluster --</option>';
    selectMergeDest.innerHTML = '<option value="">-- Select Destination Cluster --</option>';
    
    clusters.forEach(c => {
      const optSrc = document.createElement("option");
      optSrc.value = c.label;
      optSrc.innerText = `${c.label} (${c.photo_count} photos)`;
      selectMergeSrc.appendChild(optSrc);
      
      const optDest = document.createElement("option");
      optDest.value = c.label;
      optDest.innerText = `${c.label} (${c.photo_count} photos)`;
      selectMergeDest.appendChild(optDest);
    });
    
    // Fetch all photos to get individual faces for split
    const resPhotos = await authFetch("/api/photos");
    if (!resPhotos) return;
    const photos = await resPhotos.json();
    
    containerSplitCheckboxes.innerHTML = "";
    let faceCounter = 0;
    photos.forEach(photo => {
      photo.faces.forEach(face => {
        if (face.label !== "Unknown") {
          faceCounter++;
          const labelWrapper = document.createElement("label");
          labelWrapper.style.display = "flex";
          labelWrapper.style.alignItems = "center";
          labelWrapper.style.gap = "0.4rem";
          labelWrapper.style.fontSize = "0.82rem";
          labelWrapper.innerHTML = `
            <input type="checkbox" name="split-face-check" value="${face.id}">
            <span>Face #${face.id} (${face.label}) in ${photo.original_filename}</span>
          `;
          containerSplitCheckboxes.appendChild(labelWrapper);
        }
      });
    });
    
    if (faceCounter === 0) {
      containerSplitCheckboxes.innerHTML = "<p style='font-size: 0.8rem; color: var(--text-muted);'>No labeled faces found in database to split.</p>";
    }
  });
}

function switchManageTab(tab) {
  if (tab === "merge") {
    tabMergeBtn.classList.add("active");
    tabSplitBtn.classList.remove("active");
    sectionMergeCluster.style.display = "block";
    sectionSplitCluster.style.display = "none";
  } else {
    tabSplitBtn.classList.add("active");
    tabMergeBtn.classList.remove("active");
    sectionSplitCluster.style.display = "block";
    sectionMergeCluster.style.display = "none";
  }
}

if (tabMergeBtn) tabMergeBtn.addEventListener("click", () => switchManageTab("merge"));
if (tabSplitBtn) tabSplitBtn.addEventListener("click", () => switchManageTab("split"));

if (closeMergeSplitBtn) {
  closeMergeSplitBtn.addEventListener("click", () => {
    mergeSplitModal.style.display = "none";
  });
}

// 3. Submit Merge
if (btnSubmitMerge) {
  btnSubmitMerge.addEventListener("click", async () => {
    const src = selectMergeSrc.value;
    const dest = selectMergeDest.value;
    
    if (!src || !dest) {
      alert("Please select both source and destination clusters.");
      return;
    }
    
    if (src === dest) {
      alert("Source and destination clusters must be different.");
      return;
    }
    
    if (!confirm(`Are you sure you want to merge '${src}' into '${dest}'? This updates all associated faces.`)) return;
    
    btnSubmitMerge.disabled = true;
    try {
      const res = await authFetch("/api/people/merge-clusters", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ src_label: src, dest_label: dest })
      });
      if (!res) return;
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.error || "Merge failed");
      }
      
      alert(data.message);
      mergeSplitModal.style.display = "none";
      initializeDashboard();
    } catch (err) {
      alert(`Error merging clusters: ${err.message}`);
    } finally {
      btnSubmitMerge.disabled = false;
    }
  });
}

// 4. Submit Split
if (btnSubmitSplit) {
  btnSubmitSplit.addEventListener("click", async () => {
    const checkedBoxes = document.querySelectorAll('input[name="split-face-check"]:checked');
    const faceIds = Array.from(checkedBoxes).map(cb => parseInt(cb.value));
    const newName = inputSplitNewName.value.trim();
    
    if (faceIds.length === 0) {
      alert("Please check at least one face to split.");
      return;
    }
    
    if (!newName) {
      alert("Please enter a new cluster label.");
      return;
    }
    
    btnSubmitSplit.disabled = true;
    try {
      const res = await authFetch("/api/people/split-cluster", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ face_ids: faceIds, new_label: newName })
      });
      if (!res) return;
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.error || "Split failed");
      }
      
      alert(data.message);
      mergeSplitModal.style.display = "none";
      initializeDashboard();
    } catch (err) {
      alert(`Error splitting faces: ${err.message}`);
    } finally {
      btnSubmitSplit.disabled = false;
    }
  });
}


