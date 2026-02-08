[![HACS Default](https://img.shields.io/badge/HACS-Default-blue.svg)](https://github.com/hacs/default)
[![GitHub release](https://img.shields.io/github/release/myTselection/bibliotheek_be.svg)](https://github.com/myTselection/bibliotheek_be/releases)
![GitHub repo size](https://img.shields.io/github/repo-size/myTselection/bibliotheek_be.svg)

[![GitHub issues](https://img.shields.io/github/issues/myTselection/bibliotheek_be.svg)](https://github.com/myTselection/bibliotheek_be/issues)
[![GitHub last commit](https://img.shields.io/github/last-commit/myTselection/bibliotheek_be.svg)](https://github.com/myTselection/bibliotheek_be/commits/master)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/m/myTselection/bibliotheek_be.svg)](https://github.com/myTselection/bibliotheek_be/graphs/commit-activity)

# Bibliotheek.be Bib Home Assistant integration

[bibliotheek.be](https://www.bibliotheek.be/) Home Assistant custom component. It provides a clear overview of all items lended. Supporting accounts with different lendings at different libraries. Also supporting different users linked to a main account (eg parent and children).

An overview of all items per library or an overview of all items per user can be shown, see complex markdown examples below.

Based on the sensors, automations can be built to get warned: eg when little time is left to return an item and considering item extension in the library is not more possible.

By using the custom services available in this integration, the lendings can be extended automatically, which can be integrated in automations. For example: auto extend lending for all items which are to be returned within 5 days. Full info below.

| :warning: Please don't report issues with this integration to Bibliotheek.be, they will not be able to support you. |
| ------------------------------------------------------------------------------------------------------------------- |

<p align="center"><img src="https://raw.githubusercontent.com/myTselection/bibliotheek_be/master/icon_small.png"/></p>

## Installation

- [HACS](https://hacs.xyz/): search for the integration in the list of HACS
  - [![Open your Home Assistant instance and open the repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg?style=flat-square)](https://my.home-assistant.io/redirect/hacs_repository/?owner=myTselection&repository=bibliotheek_be&category=integration)
- Restart Home Assistant
- Add 'Bibliotheek.be' integration via HA Settings > 'Devices and Services' > 'Integrations'
- Provide Bibliotheek.be username and password

## Integration

Sensors `Bibliotheek.be` should become available with the number of items lent out.

- <details><summary><code>sensor.bibliotheek_be_[username]_[library]</code> will be created for each user linked to the account</summary>

  | Attribute               | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
  | ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
  | State                   | Number of loans by this user at this library                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
  | `userid `               | Technical user id assigned by bibliotheek.be                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
  | `barcode`               | The unique user barcode which is also shown on the library card                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
  | `barcode_url`           | Image url of the unique user barcode which is also shown on the library card                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
  | `num_loans`             | Number of loans by this user at this library (same as state value)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
  | `loans_url`             | URL for overview of loans by this user at this library                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
  | `num_reservations`      | Number of reservations by this user at this library                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
  | `reservations_url`      | URL for overview of reservations by this user at this library                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
  | `open_amounts`          | Open amount (€) due to this library (eg related to fines)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
  | `username`              | First and lastname of the user                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
  | `libraryName`           | Name of the library or the group of libraries                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
  | `isExpired`             | Boolean indication if the user account is expired at this library                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
  | `expirationDate`        | Date of expiration of the user account at this library                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
  | `isBlocked`             | Boolean indication if the user account is blocked at this library                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
  | `hasError`              | Boolean indication if the user account has an error at this library                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
  | `entity_picture`        | General picture for library sensor, eg used by HA when showing the sensor on a map                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
  | `name`                  | Name of the user at this library                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
  | `address`               | Address of the user                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
  | `id`                    | Unique technical id of the user at this library                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
  | `libraryUrl`            | Base url of this library                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
  | `mail`                  | Account email address of the user at this library                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
  | `userMail`              | User email address of the user at this library                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
  | `mailNotInSync`         | Boolean indication if the mail is not in sync at this library                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
  | `pendingValidationDate` | Date of pending validation of the user account at this library                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
  | `supportsOnlineRenewal` | Boolean indication if the user account supports online renewal at this library                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
  | `wasRecentlyAdded`      | Boolean indication if the user account was recently added at this library                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
  | `loandetails`           | Json containing all the loans of this user at this library. The structure of json is:<br/> `{ 'item name' :` <br/>&nbsp;`{ tile: 'title of the item',` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`author: 'author of the item', ` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`loan_type: 'type of the item (eg book, dvd, ...) , ` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`url: 'url of the specific item', ` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`image_src: 'url to image of the item', ` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`days_remaining: 'number of days by which the item has to be returned or extended', ` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`loan_from: 'Start date of the loan', ` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`loan_till: 'Date by which the item needs to be returned', ` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`extend_loan_id: 'the id used to extend the item, if no id is available, the item can not be extended',` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`library: 'name of the actual library location (city) where the item is belonging too',` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`user: 'the user that lended the item',` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`barcode: 'the barcode of the card that was used to lend the item' }` |

  </details>

- <details><summary><code>sensor.bibliotheek_be_bib_[library]</code> will be created for each library</summary>

  | Attribute             | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
  | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
  | State                 | Min days left by which some items need to be returned                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
  | `some_not_extendable` | True if some of the items that needs to be returned first (see state for nr of days) of this library can not be extended                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
  | `lowest_till_date`    | Min date by which some items need to be returned                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
  | `num_loans`           | Number of loans that need to be returned first (see state for nr of days)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
  | `num_loans_total`     | Total number of loans at this library                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
  | `loandetails`         | Json containing all the loans of this user at this library. The structure of json is:<br/> `[{ 'item name' :` <br/>&nbsp;`{ tile: 'title of the item',` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`author: 'author of the item', ` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`loan_type: 'type of the item (eg book, dvd, ...) , ` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`url: 'url of the specific item', ` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`image_src: 'url to image of the item', ` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`days_remaining: 'number of days by which the item has to be returned or extended', ` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`loan_from: 'Start date of the loan', ` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`loan_till: 'Date by which the item needs to be returned', ` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`extend_loan_id: 'the id used to extend the item, if no id is available, the item can not be extended',` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`library: 'name of the actual library location (city) where the item is belonging too',` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`user: 'the user that lended the item',` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`barcode: 'the barcode of the card that was used to lend the item' }]` |
  | <loan_type>           | Number of items of this loan type lended. For each loan type known this attribute will be added                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
  | address               | Street and city address details of the library                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
  | latitude              | GPS coordinates of the library, makes it possible to show the sensor on a map                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
  | longitude             | GPS coordinates of the library, makes it possible to show the sensor on a map                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
  | phone                 | Phone number of the library                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
  | email                 | Email address of the library                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
  | opening_hours         | Opening hours of the library                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
  | closed_date           | Closing days of the library with reason of closure                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |

  </details>

- <details><summary><code>sensor.bibliotheek_be_warning</code> will indicate within how many days some items have to be returned at *any* library (this can be used of conditions, notifications, etc).</summary>

  | Attribute             | Description                                                                                                              |
  | --------------------- | ------------------------------------------------------------------------------------------------------------------------ |
  | State                 | Min days left by which some items need to be returned by any user linked to the account at any library                   |
  | `some_not_extendable` | True if some of the items that needs to be returned first (see state for nr of days) of this library can not be extended |
  | `lowest_till_date`    | Min date by which some items need to be returned                                                                         |
  | `num_loans`           | Number of loans that need to be returned first (see state for nr of days)                                                |
  | `num_loans_total`     | Total number of loans by any user at any library                                                                         |
  | `library_name`        | Name(s) of the library at which some items need to be returned first (or comma spearated list of names)                  |

  </details>

- <details><summary><code>sensor.bibliotheek_be_list_[listname]</code> will be created for each list linked to the account</summary>

  | Attribute           | Description                                                                                                                                                                                                                             |
  | ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
  | State               | Number of items on the list                                                                                                                                                                                                             |
  | `List name `        | Technical user id assigned by bibliotheek.be                                                                                                                                                                                            |
  | `List ID`           | The unique user barcode which is also shown on the library card                                                                                                                                                                         |
  | `List URL`          | Image url of the unique user barcode which is also shown on the library card                                                                                                                                                            |
  | `List last changed` | Number of loans by this user at this library (same as state value)                                                                                                                                                                      |
  | `List items`        | Json containing all the items linked to the list. The structure of json is:<br/> `[{ tile: 'title of the item', ` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`author: 'author of the item', ` <br/>&nbsp;&nbsp;&nbsp;&nbsp;`url: 'url of the item }]` |

  </details>

Following services `bibliotheek_be` will be available:

- <details><summary><code>bibliotheek_be.extend_loan</code>: extend a single item, based on <code>extend_loan_id</code>, if the <code>days_remaining</code> is less than or equal the max set</summary>

  ```
  service: bibliotheek_be.extend_loan
  data:
    extend_loan_id: 12345678
    max_days_remaining: 8
  ```

  </details>

- <details><summary><code>bibliotheek_be.extend_loans_library</code>: extend all loans of a library that have <code>days_remaining</code> less than or equal the max set</summary>

  ```
  service: bibliotheek_be.extend_loans_library
  data:
    library_name: 'City'
    max_days_remaining: 8
  ```

  </details>

- <details><summary><code>bibliotheek_be.extend_loans_user</code>: extend all loans of a user that have <code>days_remaining</code> less than or equal the max set</summary>

  ```
  service: bibliotheek_be.extend_loan
  data:
    barcode: '1234567890123'
    max_days_remaining: 8
  ```

  </details>

- <details><summary><code>bibliotheek_be.extend_all_loans</code>: extend all loans that have <code>days_remaining</code> less than or equal the max set</summary>

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

All other files just contain boilerplate code for the integration to work within HA or to have some constants/strings/translations.

## Example usage:

### Markdown Example for details of all libraries

<p align="center"><img src="https://raw.githubusercontent.com/myTselection/bibliotheek_be/master/Markdown%20Card%20example.png" width="400"/></p>
<p align="center"><img src="https://raw.githubusercontent.com/myTselection/bibliotheek_be/master/Markdown%20Card%20details%20example.png" width="400"/></p>

<details><summary>Click to show the Mardown example</summary>

```
type: markdown
content: >-
  [<img
  src="https://raw.githubusercontent.com/myTselection/bibliotheek_be/master/icon_small_transp.png"
  style="max-width: 10%; height:
  auto;!important;">](https://beersel.bibliotheek.be)

  {% if state_attr('sensor.bibliotheek_be_warning','refresh_required') %}

  De gegevens moeten nog bijgewerkt worden!

  {% endif %}

  {% set libs = states
    | selectattr("entity_id","match","^sensor.bibliotheek_be_bib*")
    | rejectattr("state", "match","unavailable")
    | list %}

  {% set numeric = libs
    | rejectattr("state","eq","unknown")
    | list %}

  {% set unknown = libs
    | selectattr("state","eq","unknown")
    | list %}

  {# 1. Sort by numeric state (ascending) #} {% set numeric = numeric |
  sort(attribute="state") %}

  {# 2. Bring non-extendable (true) to the top #} {% set numeric = numeric |
  sort(attribute="attributes.some_not_extendable", reverse=true) %}

  {# 3. Combine — unknown always last #} {% set libraries = numeric + unknown %}

  {% for library_device in libraries %}
    {% set library = library_device.entity_id %}
    ## Bib {{state_attr(library,'libraryName') }}:
    {% set all_books = state_attr(library,'loandetails')| sort(attribute="isRenewable", reverse=False) | sort(attribute="days_remaining", reverse=False)  | list %}
    {% if all_books %}

    - {{state_attr(library,"num_loans") }} stuk{% if state_attr(library,'num_loans')|int > 1 %}s{% endif %} {%if state_attr(library,'some_not_extendable')%}**in te leveren** binnen{% else %}te verlengen in{% endif %} **{{states(library)}}** dag{% if states(library)|int > 1 %}en{% endif %}: {{strptime(state_attr(library,'lowest_till_date'), "%d/%m/%Y").strftime("%a %d/%m/%Y") }}

  <details><summary>Toon details:</summary>

  {% for book in all_books  %}  <details>

  <summary>{% if book.extend_loan_id %}{{ strptime(book.loan_till,
  "%d/%m/%Y").strftime("%a %d/%m/%Y") }}{% else %}<b>{{ strptime(book.loan_till,
  "%d/%m/%Y").strftime("%a %d/%m/%Y") }}</b>{% endif %}: {{ book.title}}{% if
  book.author != "-" %} ~ {{ book.author }}{% endif %}</summary>  <ul>
  <li>Binnen: {{ book.days_remaining }} dagen</li> <li>Verlenging: {% if
  book.extend_loan_id %}<a href="https://{{state_attr(library,'libraryName')
  }}.bibliotheek.be/mijn-bibliotheek/lidmaatschappen/{{book.userid}}/uitleningen/verlengen?loan-ids={{book.extend_loan_id}}"
  target="_blank">verlengbaar</a>{% else %}<b>Niet verlengbaar</b>{% endif
  %}</li> <li>Bibliotheek: <a href="{{book.url}}"
  target="_blank">{{book.library}}</a></li> <li>Gebruiker: <a
  href="https://barcodeapi.org/api/128/{{book.barcode}}">{{book.user}}
  ({{book.barcode}})</a></li> <li>Type: {% if book.loan_type == 'Unknown'
  %}Onbekend{% else %}{{book.loan_type}}{% endif %}</li> <br/><a
  href="{{book.url}}"><img src="{{ book.image_src }}" height="100"/></a> </ul>

  </details> {% endfor %} 
      
  </details>
    {% endif %}
    - <details><summary>In totaal {{state_attr(library,'num_total_loans') }} uitgeleend:</summary>
    
      - Boeken: {{state_attr(library,'Boek') }}
      - Onbekend: {{state_attr(library,'Unknown') }}
      - DVDs: {{state_attr(library,'Dvd') }}
      - Strips: {{state_attr(library,'Strip') }}
      
    </details>
    
    - <details><summary>Info Bib {{state_attr(library,'libraryName') }}</summary>


        - Url: {{state_attr(library,'url')}}
        - Adres: {{state_attr(library,'address')}}
        - GPS: [{{state_attr(library,'latitude')}},{{state_attr(library,'longitude')}}](http://maps.google.com/maps?daddr={{state_attr(library,'latitude')}},{{state_attr(library,'longitude')}}&ll=)
        - Tel: {{state_attr(library,'phone')}}
        - Email: {{state_attr(library,'email')}}
        - Openingsuren: 
           {% if state_attr(library,'opening_hours') %}
           
           {# --- compute which day to bold (server-side) --- #}
           {% set days = ['maandag','dinsdag','woensdag','donderdag','vrijdag','zaterdag','zondag'] %}
           {% set oh = state_attr(library,'opening_hours') %}
           {% set ns = namespace(bold=None) %}
           {# current server time (Home Assistant server timezone) #}
           {% set now_dt = now() %}
           {% set now_t = now_dt.time() %}

           {# iterate up to 7 days starting from today #}
           {% for offset in range(0,7) %}
             {% set idx = (now_dt.weekday() + offset) % 7 %}
             {% set day = days[idx] %}
             {% set intervals = [] %}
             {% if oh and day in oh %}
               {% set intervals = oh[day] %}
             {% endif %}
             {% if intervals | length > 0 %}
               {% if offset == 0 %}
                 {# check if now inside any interval today #}
                 {% for intr in intervals %}
                   {% set parts = intr.split('-') %}
                   {% set st = parts[0].strip() %}
                   {% set en = parts[1].strip() %}
                   {% if now_t >= strptime(st, "%H:%M").time() and now_t < strptime(en, "%H:%M").time() %}
                     {% set ns.bold = day %}
                     {% break %}
                   {% endif %}
                 {% endfor %}
                 {% if ns.bold is not none %}
                   {% break %}
                 {% endif %}
                 {# check if there is a later interval today #}
                 {% for intr in intervals %}
                   {% set st = intr.split('-')[0].strip() %}
                   {% if now_t < strptime(st, "%H:%M").time() %}
                     {% set ns.bold = day %}
                     {% break %}
                   {% endif %}
                 {% endfor %}
                 {% if ns.bold is not none %}
                   {% break %}
                 {% endif %}
               {% else %}
                 {# first future day with intervals -> bold it #}
                 {% set ns.bold = day %}
                 {% break %}
               {% endif %}
             {% endif %}
           {% endfor %}

           {# render openings, bolding ns.bold if set #}
           {% for key,value in oh.items() %}
           - {% if key == ns.bold %}**{{key}}**{% else %}{{key}}{% endif %}: {% if value %}{{ value | join(', ') }}{% else %}Gesloten{% endif %}
           {% endfor %}
           {% endif %}
        - Sluitingsdagen: 
           {% if state_attr(library,'closed_dates') %}
           {% for closed in state_attr(library,'closed_dates') %}
           -  {{closed.date}}: {{closed.reason}} 
           {% endfor %}
           {% endif %}
    {% endfor %}
  {% if libraries | count > 0 %} {% set first_library = libraries[0].entity_id
  %}

  Laatst bijgewerkt: {{ state_attr(first_library, 'last update') | as_timestamp
  | timestamp_custom("%d %h %H:%M") }} {% endif %}
    
  Automatische verlenging van boeken die binnen 5 dagen moeten ingeleverd
  worden.

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
  rejectattr("entity_id","match","^sensor.bibliotheek_be_list*")|
  rejectattr("entity_id","match","^sensor.bibliotheek_be_warning")|
  sort(attribute="state")|
   list%}

  {% for user_device in library_users %}

  {% set user = user_device.entity_id %}

  {% set loans = state_attr(user, 'loandetails') %} {% if loans %}

  <details><summary><b>{{state_attr(user,'username') }}
  {{state_attr(user,'libraryName') }}:</b></summary> <ul> <li>Kaart
  {{state_attr(user,'barcode') }} ({{state_attr(user,'barcode_spell')| join(',
  ') }}):<br/>
      <a href="{{state_attr(user,'barcode_url') }}"><img src="{{state_attr(user,'barcode_url') }}" height=100></img></a></li>
  <li>Account vervalt {{state_attr(user,'expirationDate')}}{% if
  state_attr(user,'isExpired') %} Vervallen{% endif %}{% if
  state_attr(user,'isBlocked') %} Geblokkeerd{% endif %}{% if
  state_attr(user,'hasError') %} Foutief{% endif %}</li> <li>Gereserveerde
  stuks: <a href="{{state_attr(user,'reservations_url')}}"
  target="_blank">{{state_attr(user,'num_reservations') }}</a></li>
  <li>Uitstaande boetes: {{state_attr(user,'open_amounts') }}</li> {% if
  state_attr(user,'num_loans') > 0 %} {% set all_books =
  state_attr(user,'loandetails') | sort(attribute="isRenewable", reverse=False)
  | sort(attribute="days_remaining", reverse=False)  |list %} <li>In totaal <a
  href="{{state_attr(user,'loans_url')}}"
  target="_blank">{{state_attr(user,'num_loans') }}</a> uitgeleend{% if
  all_books %} {% for book in all_books %}

  <details><summary>{% if book.isRenewable %}{{ strptime(book.dueDate,
  "%d/%m/%Y").strftime("%a %d/%m/%Y") }}{% else %}<b>{{ strptime(book.dueDate,
  "%d/%m/%Y").strftime("%a %d/%m/%Y") }}</b>{% endif %}: {{ book.title
  }}</summary>

  <ul> <li>Binnen: {{ book.days_remaining }} dagen</li> <li>Verlenging: {% if
  book.isRenewable %}<a href="{{book.renewUrl}}"
  target="_blank">verlengbaar</a>{% else %}<b>Niet verlengbaar</b>{% endif
  %}</li> <li>Bibliotheek: <a href="{{state_attr(user,'libraryUrl')}}"
  target="_blank">{{book.location.libraryName}}</a></li> </ul> </details> {%
  endfor %} {% endif %}</li> {% else %} <ul><li>Geen uitleningen</li></ul> {%
  endif %} Laatst bijgewerkt: {{state_attr(user,'last update')  | as_timestamp |
  timestamp_custom("%d-%m-%Y %H:%M")}} </details>

  {% endif %}

  {% endfor %}

  {% for user_device in library_users %}

  {% set user = user_device.entity_id %}

  {% if state_attr(user,'num_loans') == 0 %}

  <details><summary><b>{{state_attr(user,'username') }}
  {{state_attr(user,'libraryName') }}:</b></summary> <ul> <li>Kaart
  {{state_attr(user,'barcode') }} ({{state_attr(user,'barcode_spell')| join(',
  ') }}):<br/>
      <a href="{{state_attr(user,'barcode_url') }}"><img src="{{state_attr(user,'barcode_url') }}" height=100></img></a></li>
  <li>Account vervalt {{state_attr(user,'expirationDate')}}{% if
  state_attr(user,'isExpired') %} Vervallen{% endif %}{% if
  state_attr(user,'isBlocked') %} Geblokkeerd{% endif %}{% if
  state_attr(user,'hasError') %} Foutief{% endif %}</li> <li>Gereserveerde
  stuks: <a href="{{state_attr(user,'reservations_url')}}"
  target="_blank">{{state_attr(user,'num_reservations') }}</a></li>
  <li>Uitstaande boetes: {{state_attr(user,'open_amounts') }}</li> <li><a
  href="{{state_attr(user,'loans_url')}}" target="_blank">Geen
  uitleningen</a></ul> </ul> </details>

  {% endif %}

  {% endfor %}
title: Gebruikers


```

</details>

### Markdown Example for lists:

<details><summary>Click to show the Mardown example</summary>

```
type: markdown
content: >-
  {% set librarylists = states |
  selectattr("entity_id","match","^sensor.bibliotheek_be_list*") | list %}

  {% for librarylist_device in librarylists %}

  {% set librarylist = librarylist_device.entity_id %}


  <details><summary><a href="{{state_attr(librarylist,'list_url') }}" target="_blank">{{state_attr(librarylist,'list_name') }}</a> #{{states(librarylist) }}, Lijst laatst bijgewerkt {{state_attr(librarylist,'list_last_changed') }}:</summary>

  {% set all_books = state_attr(librarylist,'list_items') | list %}
    {% for book in all_books %}
    - <a href="{{book.url}}" target="_blank">{{ book.title }}{% if book.author != "-"%} ~ {{ book.author }}{% endif %}</a>
    {% endfor %}
  </details>

  {% endfor %}
title: Lijsten

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

### Example script to create a persistent notification for all books

<details><summary>When going to the library, I often want to make sure all books are packed. So I created a script that will make a persisten notification for each book lended. This way, when the book is added into our basket, the notification can easily be dismissed and remaining books can be searched.</summary>

```
alias: Boeken notificaties
sequence:
  - variables:
      libraries: >-
        {{states | selectattr("entity_id","match","^sensor.bibliotheek_be_bib*")
        | rejectattr("state", "match","unavailable") |
        map(attribute='entity_id') | list}}
  - repeat:
      for_each: "{{libraries}}"
      sequence:
        - variables:
            library: "{{repeat.item}}"
        - repeat:
            for_each: >-
              {{state_attr(library,'loandetails')| list
              |sort(attribute="days_remaining", reverse=True)| list}}
            sequence:
              - variables:
                  book: "{{repeat.item}}"
              - service: notify.persistent_notification
                data:
                  title: "{{book.title}} ~ {{book.author}}"
                  message: >-
                    {% if book.extend_loan_id == '' %}<b>Kan NIET verlengd
                    worden</b><br>{% endif %} {{ book.days_remaining }} dagen:
                    {{strptime(book.loan_till,'%d/%m/%Y').strftime('%a
                    %d/%m/%Y')}}<br> {{state_attr(library,'libraryName')}}
        - service: notify.persistent_notification
          data:
            title: "{{state_attr(library,'libraryName')}}"
            message: >-
              - Openingsuren: {% for key,value in
              state_attr(library,'opening_hours').items() %}
                  - {{key}}: {{value | join(',')}}{% if not value %}Gesloten{% endif %}{% endfor %}
              - Sluitingsdagen: {% for closed in
              state_attr(library,'closed_dates') %}
                  - {{closed.date}}: {{closed.reason}}{% endfor %}-
mode: single
icon: mdi:basket-check

```

</details>
