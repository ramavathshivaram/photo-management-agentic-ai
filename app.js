// Drishyamitra AI - Core Application Logic

// Current Local Time Context
const CURRENT_DATE = new Date("2026-06-09T09:34:28+05:30");

// Mock Contacts Database
const CONTACTS = {
  "mom": { name: "Mom", email: "mom.sharma@gmail.com", whatsapp: "+91 98765 43210", avatar: "assets/mom.png" },
  "rahul": { name: "Rahul", email: "rahul.dev@gmail.com", whatsapp: "+91 99887 76655", avatar: "assets/rahul.png" },
  "priya": { name: "Priya", email: "priya.sen@gmail.com", whatsapp: "+91 91234 56789", avatar: "assets/priya.png" },
  "dad": { name: "Dad", email: "dad.sharma@gmail.com", whatsapp: "+91 90000 11111", avatar: "assets/dad.png" }
};

// Mock Photos Database
// Includes tags, dates, events, and background gradient configuration for mock display
const PHOTOS = [
  {
    id: 1,
    person: "Priya",
    tags: ["Priya", "graduation", "celebration"],
    date: "2026-05-12", // last month
    event: "Graduation Ceremony",
    bgGradient: "linear-gradient(135deg, #4f46e5, #06b6d4)",
    avatar: "assets/priya.png"
  },
  {
    id: 2,
    person: "Priya",
    tags: ["Priya", "cafe", "food"],
    date: "2026-05-20", // last month
    event: "Weekend Cafe Outing",
    bgGradient: "linear-gradient(135deg, #f59e0b, #ec4899)",
    avatar: "assets/priya.png"
  },
  {
    id: 3,
    person: "Priya",
    tags: ["Priya", "park", "nature"],
    date: "2026-05-28", // last month
    event: "Evening Walk",
    bgGradient: "linear-gradient(135deg, #10b981, #3b82f6)",
    avatar: "assets/priya.png"
  },
  {
    id: 4,
    person: "Priya",
    tags: ["Priya", "trek", "mountains"],
    date: "2026-04-10",
    event: "Weekend Hill Trek",
    bgGradient: "linear-gradient(135deg, #06b6d4, #3b82f6)",
    avatar: "assets/priya.png"
  },
  {
    id: 5,
    person: "Mom",
    tags: ["Mom", "birthday", "cake"],
    date: "2025-06-15", // last year
    event: "Mom's 50th Birthday Party",
    bgGradient: "linear-gradient(135deg, #ec4899, #f43f5e)",
    avatar: "assets/mom.png"
  },
  {
    id: 6,
    person: "Mom",
    tags: ["Mom", "family", "dinner"],
    date: "2025-06-20", // last year
    event: "Anniversary Family Dinner",
    bgGradient: "linear-gradient(135deg, #f59e0b, #d97706)",
    avatar: "assets/mom.png"
  },
  {
    id: 7,
    person: "Rahul",
    tags: ["Rahul", "football", "sports"],
    date: "2026-03-05",
    event: "Inter-College Soccer Finals",
    bgGradient: "linear-gradient(135deg, #3b82f6, #1d4ed8)",
    avatar: "assets/rahul.png"
  },
  {
    id: 8,
    person: "Rahul",
    tags: ["Rahul", "hackathon", "coding"],
    date: "2026-02-14",
    event: "National AI Hackathon",
    bgGradient: "linear-gradient(135deg, #8b5cf6, #3b82f6)",
    avatar: "assets/rahul.png"
  },
  {
    id: 9,
    person: "Dad",
    tags: ["Dad", "retirement", "office"],
    date: "2025-09-10",
    event: "Dad's Retirement Gathering",
    bgGradient: "linear-gradient(135deg, #374151, #111827)",
    avatar: "assets/dad.png"
  }
];

// State variables for Orchestration
let isRunning = false;
let currentPlan = null;
let currentPhotos = [];
let pendingExecutionCallback = null;

// DOM Elements
const queryInput = document.getElementById("query-input");
const submitBtn = document.getElementById("submit-btn");
const terminal = document.getElementById("terminal");
const jsonOutput = document.getElementById("json-output");
const confirmationBanner = document.getElementById("confirmation-banner");
const confirmationMessage = document.getElementById("confirmation-message");
const confirmBtn = document.getElementById("confirm-btn");
const agentGlobalStatus = document.getElementById("agent-global-status");

