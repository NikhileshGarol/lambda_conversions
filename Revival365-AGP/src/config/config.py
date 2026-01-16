# -*- coding: utf-8 -*-

import configparser
import os


class Config:
    def __init__(self, filename='config.ini'):
        base_path = os.path.dirname(__file__)
        config_path = os.path.join(base_path, filename)
        print(f"Attempting to read from: {config_path}")  # Debug print
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Unable to find the config.ini file at {config_path}")
        self.config = configparser.ConfigParser()
        self.config.read(config_path)


    def get(self, section, option):
        """Utility method to get configuration values"""
        return self.config.get(section, option)

    def get_database_config(self):
        """Retrieve database configuration as a dictionary."""
        return {
            'host': self.get('database', 'host'),
            'user': self.get('database', 'user'),
            'password': self.get('database', 'password'),
            'database': self.get('database', 'database')
        }

    def get_api_key(self):
        """Retrieve API key."""
        return self.get('api', 'api_key')

    def get_logging_config(self):
        """Retrieve logging configuration as a dictionary."""
        return {
            'log_file': self.get('logging', 'log_file'),
            'log_level': self.get('logging', 'log_level')
        }

    def get_time_classification(self):
        """Retrieve time classification settings."""
        return {
            'night_start': self.get('time_classification', 'night_start'),
            'night_end': self.get('time_classification', 'night_end'),
            'day_start': self.get('time_classification', 'day_start'),
            'day_end': self.get('time_classification', 'day_end')
        }
    

    def get_glucose_thresholds(self):
        """Retrieve glucose thresholds for shading."""
        return {
            'low_threshold': int(self.get('glucose_thresholds', 'low_threshold')),
            'high_threshold': int(self.get('glucose_thresholds', 'high_threshold'))
            }



# Define two colors for higher contrast background effect
colors = ['#a3c1da', '#cad2d3']  # Light gray and deep navy for higher contrast



# Instantiate the configuration to be used across the application
config = Config()
