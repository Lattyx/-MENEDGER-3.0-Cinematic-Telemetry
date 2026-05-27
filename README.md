<div align="center">
  <h1>🌌 MENEDGER 3.0 // Cinematic Telemetry</h1>
  <p><b>An ultra-realistic, premium glassmorphism desktop task manager and system monitor for Windows.</b></p>
  <p><i>Created by <a href="https://github.com/Lattyxx">Lattyxx</a></i></p>
</div>

---

## ✨ Features

* **💎 Ultra-Realistic Glassmorphism**: True window translucency with dynamic frosted glass (blur) that perfectly bleeds your desktop background through the app.
* **🎨 Infinite Customization**: Choose between meticulously crafted preset themes (Aurora, Teal, Cyber Rose), or use the built-in color picker to inject your own custom hex codes dynamically!
* **⚡ Real-Time Telemetry Engine**: Tracks CPU, RAM, GPU, Disk usage, and Network Speeds via a lightning-fast asynchronous WebSocket backend.
* **🧩 Modular Dashboard**: Toggle individual hardware widgets on and off to create your perfect monitoring setup.
* **🔍 Smart Interface Scaling**: Crisp and responsive native zooming mechanism that scales beautifully, even on 4K displays.
* **🛡️ Advanced Process Manager**: Search, sort, and securely terminate running processes directly from the UI.
* **🔥 Drag & Drop File Shredder**: Securely delete files directly from the dashboard.

## 🛠️ Tech Stack

* **Backend**: Python 3, `FastAPI`, `WebSockets`, `psutil`
* **Frontend**: Vanilla HTML5, CSS3, JavaScript (`Chart.js` for dynamic graphs)
* **GUI Engine**: `pywebview` (utilizing Microsoft Edge WebView2 for true frameless transparency on Windows)

## 🚀 Installation & Usage

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Lattyxx/Menedger.git
   cd Menedger
   ```

2. **Install the required dependencies:**
   Make sure you have Python installed, then run:
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: You will need `fastapi`, `uvicorn`, `psutil`, `pywebview`, and `websockets`)*

3. **Launch the application:**
   ```bash
   python main.py
   ```

## ⚙️ Customizing the UI

Menedger 3.0 is built to be yours. Head over to the **Settings (Внешний Вид)** tab to customize:
* **Window Opacity**: Adjust from 30% to 100%.
* **Frost Blur**: Control the background backdrop-filter intensity (10px to 40px).
* **Accent Colors**: Select a custom color to instantly redraw graphs, neon sliders, and glowing buttons.
* **Interface Scale**: Zoom in or out from 80% to 150% with perfect pixel clarity.

---

<div align="center">
  <p>&copy; 2026 Created with 💜 by <b>Lattyxx</b>.</p>
</div>
