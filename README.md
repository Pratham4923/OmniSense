# OmniSense

OmniSense Emergency Priority is a real-time traffic signal priority system designed to detect emergency vehicles and create intelligent green corridors for faster response.

The system combines RFID, acoustic detection, CCTV/vision data, and traffic metrics to identify emergency vehicles such as ambulances and firetrucks. It then updates signal behavior and provides dashboard visibility for monitoring active emergency flow.

## Features

- Real-time emergency vehicle simulation
- RFID-based emergency vehicle detection
- Siren/acoustic data integration
- Vision/CCTV-based vehicle status display
- Smart signal preemption
- Green corridor route visualization
- Live traffic signal countdown
- Emergency type injection: Ambulance and Firetruck
- Dashboard with system metrics and history
- Flask-based backend API

## Tech Stack

- Python
- Flask
- HTML
- CSS
- JavaScript

## Project Structure

```text
OmniSense/
├── Architecture and TechStack/
│   ├── OmniSense_EVRS_TechStack.docx
│   ├── OmniSense_Simulation.pptx
│   ├── Omnisense TechStack.pptx
│   └── omnisense_simulation_techstack.pdf
│
├── Code/
│   ├── app.py
│   ├── requirements.txt
│   ├── static/
│   ├── templates/
│   └── utils/
│
├── Testing/
├── data-collection/
├── final code/
├── LICENSE
└── README.md
````

## Installation

1. Clone the repository:

```bash
git clone https://github.com/Pratham4923/OmniSense.git
cd OmniSense/Code
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
```

For Windows:

```bash
venv\Scripts\activate
```

For macOS/Linux:

```bash
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the Flask application:

```bash
python app.py
```

Open the application in your browser:

```text
http://127.0.0.1:5000
```

## API Endpoints

### Home Page

```http
GET /
```

Renders the OmniSense dashboard.

### Get Current System State

```http
GET /api/state
```

Returns live simulation data including signal state, emergency type, RFID data, acoustic data, vision data, metrics, and green corridor path.

### Perform Action

```http
POST /api/action
```

Supported actions:

```json
{
  "action": "toggle"
}
```

Starts or pauses the simulation.

```json
{
  "action": "inject",
  "vehicleType": "Ambulance"
}
```

Injects an emergency vehicle event.

```json
{
  "action": "inject",
  "vehicleType": "Firetruck"
}
```

Injects a firetruck emergency event.

```json
{
  "action": "reset"
}
```

Resets the simulation.

## How It Works

1. The simulation starts with normal traffic signal behavior.
2. RFID, acoustic, and vision modules provide emergency vehicle signals.
3. When an emergency vehicle is injected, the system activates signal preemption.
4. The active junction turns green to create a temporary green corridor.
5. The dashboard updates live metrics, system history, signal state, and route information.
6. Once the preemption window ends, the system returns to normal signal cycling.

## Use Cases

* Smart city emergency response
* Ambulance priority systems
* Firetruck route clearance
* Traffic signal optimization
* Emergency vehicle tracking dashboards
* Intelligent transportation system prototypes

## Requirements

```txt
Flask>=3.0,<4.0
```

## License

This project is licensed under the MIT License.


[1]: https://github.com/Pratham4923/OmniSense "GitHub - Pratham4923/OmniSense: OmniSense Emergency Priority is a real-time traffic system that detects ambulances using siren audio, CCTV, and GPS/V2X data. A fusion engine assigns a probability score, while an AI optimizer creates green corridors and updates smart signals, reducing response time with full tracking and dashboard visibility. · GitHub"