// Output containers
const emptyOutputMessage = document.getElementById("empty-output-message");
const photoGalleryOutput = document.getElementById("photo-gallery-output");
const galleryGrid = document.getElementById("gallery-grid");
const emailDeliveryOutput = document.getElementById("email-delivery-output");
const emailPreviewCard = document.getElementById("email-preview-card");
const whatsappDeliveryOutput = document.getElementById("whatsapp-delivery-output");
const whatsappPreviewCard = document.getElementById("whatsapp-preview-card");
const folderStructureOutput = document.getElementById("folder-structure-output");
const folderView = document.getElementById("folder-view");
const faceIdentificationOutput = document.getElementById("face-identification-output");
const faceIdCard = document.getElementById("face-id-card");
const faceLabelingOutput = document.getElementById("face-labeling-output");
const faceLabelCard = document.getElementById("face-label-card");

// SVGs for Folder Mockup
const folderSvg = `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M10 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/></svg>`;
const fileSvg = `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/></svg>`;

// Initialize Tabs
document.querySelectorAll(".tab-btn").forEach(button => {
  button.addEventListener("click", () => {
    const parent = button.parentElement;
    
    // Check if it's Left panel tabs or Right output tabs
    if (button.dataset.tab) {
      // Left tabs (Terminal / JSON)
      parent.querySelectorAll(".tab-btn").forEach(btn => btn.classList.remove("active"));
      button.classList.add("active");
      
      document.getElementById("terminal-tab").classList.remove("active");
      document.getElementById("json-tab").classList.remove("active");
      document.getElementById(`${button.dataset.tab}-tab`).classList.add("active");
    } else if (button.dataset.outputTab) {
      // Right tabs (Results / History)
      parent.querySelectorAll(".tab-btn").forEach(btn => btn.classList.remove("active"));
      button.classList.add("active");
      
      document.getElementById("results-output-tab").classList.remove("active");
      document.getElementById("history-output-tab").classList.remove("active");
      document.getElementById(`${button.dataset.outputTab}-output-tab`).classList.add("active");
      
      if (button.dataset.outputTab === "history") {
        renderAuditHistory();
      }
    }
  });
});

// Setup Preset Card listeners
document.querySelectorAll(".preset-card").forEach(card => {
  card.addEventListener("click", () => {
    if (isRunning) return;
    queryInput.value = card.dataset.query;
    runOrchestrator();
  });
});

// Setup click search and submit
submitBtn.addEventListener("click", () => {
  runOrchestrator();
});

queryInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") {
    runOrchestrator();
  }
});

confirmBtn.addEventListener("click", () => {
  if (pendingExecutionCallback) {
    confirmationBanner.style.display = "none";
    const callback = pendingExecutionCallback;
    pendingExecutionCallback = null;
    callback();
  }
});

// Heuristics NLP Parser (Intent Agent)
function parseQuery(text) {
  const query = text.toLowerCase();
  let intent = "search_photos";
  let person = "";
  let event = "";
  let date_range = "";
  let delivery_method = "none";
  let requires_confirmation = false;
  let action_plan = [];

  // 1. Identify Person
  if (query.includes("priya")) person = "Priya";
  else if (query.includes("rahul")) person = "Rahul";
  else if (query.includes("mom")) person = "Mom";
  else if (query.includes("dad")) person = "Dad";

  // 2. Identify Event
  if (query.includes("birthday")) event = "Birthday";
  else if (query.includes("graduation")) event = "Graduation";
  else if (query.includes("vacation")) event = "Vacation";
  else if (query.includes("trek") || query.includes("hiking")) event = "Trek";
  else if (query.includes("dinner")) event = "Dinner";
  else if (query.includes("hackathon")) event = "Hackathon";

  // 3. Identify Date Range
  if (query.includes("last month")) {
    date_range = "May 2026"; // Current is June 2026
  } else if (query.includes("last year")) {
    date_range = "Year 2025";
  } else if (query.includes("yesterday")) {
    date_range = "2026-06-08";
  } else if (query.includes("recent") || query.includes("latest")) {
    date_range = "Recent 3 months";
  }

  // 4. Identify Intent and Delivery Method
  if (query.includes("identify") || query.includes("who is")) {
    intent = "identify_person";
    delivery_method = "none";
  } else if (query.includes("label") || query.includes("tag face")) {
    intent = "label_face";
    delivery_method = "none";
  } else if (query.includes("email") || query.includes("gmail") || query.includes("mail")) {
    intent = "send_email";
    delivery_method = "email";
    requires_confirmation = true;
  } else if (query.includes("whatsapp") || query.includes("send rahul's photos to whatsapp") || query.includes("text")) {
    intent = "send_whatsapp";
    delivery_method = "whatsapp";
    requires_confirmation = true;
  } else if (query.includes("organize") || query.includes("folder") || query.includes("create folder") || query.includes("group")) {
    intent = "organize_photos";
    delivery_method = "local_storage";
  } else if (query.includes("history") || query.includes("logs")) {
    intent = "show_history";
  }

  // 5. Generate action plan
  action_plan.push("Extract intent and entities");
  if (person) action_plan.push(`Verify person ID for '${person}'`);
  
  if (intent === "identify_person") {
    action_plan.push("Extract query face descriptor");
    action_plan.push("Scan face library for similarity match");
    action_plan.push("Return identified profile");
  } else if (intent === "label_face") {
    action_plan.push("Locate target face cluster cluster_id");
    action_plan.push("Map custom label to metadata store");
    action_plan.push("Update local facial index catalog");
  } else {
    action_plan.push("Retrieve matching photo entries");
    
    if (intent === "organize_photos") {
      action_plan.push(`Create file system folder structure for ${person || "Photos"}`);
      action_plan.push("Copy photos into target directories");
    } else if (intent === "send_email") {
      action_plan.push(`Locate email contact details for '${person || "Mom"}'`);
      action_plan.push("Draft email with attachments");
      action_plan.push("Deliver email securely via SMTP API");
    } else if (intent === "send_whatsapp") {
      action_plan.push(`Locate WhatsApp number for '${person || "Recipient"}'`);
      action_plan.push("Format media message payload");
      action_plan.push("Transmit via WhatsApp API");
    }
  }
  
  action_plan.push("Record transaction logs to audit store");

  return {
    intent,
    person,
    event,
    date_range,
    delivery_method,
    requires_confirmation,
    action_plan
  };
}

