FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS base

# Stay as root initially to install and configure everything
USER root

# Set the working directory
WORKDIR /app

# Expose necessary ports
EXPOSE 8080

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

USER root

ENTRYPOINT ["dotnet", "RegistryService.dll"]


