[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/myTselection/bibliotheek_be.svg)](https://github.com/myTselection/bibliotheek_be/releases)
![GitHub repo size](https://img.shields.io/github/repo-size/myTselection/bibliotheek_be.svg)

[![GitHub issues](https://img.shields.io/github/issues/myTselection/bibliotheek_be.svg)](https://github.com/myTselection/bibliotheek_be/issues)
[![GitHub last commit](https://img.shields.io/github/last-commit/myTselection/bibliotheek_be.svg)](https://github.com/myTselection/bibliotheek_be/commits/master)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/m/myTselection/bibliotheek_be.svg)](https://github.com/myTselection/bibliotheek_be/graphs/commit-activity)

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
### Markdown Example for details of all libraries
```
{% set libraries = states | selectattr("entity_id", "match","^sensor.bibliotheek_be_bib*") | list %}
{% for library_device in libraries %}
  {% set library = library_device.entity_id %}
  ## Bib {{state_attr(library,'libraryName') }}:
  - {{state_attr(library,'num_loans') }} stuks in te leveren binnen **{{states(library)}}** dagen ({{state_attr(library,'lowest_till_date') }})
  {% for book in state_attr(library,'loandetails') %}
    - {{ book.title }} ~ {{ book.author }} ({% if book.loan_type == 'Unknown' %}Onbekend{% else %}{{book.loan_type}}{% endif %}) {# TODO {{book.user}}#}<img src="{{book.image_src}}" height="20"/>
  {% endfor %}
  - In totaal {{state_attr(library,'num_total_loans') }} uitgeleend:
    - Boeken: {{state_attr(library,'Boek') }}
    - Onbekend: {{state_attr(library,'Unknown') }}
    - DVDs: {{state_attr(library,'Dvd') }}
    - Strips: {{state_attr(library,'Strip') }}
{% endfor %}

```

<p align="center"><img src="https://raw.githubusercontent.com/myTselection/bibliotheek_be/master/Markdown%20Gauge%20Card%20example.png"/></p>
