# API Monitoring tool
### Features:
```
1. Test APIs in the system once every 10 minutes ( The time can be changed )
2. If errors are found, error messages are generated
3. Send error messages to a designated email address in the config file
4. Send error messages to a designated Slack channel
```

### How to run:
```
1. Create a config file based on the config/config-template.ini file
2. Put the config file link in to the CONFIG_FILE variable in the monitor.py file
3. Create API routings for your system for the tool to test
3. Run monitor.py to test the system's API
```