// Log message to terminal with timestamp
function appendLog(agentName, message, type = "agent") {
  const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  const line = document.createElement("div");
  line.className = "terminal-line";
  
  if (type === "system") {
    line.innerHTML = `<span class="terminal-line timestamp">[${timestamp}]</span> <span class="terminal-line system">${message}</span>`;
  } else {
    line.innerHTML = `<span class="terminal-line timestamp">[${timestamp}]</span> <span class="terminal-line agent">${agentName}:</span> ${message}`;
  }
  
  terminal.appendChild(line);
  terminal.scrollTop = terminal.scrollHeight;
}

// Visual Node State Updates
function updateNode(nodeId, state) {
  const node = document.getElementById(nodeId);
  if (!node) return;
  
  node.className = `agent-node ${nodeId === "node-coordinator" ? "coordinator" : ""} ${state}`;
}

// Visual Connection Line State Updates
function updateLine(lineId, state) {
  const line = document.getElementById(lineId);
  if (!line) return;
  
  line.className.baseVal = `flow-line ${state}`;
}

// Reset all agent graph nodes and lines
function resetAgentGraph() {
  const nodes = ["node-coordinator", "node-intent", "node-facerecog", "node-search", "node-org", "node-gmail", "node-whatsapp", "node-audit"];
  const lines = ["line-intent", "line-facerecog", "line-search", "line-org", "line-gmail", "line-whatsapp", "line-audit"];
  
  nodes.forEach(id => updateNode(id, "idle"));
  lines.forEach(id => updateLine(id, ""));
}

