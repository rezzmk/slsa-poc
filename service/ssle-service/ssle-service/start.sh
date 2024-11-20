#!/bin/bash

# Enable error reporting
set -e
#!/bin/bash

/var/ossec/bin/wazuh-control start

exec dotnet ssle-service.dll
