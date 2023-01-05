# YUDEE Smart Pillow

Custom cloud integration for YUDEE Smart Pillow


## Features

This integration will poll daily sleep report from cloud server after pressing `Get last night report` button.


## Available data

  
| Metric | Unit |
|--------------------------|-----------------------|
| Awake | % |
| Deep sleep | % |
| Light sleep | % |
| REM | % |
| Respiratory rate average | BPM |
| Heart beat average | BPM |
| Sleep score | % |
| Go to bed time | time |
| Wake up time | time |
| Snore count | times |
| Vibration count | times |
| Deep sleep time | occurred time |
| Light sleep time | time duration |
| REM time | time duration |
| Awake time | time duration |
| Move time | occurred time + count |
| Revolve time | occurred time + count |
| Snore count | occurred time + count |
| Vibration time | occurred time + count |

## Installation
1. Copy `custom_components/YUDEE_SMART_PILLOW` folder to your `custom_components` folder.
2. Restart your Home Assistant.
3. If your Home Assistant setup supports Bluetooth and the smart pillow is nerby, this integration should automatically discovered the pillow and mac address will be filled in automatically. If not, you need to press `ADD INTEGRATION` botton and search for `YUDEE Smart Pillow`
4. Fill out credentials. (cname, cnametype, sort)