// Helper to delay execution (mimicking processing time)
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// Main Simulation Pipeline
async function runOrchestrator() {
  const query = queryInput.value.trim();
  if (!query) return;

  isRunning = true;
  submitBtn.disabled = true;
  queryInput.disabled = true;
  pendingExecutionCallback = null;
  
  // Clear displays
  terminal.innerHTML = "";
  confirmationBanner.style.display = "none";
  emptyOutputMessage.style.display = "none";
  photoGalleryOutput.style.display = "none";
  emailDeliveryOutput.style.display = "none";
  whatsappDeliveryOutput.style.display = "none";
  folderStructureOutput.style.display = "none";
  faceIdentificationOutput.style.display = "none";
  faceLabelingOutput.style.display = "none";
  
  resetAgentGraph();
  agentGlobalStatus.innerText = "Processing...";
  document.querySelector(".status-dot").style.backgroundColor = "var(--color-processing)";
  document.querySelector(".status-dot").style.boxShadow = "0 0 8px var(--color-processing)";

  appendLog("System", `Incoming user request: "${query}"`, "system");
  await delay(600);

  // STEP 1: Understand Request (Intent Agent)
  appendLog("Coordinator Agent", "Received query, initiating parsing pipeline.", "coordinator");
  updateNode("node-coordinator", "processing");
  updateNode("node-intent", "processing");
  updateLine("line-intent", "active");
  await delay(1200);

  currentPlan = parseQuery(query);
  jsonOutput.innerText = JSON.stringify(currentPlan, null, 2);
  appendLog("Intent Agent", `Completed extraction. Intent: ${currentPlan.intent}, Person: ${currentPlan.person || "None"}, Event: ${currentPlan.event || "None"}, Range: ${currentPlan.date_range || "None"}`, "intent");
  updateNode("node-intent", "success");
  updateLine("line-intent", "highlight-success");
  await delay(800);

  if (currentPlan.intent === "identify_person") {
    // Face Identification Flow
    appendLog("Coordinator Agent", "Calling Face Recognition Agent to identify target face cluster.", "coordinator");
    updateNode("node-facerecog", "processing");
    updateLine("line-facerecog", "active");
    await delay(1200);
    
    appendLog("Face Recognition Agent", "Extracting query facial landmark vector...", "facerecog");
    await delay(800);
    appendLog("Face Recognition Agent", "Comparing landmarks against reference database clusters...", "facerecog");
    await delay(1000);
    appendLog("Face Recognition Agent", "Match identified: 'Priya' (Similarity score: 98.4%, ID: FR_PRIYA_092)", "facerecog");
    updateNode("node-facerecog", "success");
    updateLine("line-facerecog", "highlight-success");
    await delay(800);

    appendLog("Coordinator Agent", "Delegating search queries to verify metadata history.", "coordinator");
    updateNode("node-search", "processing");
    updateLine("line-search", "active");
    await delay(1000);
    
    currentPhotos = PHOTOS.filter(p => p.person === "Priya");
    appendLog("Search Agent", "Found 4 associated media items under profile record 'Priya'.", "search");
    renderFaceIdentification();
    updateNode("node-search", "success");
    updateLine("line-search", "highlight-success");
    await delay(800);

    // Audit logs & finalize
    await runAuditLogsAndFinalize(true);
    return;
  }

  if (currentPlan.intent === "label_face") {
    // Face Labeling Flow
    appendLog("Coordinator Agent", "Delegating face label mapping to Face Recognition Agent.", "coordinator");
    updateNode("node-facerecog", "processing");
    updateLine("line-facerecog", "active");
    await delay(1200);
    
    appendLog("Face Recognition Agent", "Locating target cluster face_unk_042...", "facerecog");
    await delay(800);
    appendLog("Face Recognition Agent", "SUCCESS: Map 'face_unk_042' -> 'Rohan' added to dictionary.", "facerecog");
    updateNode("node-facerecog", "success");
    updateLine("line-facerecog", "highlight-success");
    await delay(800);

    appendLog("Coordinator Agent", "Instructing Organization Agent to update facial indices database.", "coordinator");
    updateNode("node-org", "processing");
    updateLine("line-org", "active");
    await delay(1000);
    
    renderFaceLabeling();
    appendLog("Organization Agent", "SUCCESS: Local facial indexing catalog synchronized with new tags.", "org");
    updateNode("node-org", "success");
    updateLine("line-org", "highlight-success");
    await delay(800);

    // Audit logs & finalize
    await runAuditLogsAndFinalize(true);
    return;
  }

  // STEP 2: Verify Entities (Face Recognition Agent)
  if (currentPlan.person) {
    appendLog("Coordinator Agent", `Delegating identity validation to Face Recognition Agent.`, "coordinator");
    updateNode("node-facerecog", "processing");
    updateLine("line-facerecog", "active");
    await delay(1200);
    
    // Check if the person exists in database
    const personExists = currentPlan.person.toLowerCase() in CONTACTS;
    if (!personExists) {
      appendLog("Face Recognition Agent", `ERROR: Person entity '${currentPlan.person}' could not be identified in current facial library.`, "error");
      updateNode("node-facerecog", "error");
      updateLine("line-facerecog", "highlight-error");
      finalizeExecution(false, `Face recognition lookup failed for '${currentPlan.person}'`);
      return;
    }
    
    appendLog("Face Recognition Agent", `SUCCESS: Target matches profile in system database. Person ID = FR_${currentPlan.person.toUpperCase()}_092`, "facerecog");
    updateNode("node-facerecog", "success");
    updateLine("line-facerecog", "highlight-success");
    await delay(800);
  }

  // STEP 3: Retrieve Photos (Search Agent)
  appendLog("Coordinator Agent", "Calling Search Agent to retrieve matching photo assets.", "coordinator");
  updateNode("node-search", "processing");
  updateLine("line-search", "active");
  await delay(1200);

  // Perform mock query filtering
  currentPhotos = filterPhotos(currentPlan.person, currentPlan.event, currentPlan.date_range);
  appendLog("Search Agent", `Found ${currentPhotos.length} photo(s) matching request.`, "search");
  
  if (currentPhotos.length === 0) {
    appendLog("Search Agent", "WARNING: Zero photos found matching query parameters.", "search");
  }
  
  renderPhotoGallery();
  updateNode("node-search", "success");
  updateLine("line-search", "highlight-success");
  await delay(800);

  // STEP 4: Organize Photos (Organization Agent)
  if (currentPlan.intent === "organize_photos") {
    appendLog("Coordinator Agent", "Calling Organization Agent to structure files.", "coordinator");
    updateNode("node-org", "processing");
    updateLine("line-org", "active");
    await delay(1200);
    
    renderFolderStructure();
    appendLog("Organization Agent", `Created target folder: /Output/${currentPlan.person || "Generic"}_Photos/`, "org");
    appendLog("Organization Agent", `Copied ${currentPhotos.length} file(s) into destination directory.`, "org");
    updateNode("node-org", "success");
    updateLine("line-org", "highlight-success");
    await delay(800);
  } else {
    // Basic pass for coordination visual
    appendLog("Coordinator Agent", "Staging visual resources in background environment.", "coordinator");
    updateNode("node-org", "processing");
    updateLine("line-org", "active");
    await delay(600);
    updateNode("node-org", "success");
    updateLine("line-org", "highlight-success");
    await delay(400);
  }

  // STEP 5: Delivery & Confirmations (Gmail / WhatsApp)
  if (currentPlan.delivery_method === "email") {
    if (currentPlan.requires_confirmation) {
      appendLog("Coordinator Agent", "Awaiting confirmation from user before email dispatch.", "coordinator");
      confirmationMessage.innerText = `Approve sending ${currentPhotos.length} photos of ${currentPlan.person || "Mom"} to ${CONTACTS[currentPlan.person.toLowerCase()]?.email || "mom.sharma@gmail.com"}?`;
      confirmationBanner.style.display = "flex";
      
      pendingExecutionCallback = async () => {
        appendLog("System", "User approved email dispatch.", "system");
        await runEmailDelivery();
      };
      
      // Pause runner execution. Wait for button click callback.
      return;
    } else {
      await runEmailDelivery();
    }
  } else if (currentPlan.delivery_method === "whatsapp") {
    if (currentPlan.requires_confirmation) {
      appendLog("Coordinator Agent", "Awaiting confirmation from user before WhatsApp dispatch.", "coordinator");
      confirmationMessage.innerText = `Approve sending ${currentPhotos.length} photos of ${currentPlan.person || "Rahul"} to WhatsApp contact ${CONTACTS[currentPlan.person.toLowerCase()]?.whatsapp || "+91 99887 76655"}?`;
      confirmationBanner.style.display = "flex";
      
      pendingExecutionCallback = async () => {
        appendLog("System", "User approved WhatsApp dispatch.", "system");
        await runWhatsAppDelivery();
      };
      
      return;
    } else {
      await runWhatsAppDelivery();
    }
  } else {
    // Standard photo display (no delivery)
    await runAuditLogsAndFinalize(true);
  }
}

