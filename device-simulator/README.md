# Simulated devices

This directory contains a Python publisher for the temperature sensor, humidity sensor, and irrigation controller. Topics and JSON payloads follow `../contracts/mqtt-topics.md`.

Start the backend first, then publish one complete telemetry pair from the project root:

```powershell
.venv\\Scripts\\python.exe device-simulator/simulator.py --once
```

The backend should mark the three devices online and create a complete `plot_report` row after receiving the temperature and humidity messages.

To keep publishing a fixed moisture value every five seconds:

```powershell
.venv\Scripts\python.exe device-simulator/simulator.py --moisture 40 --interval 5
```

The publisher continues to receive irrigation commands and return acknowledgements, but it does not synthesize drought or post-irrigation recovery scenarios.
