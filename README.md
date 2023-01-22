[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

# NOT USABLE YET, STILL IN EARLY DEVELOPMENT

# Bibliotheek.be (Beta)
[bibliotheek.be](https://www.bibliotheek.be/) Home Assistant custom component

<p align="center"><img src="https://raw.githubusercontent.com/myTselection/bibliotheek_be/master/icon.png"/></p>


## Installation
- [HACS](https://hacs.xyz/): add url https://github.com/myTselection/bibliotheek_be as custom repository (HACS > Integration > option: Custom Repositories)
- Restart Home Assistant
- Add 'Bibliotheek.be' integration via HA Settings > 'Devices and Services' > 'Integrations'
- Provide Bibliotheek.be username and password
- Sensor `Bibliotheek.be` should become available with the number of items lent out.

## Status
Still some optimisations are planned, see [Issues](https://github.com/myTselection/bibliotheek_be/issues) section in GitHub.

## Technical pointers
The main logic and API connection related code can be found within source code bibliotheek_be/custom_components/bibliotheek_be:
- [sensor.py](https://github.com/myTselection/bibliotheek_be/blob/master/custom_components/bibliotheek_be/sensor.py)
- [utils.py](https://github.com/myTselection/bibliotheek_be/blob/master/custom_components/bibliotheek_be/utils.py) -> mainly ComponentSession class

All other files just contain boilerplat code for the integration to work wtihin HA or to have some constants/strings/translations.

## Example usage:
### Gauge & Markdown
```
type: vertical-stack
cards:
  - type: markdown
    content: >-
      ## Bibliotheek.be {{state_attr('sensor.bibliotheek_be','TODO')}}



      latst update: *{{state_attr('sensor.bibliotheek_be','last update')
      | as_timestamp | timestamp_custom("%d-%m-%Y")}}*
       
      green: 0
  - type: history-graph
    entities:
      - entity: sensor.bibliotheek_be
    hours_to_show: 500
    refresh_interval: 60

```

<p align="center"><img src="https://raw.githubusercontent.com/myTselection/bibliotheek_be/master/Markdown%20Gauge%20Card%20example.png"/></p>