// Run Email Delivery Flow
async function runEmailDelivery() {
  appendLog("Coordinator Agent", "Delegating dispatch to Gmail Agent.", "coordinator");
  updateNode("node-gmail", "processing");
  updateLine("line-gmail", "active");
  await delay(1200);

  const contact = CONTACTS[currentPlan.person.toLowerCase()] || { name: "Mom", email: "mom.sharma@gmail.com" };
  renderEmailPreview(contact);
  
  appendLog("Gmail Agent", `Drafting message with ${currentPhotos.length} attachments.`, "gmail");
  appendLog("Gmail Agent", `Connecting to Gmail API; transmitting message package to <${contact.email}>`, "gmail");
  await delay(1000);
  appendLog("Gmail Agent", `SUCCESS: Message sent successfully. ID: g_msg_${Math.floor(Math.random()*1000000)}`, "gmail");
  
  updateNode("node-gmail", "success");
  updateLine("line-gmail", "highlight-success");
  await delay(800);
  
  await runAuditLogsAndFinalize(true);
}

// Run WhatsApp Delivery Flow
async function runWhatsAppDelivery() {
  appendLog("Coordinator Agent", "Delegating dispatch to WhatsApp Agent.", "coordinator");
  updateNode("node-whatsapp", "processing");
  updateLine("line-whatsapp", "active");
  await delay(1200);

  const contact = CONTACTS[currentPlan.person.toLowerCase()] || { name: "Rahul", whatsapp: "+91 99887 76655" };
  renderWhatsAppPreview(contact);

  appendLog("WhatsApp Agent", `Structuring media payload for ${currentPhotos.length} image(s).`, "whatsapp");
  appendLog("WhatsApp Agent", `Sending media messages to ${contact.whatsapp} via WhatsApp API...`, "whatsapp");
  await delay(1000);
  appendLog("WhatsApp Agent", `SUCCESS: Message status = delivered (double green tick).`, "whatsapp");
  
  updateNode("node-whatsapp", "success");
  updateLine("line-whatsapp", "highlight-success");
  await delay(800);

  await runAuditLogsAndFinalize(true);
}

