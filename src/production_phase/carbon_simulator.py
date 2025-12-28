import random
from datetime import datetime

def get_current_carbon_intensity(force_mode=None):
    """
    Simulates Grid Carbon. 
    Can be forced to 'HIGH' or 'LOW' by user input for demo purposes.
    """
    # 1. Determine Status (Forced or Simulated)
    if force_mode and force_mode.upper() in ["HIGH", "LOW"]:
        status = force_mode.upper()
        # Add a flag to show this was manual
        is_manual = True
    else:
        # Default Logic: Peak hours = High Carbon
        current_hour = datetime.now().hour
        # Peak hours: 8am-11am AND 5pm-9pm
        is_peak = (8 <= current_hour <= 11) or (17 <= current_hour <= 21)
        status = "HIGH" if is_peak else "LOW"
        is_manual = False

    # 2. Generate appropriate random numbers based on status
    if status == "HIGH":
        # Coal/Gas heavy scenario
        carbon_val = random.uniform(400, 650)
    else:
        # Wind/Solar heavy scenario
        carbon_val = random.uniform(50, 180)

    return {
        "timestamp": datetime.now().isoformat(),
        "carbon_intensity": round(carbon_val, 1),
        "status": status,
        "is_manual_override": is_manual,
        "message": f"Grid Carbon is {status} ({round(carbon_val)} gCO2/kWh)"
    }

if __name__ == "__main__":
    # Test run
    print(get_current_carbon_intensity())
    print(get_current_carbon_intensity("HIGH"))