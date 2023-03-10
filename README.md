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

## Integration
Sensors `Bibliotheek.be` should become available with the number of items lent out.
- <details><summary><code>sensor.bibliotheek_be_[username]_[library]</code> will be created for each user linked to the account</summary>

	| Attribute | Description |
	| --------- | ----------- |
	| State     | Number of loans by this user at this library |
	| `userid `   | Technical user id assigned by bibliotheek.be |
	| `barcode`   | The unique user barcode which is also shown on the library card |
	| `num_loans` | Number of loans by this user at this library (same as state value) |
	| `num_reservations`  | Number of reservations by this user at this library |
	| `open_amounts`  | Open amount (???) due to this library (eg related to fines) |
	| `username`  | First and lastname of the user |
	| `libraryName`  | Name of the library or the group of libraries |
	| `loandetails`  | Json containing all the loans of this user at this library. The structure of json is:<br/>  `{ 'item name' :` <br/>&nbsp;` { tile: 'title of the item', ` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`author: 'author of the item', ` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`loan_type: 'type of the item (eg book, dvd, ...) , ` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`url: 'url of the specific item', ` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`image_src: 'url to image of the item', ` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`days_remaining: 'number of days by which the item has to be returned or extended', ` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`loan_from: 'Start date of the loan', ` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`loan_till: 'Date by which the item needs to be returned', ` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`extend_loan_id: 'the id used to extend the item, if no id is available, the item can not be extended',` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`library: 'name of the actual library location (city) where the item is belonging too',` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`user: 'the user that lended the item',` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`barcode: 'the barcode of the card that was used to lend the item' }`  |
	</details>
- <details><summary><code>sensor.bibliotheek_be_bib_[library]</code> will be created for each library</summary>

	| Attribute | Description |
	| --------- | ----------- |
	| State     | Min days left by which some items need to be returned |
	| `some_not_extendable` | True if some of the items that needs to be returned first (see state for nr of days) of this library can not be extended |
	| `lowest_till_date`   | Min date by which some items need to be returned |
	| `num_loans`  | Number of loans that need to be returned first (see state for nr of days)  |
	| `num_loans_total`  | Total number of loans at this library |
	| `loandetails`  | Json containing all the loans of this user at this library. The structure of json is:<br/>  `[{ 'item name' :` <br/>&nbsp;` { tile: 'title of the item', ` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`author: 'author of the item', ` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`loan_type: 'type of the item (eg book, dvd, ...) , ` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`url: 'url of the specific item', ` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`image_src: 'url to image of the item', ` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`days_remaining: 'number of days by which the item has to be returned or extended', ` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`loan_from: 'Start date of the loan', ` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`loan_till: 'Date by which the item needs to be returned', ` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`extend_loan_id: 'the id used to extend the item, if no id is available, the item can not be extended',` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`library: 'name of the actual library location (city) where the item is belonging too',` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`user: 'the user that lended the item',` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`barcode: 'the barcode of the card that was used to lend the item' }]`  |
	| <loan_type> | Number of items of this loan type lended. For each loan type known this attribute will be added |
	
	</details>
- <details><summary><code>sensor.bibliotheek_be_warning</code> will indicate within how many days some items have to be returned at *any* library (this can be used of conditions, notifications, etc).</summary>

	| Attribute | Description |
	| --------- | ----------- |
	| State     | Min days left by which some items need to be returned by any user linked to the account at any library |
	| `some_not_extendable` | True if some of the items that needs to be returned first (see state for nr of days) of this library can not be extended |
	| `lowest_till_date` | Min date by which some items need to be returned |
	| `num_loans`  | Number of loans that need to be returned first (see state for nr of days)  |
	| `num_loans_total`  | Total number of loans by any user at any library |
	| `library_name`  | Name(s) of the library at which some items need to be returned first (or comma spearated list of names) |
	
	</details>
- Following services `bibliotheek_be` will be available:
	- <details><summary><code>bibliotheek_be.extend_loan</code>: extend a single item, based on extend_loan_id, if the days_remaining is less than or equal the max set</summary> 
	
		```
		service: bibliotheek_be.extend_loan
		data:
		  extend_loan_id: 12345678 
		  max_days_remaining: 8
		``` 
		
	  </details>
	
	- <details><summary><code>bibliotheek_be.extend_loans_library</code>: extend all loans of a library that have days_remaining less than or equal the max set</summary>
	
		```
		service: bibliotheek_be.extend_loans_library
		data:
		  library_name: 'City' 
		  max_days_remaining: 8
		```
		  
	  </details>
	  
	- <details><summary><code>bibliotheek_be.extend_loans_user</code>: extend all loans of a user that have days_remaining less than or equal the max set</summary>
	
		```
		service: bibliotheek_be.extend_loan
		data:
		  barcode: '1234567890123'
		  max_days_remaining: 8
		```
		  
          </details>
	  
	- <details><summary><code>bibliotheek_be.extend_all_loans</code>: extend all loans that have days_remaining less than or equal the max set</summary>
	
		```
		service: bibliotheek_be.extend_loan
		data:
		  max_days_remaining: 8
		```
		  
	   </details>