// Step 6: Log history with Audit Agent and finalize execution
async function runAuditLogsAndFinalize(success) {
  appendLog("Coordinator Agent", "Submitting final transaction logs to Audit Agent.", "coordinator");
  updateNode("node-audit", "processing");
  updateLine("line-audit", "active");
  await delay(1000);

  // Save to history list in localStorage
  saveToHistory(success);
  appendLog("Audit Agent", "Saved execution transaction history to local audit database.", "audit");
  
  updateNode("node-audit", "success");
  updateLine("line-audit", "highlight-success");
  await delay(600);

  finalizeExecution(success, success ? "All operations completed successfully." : "Execution aborted with issues.");
}

// Wrap up execution state
function finalizeExecution(success, message) {
  isRunning = false;
  submitBtn.disabled = false;
  queryInput.disabled = false;
  
  if (success) {
    updateNode("node-coordinator", "success");
    agentGlobalStatus.innerText = "Completed";
    document.querySelector(".status-dot").style.backgroundColor = "var(--color-success)";
    document.querySelector(".status-dot").style.boxShadow = "0 0 8px var(--color-success)";
    appendLog("Coordinator Agent", "Workflow completed. Standing by for next request.", "coordinator");
  } else {
    updateNode("node-coordinator", "error");
    agentGlobalStatus.innerText = "Error";
    document.querySelector(".status-dot").style.backgroundColor = "var(--color-error)";
    document.querySelector(".status-dot").style.boxShadow = "0 0 8px var(--color-error)";
    appendLog("Coordinator Agent", `Workflow failed: ${message}`, "coordinator");
  }
}

// Database query search filters
function filterPhotos(person, event, dateRange) {
  return PHOTOS.filter(photo => {
    // 1. Filter by Person
    if (person && photo.person.toLowerCase() !== person.toLowerCase()) return false;
    
    // 2. Filter by Event
    if (event && photo.event.toLowerCase().indexOf(event.toLowerCase()) === -1 && photo.tags.indexOf(event.toLowerCase()) === -1) return false;
    
    // 3. Filter by Date range
    if (dateRange) {
      const year = new Date(photo.date).getFullYear();
      const month = new Date(photo.date).getMonth() + 1; // 1-indexed
      
      if (dateRange.includes("2026") || dateRange.includes("May 2026")) {
        if (year !== 2026 || month !== 5) return false;
      } else if (dateRange.includes("2025") || dateRange.includes("Year 2025")) {
        if (year !== 2025) return false;
      }
    }
    
    return true;
  });
}

// Render Photos in Grid Gallery
function renderPhotoGallery() {
  galleryGrid.innerHTML = "";
  
  if (currentPhotos.length === 0) {
    galleryGrid.innerHTML = '<div class="empty-history" style="grid-column: 1/-1;">No photos match the search parameters.</div>';
  } else {
    currentPhotos.forEach(photo => {
      const card = document.createElement("div");
      card.className = "photo-card";
      card.innerHTML = `
        <div class="photo-img-wrapper" style="background: ${photo.bgGradient}; display: flex; align-items: center; justify-content: center; position: relative;">
          <!-- Simulated photo layout -->
          <div style="position: absolute; color: rgba(255,255,255,0.15); font-weight: 700; font-size: 2rem; text-transform: uppercase;">
            ${photo.tags[1] || "Photo"}
          </div>
          <img class="photo-img" src="${photo.avatar}" alt="${photo.person}" style="width: 70px; height: 70px; border-radius: 50%; border: 3px solid rgba(255,255,255,0.8); box-shadow: 0 4px 10px rgba(0,0,0,0.3); z-index: 2;">
        </div>
        <div class="photo-info">
          <div class="photo-event">${photo.event}</div>
          <div class="photo-tags">
            ${photo.tags.map(t => `<span class="tag-badge">${t}</span>`).join("")}
          </div>
          <div class="photo-date">${photo.date}</div>
        </div>
      `;
      galleryGrid.appendChild(card);
    });
  }
  
  photoGalleryOutput.style.display = "block";
}

