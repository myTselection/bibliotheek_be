[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/myTselection/bibliotheek_be.svg)](https://github.com/myTselection/bibliotheek_be/releases)
![GitHub repo size](https://img.shields.io/github/repo-size/myTselection/bibliotheek_be.svg)

[![GitHub issues](https://img.shields.io/github/issues/myTselection/bibliotheek_be.svg)](https://github.com/myTselection/bibliotheek_be/issues)
[![GitHub last commit](https://img.shields.io/github/last-commit/myTselection/bibliotheek_be.svg)](https://github.com/myTselection/bibliotheek_be/commits/master)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/m/myTselection/bibliotheek_be.svg)](https://github.com/myTselection/bibliotheek_be/graphs/commit-activity)

# Bibliotheek.be
[bibliotheek.be](https://www.bibliotheek.be/) Home Assistant custom component. It provides a clear overview of all items loaned a the different libraries by different users linked to the main account (eg children). An overview off all items per library or an overview of all items per user can be shown, see complex markdown examples below. Based on the sensors, automations can be build to get warned: eg when little time is left and certainly when extension is not possible.

<p align="center"><img src="https://raw.githubusercontent.com/myTselection/bibliotheek_be/master/icon.png"/></p>


## Installation
- [HACS](https://hacs.xyz/): add url https://github.com/myTselection/bibliotheek_be as custom repository (HACS > Integration > option: Custom Repositories)
- Restart Home Assistant
- Add 'Bibliotheek.be' integration via HA Settings > 'Devices and Services' > 'Integrations'
- Provide Bibliotheek.be username and password
- Sensor `Bibliotheek.be` should become available with the number of items lent out.
  - sensor.bibliotheek_be_`<username>`_`<library>` will be created for each user linked to the account
  - sensor.bibliotheek_be_bib_`<library>` will be created for each library
  - sensor.bibliotheek_be_warning will indicate if within how many days some items have to be returned at *any* library (this can be used of conditions, notifications, etc).

## Status
Still some optimisations are planned, see [Issues](https://github.com/myTselection/bibliotheek_be/issues) section in GitHub.

## Technical pointers
The main logic and API connection related code can be found within source code bibliotheek_be/custom_components/bibliotheek_be:
- [sensor.py](https://github.com/myTselection/bibliotheek_be/blob/master/custom_components/bibliotheek_be/sensor.py)
- [utils.py](https://github.com/myTselection/bibliotheek_be/blob/master/custom_components/bibliotheek_be/utils.py) -> mainly ComponentSession class

All other files just contain boilerplat code for the integration to work wtihin HA or to have some constants/strings/translations.

## Example usage:
### Markdown Example for details of all libraries

<p align="center"><img src="https://raw.githubusercontent.com/myTselection/bibliotheek_be/master/Markdown%20Card%20example.png"/></p>
<p align="center"><img src="https://raw.githubusercontent.com/myTselection/bibliotheek_be/master/Markdown%20Card%20details%20example.png"/></p>

<details><summary>Click to show the Mardown example</summary>
```
type: markdown
content: >-
  {% set libraries = states | selectattr("entity_id",
  "match","^sensor.bibliotheek_be_bib*") | list %}

  {% for library_device in libraries %}
    {% set library = library_device.entity_id %}
    ## Bib {{state_attr(library,'libraryName') }}:
    {% set all_books = state_attr(library,'loandetails') %}
    {% set urgent_books = all_books | selectattr("days_remaining", "eq",int(state_attr(library,'days_left'))) | list |sort(attribute="extend_loan_id", reverse=False)%}
    {% set other_books = all_books | rejectattr("days_remaining", "eq",int(state_attr(library,'days_left'))) | list |sort(attribute="days_remaining", reverse=False)|sort(attribute="extend_loan_id", reverse=False)%}
    {% if urgent_books %}
    - {{state_attr(library,'num_loans') }} stuks in te leveren binnen **{{states(library)}}** dagen: {{state_attr(library,'lowest_till_date') }}
      <details>
        <summary>Toon dringende ({{urgent_books|length}}):</summary>
        {% for book in urgent_books  %}
        - <details><summary>{% if book.extend_loan_id %}{{ book.loan_till }}{% else %}<b>{{ book.loan_till }}</b>{% endif %}: {{ book.title }} ~ {{ book.author }}</summary> 
    
          |  |  |
          | :--- | :--- |
          | Binnen: | {{ book.days_remaining }} dagen |
          | Verlenging: | {% if book.extend_loan_id %}verlengbaar{% else %}**Niet verlengbaar**{% endif %} |
          | Bibliotheek: | <a href="{{book.url}}" target="_blank">{{book.library}}</a> |
          | Type: | {% if book.loan_type == 'Unknown' %}Onbekend{% else %}{{book.loan_type}}{% endif %} |
          | Afbeelding: | <img src="{{ book.image_src }}" height="100"/> |
          </details>
        {% endfor %}
      </details>
    {% endif %}
    - In totaal {{state_attr(library,'num_total_loans') }} uitgeleend:
      - Boeken: {{state_attr(library,'Boek') }}
      - Onbekend: {{state_attr(library,'Unknown') }}
      - DVDs: {{state_attr(library,'Dvd') }}
      - Strips: {{state_attr(library,'Strip') }}
      {% if other_books %}
      <details>
        <summary>Toon overige ({{other_books|length}}):</summary>
      {% for book in other_books  %}
      - <details><summary>{% if book.extend_loan_id %}{{ book.loan_till }}{% else %}<b>{{ book.loan_till }}</b>{% endif %}: {{ book.title }} ~ {{ book.author }}</summary> 

          |  |  |
          | :--- | :--- |
          | Verlenging: | {% if book.extend_loan_id %}verlengbaar{% else %}**Niet verlengbaar**{% endif %} |
          | Bibliotheek: | <a href="{{book.url}}" target="_blank">{{book.library}}</a> |
          | Type: | {% if book.loan_type == 'Unknown' %}Onbekend{% else %}{{book.loan_type}}{% endif %} |
          | Afbeelding: | <img src="{{ book.image_src }}" height="100"/> |
        </details>
      {% endfor %}
      </details>
      {% endif %}
    {% endfor %}
title: Bibliotheken
```
</details>
### Markdown Example for details of all users:

<details><summary>Click to show the Mardown example</summary>
```
type: markdown
content: >-
  {% set library_users = states |
  selectattr("entity_id","match","^sensor.bibliotheek_be_*") |
  rejectattr("entity_id","match","^sensor.bibliotheek_be_bib*")|
  rejectattr("entity_id","match","^sensor.bibliotheek_be_warning")| list%}

  {% for user_device in library_users %}

  {% set user = user_device.entity_id %}

  {% if state_attr(user,'num_loans') > 0 %}

  ## {{state_attr(user,'username') }} {{state_attr(user,'libraryName') }}
  (Barcode: {{state_attr(user,'barcode') }}):

  - Gereserveerde stuks: {{state_attr(user,'num_reservations') }}

  - Uitstaande boetes: {{state_attr(user,'open_amounts') }}
    {% if state_attr(user,'num_loans') > 0 %}
    {% set all_books = state_attr(user,'loandetails').values()  |sort(attribute="days_remaining", reverse=False)|sort(attribute="extend_loan_id", reverse=False)%}
  - In totaal {{state_attr(user,'num_loans') }} uitgeleend{% if all_books %}
      {% for book in all_books %}
      - <details><summary>{% if book.extend_loan_id %}{{ book.loan_till }}{% else %}<b>{{ book.loan_till }}</b>{% endif %}: {{ book.title }} ~ {{ book.author }}</summary> 

          |  |  |
          | :--- | :--- |
          | Binnen: | {{ book.days_remaining }} dagen |
          | Verlenging: | {% if book.extend_loan_id %}verlengbaar{% else %}**Niet verlengbaar**{% endif %} |
          | Bibliotheek: | <a href="{{book.url}}" target="_blank">{{book.library}}</a> |
          | Type: | {% if book.loan_type == 'Unknown' %}Onbekend{% else %}{{book.loan_type}}{% endif %} |
          | Afbeelding: | <img src="{{ book.image_src }}" height="100"/> |
        </details>
      {% endfor %}
    {% endif %}
    {% else %}
  - Geen uitleningen
    {% endif %}
    Laatst bijgewerkt: {{state_attr(user,'last update')  | as_timestamp | timestamp_custom("%d-%m-%Y %H:%M")}}
  {% endif %}

  {% endfor %}

  {% for user_device in library_users %}

  {% set user = user_device.entity_id %}

  {% if state_attr(user,'num_loans') == 0 %}

  ## {{state_attr(user,'username') }} {{state_attr(user,'libraryName') }}
  (Barcode: {{state_attr(user,'barcode') }}):

  - Gereserveerde stuks: {{state_attr(user,'num_reservations') }}

  - Uitstaande boetes: {{state_attr(user,'open_amounts') }}

  - Geen uitleningen
    Laatst bijgewerkt: {{state_attr(user,'last update')  | as_timestamp | timestamp_custom("%d-%m-%Y %H:%M")}}
  {% endif %}

  {% endfor %}
title: Gebruikers
```
</details>

### Example with conditional check for warnings:

#### Extra binary sensor based on personal perference on number of days to limit the warning
Example provided with sensor that will turn on if items have to be returned within 7 days. The alert sensor will be turned on if items have to be returned within 7 days and no extension is possible.
`configuration.yaml`:

<details><summary>Click to show the Mardown example</summary>
```
binary_sensor:
  - platform: template
    sensors:
      bibliotheek_warning_7d:
        friendly_name: Bibliotheek Warning 7d
        value_template: >
           {{states('sensor.bibliotheek_be_warning')|int <= 7}}
  - platform: template
    sensors:
      bibliotheek_alert_7d:
        friendly_name: Bibliotheek Alert 7d
        value_template: >
           {{states('sensor.bibliotheek_be_warning')|int <= 7 and state_attr('sensor.bibliotheek_be_warning','some_not_extendable') == True}}
```
Base on these sensors, a automation can be build for notifications or below conditional card can be defined:

```
- type: conditional
conditions:
  - entity: binary_sensor.bibliotheek_warning_7d
	state: 'on'
  - entity: binary_sensor.bibliotheek_alert_7d
	state: 'off'
card:
  type: markdown
  content: ⏰Boeken verlengen deze week !
- type: conditional
conditions:
  - entity: binary_sensor.bibliotheek_warning_7d
	state: 'on'
  - entity: binary_sensor.bibliotheek_alert_7d
	state: 'on'
card:
  type: markdown
  content: ⏰Boeken binnen brengen deze week !
```
</details>
