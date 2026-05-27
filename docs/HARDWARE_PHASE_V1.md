# Hardware Phase V1.0 — Smart Capsule Embedded System

**Date:** 2026-05-27
**Status:** Specification only — no PCB fabricated

---

## 1. Purpose

Define the embedded hardware platform for the ZILFIT Smart Capsule.
V1.0 covers component selection, BLE packet design, power strategy,
and sensor polling architecture.

No hardware is ordered. This is the engineering specification
required before PCB design begins.

---

## 2. MCU Options

### Option A: ESP32-C3 (Recommended)

| Feature | Spec |
|---------|------|
| Core | RISC-V 32-bit, 160 MHz |
| BLE | 5.0, 2 Mbps |
| GPIO | 22 |
| ADC | 2× 12-bit SAR (4 channels via MUX) |
| Flash | 4 MB |
| RAM | 400 KB |
| Deep sleep | 5 µA |
| Price | ~$2.50 |

**Pros:** Mature ecosystem, Arduino/ESP-IDF, built-in BLE, low cost.

### Option B: nRF52840

| Feature | Spec |
|---------|------|
| Core | ARM Cortex-M4, 64 MHz |
| BLE | 5.4, long range |
| ADC | 8× 12-bit |
| Flash | 1 MB |
| RAM | 256 KB |
| Deep sleep | 1.4 µA |
| Price | ~$5.00 |

**Pros:** Superior BLE stack, ultra-low power, Nordic SDK.
**Cons:** Higher cost, smaller community for sensor integration.

**Decision:** Start with ESP32-C3 for V0.1 prototype.
Migrate to nRF52840 for V0.3 production if power budget requires it.

---

## 3. Sensor Array

| # | Sensor | Part | Bus | Rate | Resolution |
|---|--------|------|-----|------|------------|
| P0 | Heel pressure | IMS-C05A (capacitive) | I²C | 50 Hz | 12-bit |
| P1 | Arch pressure | IMS-C05A | I²C | 50 Hz | 12-bit |
| P2 | Ball pressure | IMS-C05A | I²C | 50 Hz | 12-bit |
| P3 | Hallux pressure | IMS-C05A | I²C | 50 Hz | 12-bit |
| IMU | 6-axis | ICM-42688-P | SPI | 100 Hz | 16-bit |
| TEMP | Temperature | MCP9808 | I²C | 1 Hz | 0.0625°C |

All I²C sensors share a single bus via TCA9548A multiplexer.

---

## 4. BLE Packet Design

### Service UUID: `0x1800` (ZILFIT Capsule Service — to be assigned)

### Data Characteristic (notify, 20 bytes)

```
Byte 0:     Packet type (0x01 = sensor data)
Byte 1:     Sequence number (0–255, wraps)
Byte 2–3:   P0_raw (uint16, big-endian, raw ADC)
Byte 4–5:   P1_raw (uint16)
Byte 6–7:   P2_raw (uint16)
Byte 8–9:   P3_raw (uint16)
Byte 10–11: Accel_X (int16, mg)
Byte 12–13: Accel_Y (int16, mg)
Byte 14–15: Accel_Z (int16, mg)
Byte 16–17: Gyro_X (int16, 0.01 dps)
Byte 18–19: Gyro_Y (int16, 0.01 dps)
```

### Extended Packet (Byte 0 = 0x02, 20 bytes)

```
Byte 0:     0x02
Byte 1:     Sequence number
Byte 2–3:   Gyro_Z (int16, 0.01 dps)
Byte 4–5:   Temp (uint16, 0.01 °C)
Byte 6–7:   Battery_mV (uint16)
Byte 8–19:  Reserved (0x00)
```

Packets alternate: Type 0x01 sent at odd sequence numbers, Type 0x02 at even. This yields effective ~50 Hz pressure + IMU data with temperature and battery every other packet.

### Connection Interval: 20 ms (50 Hz)
### MTU: 23 bytes (BLE 4.2 minimum)

---

## 5. Battery Strategy

| Parameter | Value |
|-----------|-------|
| Chemistry | Li-Po, single cell |
| Capacity | 200 mAh |
| Nominal voltage | 3.7 V |
| Operating time (streaming) | ~6 hours |
| Standby time | ~72 hours |
| Charging | USB-C, TP4056 charge IC |
| Charge time | ~45 minutes |
| Protection | Overcharge, over-discharge, short circuit (DW01 + FS8205) |

---

## 6. Charging Method

- USB-C connector on capsule housing
- TP4056 linear charger, 500 mA charge current
- Charging LED: red while charging, green when full
- Magnetic pogo-pin alternative for V0.3 (no exposed port)
- No wireless charging in V0.1

---

## 7. Sensor Polling Rates

| Sensor | Poll Rate | Notes |
|--------|-----------|-------|
| Pressure (all 4) | 50 Hz | Synchronized via I²C MUX round-robin |
| IMU accel + gyro | 100 Hz | SPI DMA, double-buffered |
| Temperature | 1 Hz | Low priority, interleaved |
| Battery voltage | 0.1 Hz | ADC read on ESP32 internal channel |

IMU runs at 100 Hz internally. Pressure at 50 Hz. BLE notifications
at 50 Hz (20ms connection interval) carry both streams interleaved.

---

## 8. Future Vibration / Plantar Feedback Module (V0.3+)

- 4× coin vibration motors (10mm, 3V) under each pressure zone
- Driven by DRV2605L haptic driver via I²C
- Patterns: tap, buzz, ramp-up, ramp-down
- Use cases: gait retraining feedback, step cadence pacing, zone awareness
- **Engineering only** — no reflexology or therapeutic vibration claims

---

## 9. PCB Constraints

| Parameter | Value |
|-----------|-------|
| Dimensions | 35 × 20 mm (fits capsule compartment) |
| Layers | 2 |
| Thickness | 0.8 mm |
| Connectors | 1× USB-C, 1× 10-pin FPC (sensors), 1× JST-PH (battery) |
| Enclosure | PA12 SLS, IPX4 rated |

---

## 10. Non-Clinical Disclaimer

> This hardware specification describes an engineering data collection
> platform. It is not a medical device. No therapeutic, diagnostic, or
> treatment function is claimed. Sensor data is provided for gait
> analysis and comfort evaluation only.

---

*End of Hardware Phase V1.0*