// Render Email preview card
function renderEmailPreview(contact) {
  const fileNames = currentPhotos.map(p => `${p.person.toLowerCase()}_${p.tags[1]}_${p.id}.png`);
  
  emailPreviewCard.innerHTML = `
    <div class="email-header">
      <div class="email-meta">
        <div><strong>To:</strong> ${contact.name} &lt;${contact.email}&gt;</div>
        <div><strong>From:</strong> Drishyamitra AI Assistant &lt;assistant@drishyamitra.ai&gt;</div>
        <div class="email-subject">Subject: Your Photos: ${currentPlan.event || "Search Results"}</div>
      </div>
    </div>
    <div class="email-body">
      Hi ${contact.name},<br><br>
      Here are the photos you requested from my search assistant. I found ${currentPhotos.length} matching photos from the database.<br><br>
      Best regards,<br>
      Drishyamitra AI
    </div>
    <div class="email-attachments">
      ${fileNames.map(name => `
        <div class="attachment-badge">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M16.5 6v11.5c0 2.21-1.79 4-4 4s-4-1.79-4-4V5c0-1.38 1.12-2.5 2.5-2.5s2.5 1.12 2.5 2.5v10.5c0 .55-.45 1-1 1s-1-.45-1-1V6H10v9.5c0 1.38 1.12 2.5 2.5 2.5s2.5-1.12 2.5-2.5V5c0-2.21-1.79-4-4-4S7 2.79 7 5v12.5c0 3.31 2.69 6 6 6s6-2.69 6-6V6h-1.5z"/></svg>
          ${name}
        </div>
      `).join("")}
    </div>
  `;
  
  emailDeliveryOutput.style.display = "block";
}

// Render WhatsApp mockup chat
function renderWhatsAppPreview(contact) {
  const mainPhoto = currentPhotos[0] || { bgGradient: "linear-gradient(135deg, #4f46e5, #06b6d4)", avatar: "assets/rahul.png", tags: ["photo"] };
  const countLabel = currentPhotos.length > 1 ? ` (+${currentPhotos.length - 1} more files)` : "";
  
  whatsappPreviewCard.innerHTML = `
    <div class="wa-container">
      <div class="wa-header">
        <div class="wa-avatar">
          <img src="${contact.avatar || 'assets/rahul.png'}" alt="${contact.name}">
        </div>
        <div class="wa-contact-info">
          <span class="wa-contact-name">${contact.name}</span>
          <span class="wa-contact-status">online</span>
        </div>
      </div>
      <div class="wa-chat-body">
        <div class="wa-msg">
          <div class="wa-msg-media" style="background: ${mainPhoto.bgGradient}; display: flex; align-items: center; justify-content: center;">
            <img src="${mainPhoto.avatar}" alt="Shared Media" style="width: 48px; height: 48px; border-radius: 50%; border: 2px solid white; box-shadow: 0 4px 8px rgba(0,0,0,0.3);">
          </div>
          <div class="wa-msg-text">Here are your photos from ${currentPlan.event || "the database"}${countLabel}! Sent via Drishyamitra AI.</div>
          <div class="wa-msg-time">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
        </div>
      </div>
    </div>
  `;
  
  whatsappDeliveryOutput.style.display = "block";
}

// Render Folder layout list
function renderFolderStructure() {
  const personName = currentPlan.person || "Staged";
  
  folderView.innerHTML = `
    <div class="folder-item">
      ${folderSvg}
      <span>Root/</span>
    </div>
    <div class="folder-item sub">
      ${folderSvg}
      <span>Output/</span>
    </div>
    <div class="folder-item sub" style="margin-left: 3rem;">
      ${folderSvg}
      <span style="color: #fbbf24; font-weight: 600;">${personName}_Photos/</span>
    </div>
    ${currentPhotos.map(p => `
      <div class="folder-item sub file" style="margin-left: 4.5rem;">
        ${fileSvg}
        <span>${p.person.toLowerCase()}_${p.tags[1]}_${p.id}.png</span>
      </div>
    `).join("")}
  `;
  
  folderStructureOutput.style.display = "block";
}

