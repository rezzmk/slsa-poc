# Stage 1: Base Image with Wazuh Agent Installed
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS base

# Stay as root initially to install and configure everything
USER root

# Install Wazuh agent dependencies and other necessary packages
RUN apt-get update && apt-get install -y \
    sudo \
    curl \
    gnupg \
    apt-transport-https \
    lsb-release \
    procps \
    netcat-traditional \
    jq \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Add Wazuh GPG key and repository
RUN curl -s https://packages.wazuh.com/key/GPG-KEY-WAZUH | apt-key add - && \
    echo "deb https://packages.wazuh.com/4.x/apt/ stable main" > /etc/apt/sources.list.d/wazuh.list

# Install Wazuh agent
RUN apt-get update && apt-get install -y wazuh-agent && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Expose necessary ports
EXPOSE 8080
EXPOSE 8081

# Stage 2: Build the Application
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
ARG BUILD_CONFIGURATION=Release
WORKDIR /src

# Copy project files and restore dependencies
COPY *.csproj ./
RUN dotnet restore

# Copy the remaining source code and build the application
COPY . .
RUN dotnet build -c $BUILD_CONFIGURATION -o /app/build

# Stage 3: Publish the Application
FROM build AS publish
ARG BUILD_CONFIGURATION=Release
RUN dotnet publish -c $BUILD_CONFIGURATION -o /app/publish /p:UseAppHost=false

# Stage 4: Final Image with Application and Wazuh Agent
FROM base AS final
WORKDIR /app

# Copy the published application into the container
COPY --from=publish /app/publish .

# Create logs directory
RUN mkdir -p /app/logs

# Copy Wazuh configuration and scripts
COPY ossec.conf /var/ossec/etc/ossec.conf
COPY internal_options.conf /var/ossec/etc/local_internal_options.conf
COPY start.sh .

# Fix line endings and make scripts executable
RUN dos2unix start.sh && \
    chmod +x start.sh

# Switch to root user to run Wazuh agent (if necessary)
USER root

# Set the entrypoint to start both Wazuh agent and your application
ENTRYPOINT ["./start.sh"]