## Status
Still some optimisations are planned, see [Issues](https://github.com/myTselection/bibliotheek_be/issues) section in GitHub.

## Technical pointers
The main logic and API connection related code can be found within source code bibliotheek_be/custom_components/bibliotheek_be:
- [sensor.py](https://github.com/myTselection/bibliotheek_be/blob/master/custom_components/bibliotheek_be/sensor.py)
- [utils.py](https://github.com/myTselection/bibliotheek_be/blob/master/custom_components/bibliotheek_be/utils.py) -> mainly ComponentSession class
- [\_init\_.py](https://github.com/myTselection/bibliotheek_be/blob/master/custom_components/bibliotheek_be/_init_.py) -> general setup + services

All other files just contain boilerplat code for the integration to work wtihin HA or to have some constants/strings/translations.

## Example usage:
### Markdown Example for details of all libraries

<p align="center"><img src="https://raw.githubusercontent.com/myTselection/bibliotheek_be/master/Markdown%20Card%20example.png" width="400"/></p>
<p align="center"><img src="https://raw.githubusercontent.com/myTselection/bibliotheek_be/master/Markdown%20Card%20details%20example.png" width="400"/></p>

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
    {% set other_books = all_books | rejectattr("days_remaining", "eq",int(state_attr(library,'days_left'))) | list |sort(attribute="days_remaining", reverse=False)%}
    {% if urgent_books %}
    - {{state_attr(library,'num_loans') }} stuks in te leveren binnen **{{states(library)}}** dagen: {{strptime(state_attr(library,'lowest_till_date'), "%d/%m/%Y").strftime("%a %d/%m/%Y") }}
      <details>
        <summary>Toon dringende ({{urgent_books|length}}):</summary>
        {% for book in urgent_books  %}
        - <details><summary>{% if book.extend_loan_id %}{{ strptime(book.loan_till, "%d/%m/%Y").strftime("%a %d/%m/%Y") }}{% else %}<b>{{ strptime(book.loan_till, "%d/%m/%Y").strftime("%a %d/%m/%Y") }}</b>{% endif %}: {{ book.title }} ~ {{ book.author }}</summary> 
    
          |  |  |
          | :--- | :--- |
          | Binnen: | {{ book.days_remaining }} dagen |
          | Verlenging: | {% if book.extend_loan_id %}verlengbaar{% else %}**Niet verlengbaar**{% endif %} |
          | Bibliotheek: | <a href="{{book.url}}" target="_blank">{{book.library}}</a> |
          | Gebruiker: | {{book.user}} ({{book.barcode}}) |
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
          | Gebruiker: | {{book.user}} ({{book.barcode}}) |
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
    {% set all_books = state_attr(user,'loandetails').values()  |sort(attribute="days_remaining", reverse=False)%}
  - In totaal {{state_attr(user,'num_loans') }} uitgeleend{% if all_books %}
      {% for book in all_books %}
      - <details><summary>{% if book.extend_loan_id %}{{ strptime(book.loan_till, "%d/%m/%Y").strftime("%a %d/%m/%Y") }}{% else %}<b>{{ strptime(book.loan_till, "%d/%m/%Y").strftime("%a %d/%m/%Y") }}</b>{% endif %}: {{ book.title }} ~ {{ book.author }}</summary> 

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
The example below will create a binary sensor that will turn on if items have to be returned within 7 days. The alert sensor will be turned on if items have to be returned within 7 days and no extension is possible for some or all.
`configuration.yaml`:

<details><summary>Click to show the binary sensor configuration example</summary>

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
</details>

Base on these sensors, a automation can be build for notifications or below conditional card can be defined:
<details><summary>Click to show the lovelace card example</summary>

```
- type: conditional
conditions:
  - entity: binary_sensor.bibliotheek_warning_7d
	state: 'on'
  - entity: binary_sensor.bibliotheek_alert_7d
	state: 'off'
card:
  type: markdown
  content: ???Boeken verlengen deze week !
- type: conditional
conditions:
  - entity: binary_sensor.bibliotheek_warning_7d
	state: 'on'
  - entity: binary_sensor.bibliotheek_alert_7d
	state: 'on'
card:
  type: markdown
  content: ???Boeken binnen brengen deze week !
```

</details>

### Example automation
Example automation that will automatically extend all items that have 7 or less days left before they need to be returned, whenever the days left is is below 6.

```
alias: Bibliotheek extend all verlengingen
description: ""
trigger:
  - platform: numeric_state
    entity_id: sensor.bibliotheek_be_warning
    below: 6
condition: []
action:
  - service: bibliotheek_be.extend_all_loans
    data:
      max_days_remaining: 7
  - service: notify.notify
    data:
      message: Al de boeken die konden verlengd worden, werden verlengd.
mode: single
```
