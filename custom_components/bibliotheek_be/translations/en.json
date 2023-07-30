{
    "config": {
        "step": {
            "user": {
                "description": "Setup a Bibliotheek.be sensor, username and password are required.",
                "data": {
                    "username": "Username",
                    "password": "Password"
                }
            },
            "edit": {
                "description": "Setup a Bibliotheek.be sensor, username and password are required.",
                "data": {
                    "username": "Username",
                    "password": "Password"
                }
            }

        },
        "error": {
            "missing username": "Please provide a valid username",
            "missing password": "Please provide a valid password",
            "missing data options handler": "Option handler failed",
            "no_valid_settings": "No valid settings, provide username, password in ha config."
        }
    },
    "options": {
        "step": {
            "edit": {
                "description": "Setup a Bibliotheek.be sensor, username and password are required.",
                "data": {
                    "username": "Username",
                    "password": "Password"
                }
            }
        },
        "error": {
            "missing username": "Please provide a valid username",
            "missing password": "Please provide a valid password",
            "missing data options handler": "Option handler failed",
            "no_valid_settings": "No valid settings, provide username, password in ha config."
        }
    },
    "services": {
        "extend_loan": {
            "name": "extend_loan",
            "description": "Request an extention of a loan for a specific item if the days_remaining is less than or equal max_days_remaining. Please note some loans which have no extende_loan_id can not be extended.",
            "fields": {
                "extend_loan_id": {
                    "name": "extend_loan_id",
                    "description": "The library extention id"
                },
                "max_days_remaining": {
                    "name": "max_days_remaining",
                    "description": "Only extend the loan if the days remaining is below this maximum"
                }
            }

        }, 
        "extend_loans_library": {
            "name": "extend_loans_library",
            "description": "Request an extention of a all the loans for a library for which the days_remaining is less than or equal max_days_remaining. Please note some loans which have no extende_loan_id can not be extended.",
            "fields": {
                "library_name": {
                    "name": "library_name",
                    "description": "The name of the library"
                },
                "max_days_remaining": {
                    "name": "max_days_remaining",
                    "description": "Only extend the loan if the days remaining is below this maximum"
                }
            }

        }, 
        "extend_loans_user": {
            "name": "extend_loans_user",
            "description": "Request an extention of a all the loans for a user for which the days_remaining is less than or equal max_days_remaining. Please note some loans which have no extende_loan_id can not be extended.",
            "fields": {
                "barcode": {
                    "name": "barcode",
                    "description": "The barcode of the user"
                },
                "max_days_remaining": {
                    "name": "max_days_remaining",
                    "description": "Only extend the loan if the days remaining is below this maximum"
                }
            }

        }, 
        "extend_all_loans": {
            "name": "extend_all_loans",
            "description": "Request an extention of a all the loans for all users for which the days_remaining is less than or equal max_days_remaining. Please note some loans which have no extende_loan_id can not be extended.",
            "fields": {
                "max_days_remaining": {
                    "name": "max_days_remaining",
                    "description": "Only extend the loan if the days remaining is below this maximum"
                }
            }

        }, 
        "update": {
            "name": "update",
            "description": "Force an update of the sensor data (standard updates are throttled per hour)."
        }

    }
}