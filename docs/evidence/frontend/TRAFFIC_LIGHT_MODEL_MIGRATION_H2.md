# Traffic Light Model Migration — H.2

**Datei:** `frontend/src/trafficLight/trafficLightModel.ts`

## Migriert

| Funktion | Vorher | Nachher |
|----------|--------|---------|
| `worstTrafficLightLamp` | `LAMP_RANK` lokal | `worstTrafficLightLampFromInputs` |
| `trafficLightStateToLamp` | direkte Rückgabe | `trafficLightLampFromInput` (+ unknown→yellow) |

## Unverändert

- Öffentliche Typen und `derive*` Domain-Funktionen
- `TRAFFIC_LIGHT_COPY`
- Outputs: green/yellow/red

## Entfernt

- `LAMP_RANK` Konstante