// Render Face Identification Result
function renderFaceIdentification() {
  faceIdCard.innerHTML = `
    <div style="display: flex; gap: 1.5rem; align-items: center;">
      <div style="position: relative; width: 100px; height: 100px; border: 2px solid var(--color-success); border-radius: 8px; overflow: hidden; background: linear-gradient(135deg, #4f46e5, #06b6d4);">
        <!-- Scanning Box Overlay -->
        <div style="position: absolute; top: 0; left: 0; right: 0; height: 2px; background: var(--color-success); box-shadow: 0 0 8px var(--color-success); animation: scanLine 2s linear infinite;"></div>
        <img src="assets/priya.png" alt="Identified Face" style="width: 100%; height: 100%; object-fit: cover;">
      </div>
      <div style="flex: 1; display: flex; flex-direction: column; gap: 0.35rem;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span style="font-size: 1.1rem; font-weight: 600; color: var(--color-success);">Priya Detected</span>
          <span style="font-size: 0.75rem; background: rgba(16, 185, 129, 0.15); color: var(--color-success); padding: 0.15rem 0.4rem; border-radius: 4px; font-weight: 600;">98.4% Match</span>
        </div>
        <div style="font-size: 0.8rem; color: var(--text-secondary);">
          <strong>Person ID:</strong> FR_PRIYA_092<br>
          <strong>Facial Signature:</strong> Vector[128] matched<br>
          <strong>Database Status:</strong> Profile verified
        </div>
      </div>
    </div>
    <!-- CSS for Scanning animation inline if not in styles.css -->
    <style>
      @keyframes scanLine {
        0% { top: 0; }
        50% { top: 100%; }
        100% { top: 0; }
      }
    </style>
  `;
  faceIdentificationOutput.style.display = "block";
}

// Render Face Labeling database update
function renderFaceLabeling() {
  faceLabelCard.innerHTML = `
    <div style="display: flex; gap: 1rem; flex-direction: column;">
      <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem;">
        <span style="font-weight: 600; color: var(--accent-blue);">Face Mapper Pipeline</span>
        <span class="history-status-badge success">INDEXED</span>
      </div>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; font-size: 0.8rem;">
        <div>
          <span style="color: var(--text-muted);">Cluster ID</span>
          <div style="font-family: var(--font-mono); margin-top: 0.1rem;">face_unk_042</div>
        </div>
        <div>
          <span style="color: var(--text-muted);">Custom Tag Assigned</span>
          <div style="font-weight: 600; color: var(--text-primary); margin-top: 0.1rem;">Rohan</div>
        </div>
      </div>
      <div style="font-size: 0.75rem; color: var(--text-secondary); background: rgba(255, 255, 255, 0.02); padding: 0.5rem; border-radius: 6px; border: 1px solid var(--border-color);">
        <strong>Audit Detail:</strong> Face recognition database updated. Local database synchronized with target folder map. Tag index 'Rohan' initialized for cluster lookup.
      </div>
    </div>
  `;
  faceLabelingOutput.style.display = "block";
}

// Local Storage History Management
function saveToHistory(success) {
  const history = JSON.parse(localStorage.getItem("drishyamitra_history") || "[]");
  const record = {
    timestamp: new Date().toISOString(),
    query: queryInput.value,
    intent: currentPlan.intent,
    person: currentPlan.person || "N/A",
    status: success ? "success" : "error",
    count: currentPhotos.length
  };
  
  history.unshift(record);
  localStorage.setItem("drishyamitra_history", JSON.stringify(history.slice(0, 20))); // Limit to 20
}

function renderAuditHistory() {
  const container = document.getElementById("history-table-container");
  const history = JSON.parse(localStorage.getItem("drishyamitra_history") || "[]");
  
  if (history.length === 0) {
    container.innerHTML = '<div class="empty-history">No execution history available yet. Run a command to begin!</div>';
    return;
  }
  
  let html = `
    <table class="history-table">
      <thead>
        <tr>
          <th>Time</th>
          <th>Query</th>
          <th>Intent</th>
          <th>Person</th>
          <th>Photos</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
  `;
  
  history.forEach(item => {
    const time = new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const date = new Date(item.timestamp).toLocaleDateString([], { month: 'short', day: 'numeric' });
    
    html += `
      <tr>
        <td style="white-space: nowrap; color: var(--text-muted);">${date} ${time}</td>
        <td>${escapeHtml(item.query)}</td>
        <td style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--accent-purple);">${item.intent}</td>
        <td>${item.person}</td>
        <td>${item.count}</td>
        <td><span class="history-status-badge ${item.status}">${item.status.toUpperCase()}</span></td>
      </tr>
    `;
  });
  
  html += `
      </tbody>
    </table>
  `;
  
  container.innerHTML = html;
}

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
