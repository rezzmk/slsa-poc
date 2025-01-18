from flask import Flask, jsonify
import docker
import random
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('/app/logs/mtd.log')]
)
logger = logging.getLogger(__name__)

class MTDService:
    def __init__(self):
        self.client = docker.from_env()
        self.api = self.client.api
        self.port_range = range(8000, 9000)
        self.used_ports = set()
        self.project_name = "ssle-poc-114834"
        self.container_port = "8080"
        self.scheduler = BackgroundScheduler()
        self.setup_scheduler()

    def setup_scheduler(self):
        """Setup the scheduler for periodic rotations"""
        self.scheduler.add_job(
            self.scheduled_rotation,
            'interval',
            minutes=30,
            id='port_rotation'
        )
        self.scheduler.start()
        logger.info("Scheduler started - port rotation will occur every 30 minutes")

    def scheduled_rotation(self):
        """Handles scheduled rotation calls"""
        logger.info("Starting scheduled port rotation")
        try:
            results = self.rotate_container_ports()
            logger.info(f"Scheduled rotation completed: {results}")
        except Exception as e:
            logger.error(f"Scheduled rotation failed: {str(e)}")


    def get_random_port(self):
        """Get a random unused port."""
        while True:
            port = random.choice(list(self.port_range))
            try:
                # Test if we can bind to it
                test_container = self.client.containers.run(
                    "alpine",
                    "true",
                    ports={f"{port}/tcp": port},
                    detach=True,
                    remove=True
                )
                self.used_ports.add(port)
                return port
            except docker.errors.APIError:
                continue

    def rotate_container_ports(self):
        """Rotate ports for all web services."""
        services = ['dotnet-ws1', 'dotnet-ws2', 'dotnet-ws3']
        results = []

        for service_name in services:
            try:
                container_name = f"{self.project_name}-{service_name}-1"
                container = self.client.containers.get(container_name)

                # Generate new host port
                new_port = self.get_random_port()
                logger.info(f"Attempting to rotate {service_name} to port {new_port}")

                # Stop and remove old container
                container.stop()
                config = container.attrs
                old_port = config["HostConfig"]["PortBindings"].get(
                    f"{self.container_port}/tcp", [{}]
                )[0].get("HostPort", "unknown")
                container.remove()

                # Determine the existing network(s)
                network_names = list(config["NetworkSettings"]["Networks"].keys())
                main_network = network_names[0] if network_names else None

                # Build host config for port binding + restart policy
                host_config = self.api.create_host_config(
                    port_bindings={f"{self.container_port}/tcp": new_port},
                    restart_policy={"Name": "always"}
                )

                # Collect volume destinations (keys) for create_container's 'volumes' argument
                # The actual host -> container mapping is in host_config, so we just pass
                # the container’s mount points to 'volumes='.
                volumes = []
                for vol in config.get('Mounts', []):
                    volumes.append(vol['Destination'])

                # Create the new container (low-level API call)
                container_id = self.api.create_container(
                    image=container.image.tags[0],
                    name=container_name,
                    hostname=service_name,  # so it’s accessible as service_name:8080
                    environment=config.get('Config', {}).get('Env', []),
                    volumes=volumes,
                    host_config=host_config
                )["Id"]

                # Connect the new container to the same network with an alias
                if main_network:
                    self.api.connect_container_to_network(container_id, main_network, aliases=[service_name])

                # Finally, start the new container
                self.api.start(container_id)
                
                # Reload container object from the new ID
                new_container = self.client.containers.get(container_id)
                new_container.reload()

                # Confirm the mapped host port
                port_info = new_container.ports.get(f"{self.container_port}/tcp", [{}])
                actual_port = port_info[0].get("HostPort", "unknown")

                logger.info(f"Successfully rotated {service_name} from port {old_port} to {actual_port}")

                results.append({
                    "service": service_name,
                    "status": "success",
                    "old_port": old_port,
                    "new_port": actual_port
                })
            except Exception as e:
                logger.error(f"Failed to rotate {service_name}: {str(e)}")
                results.append({
                    "service": service_name,
                    "status": "failed",
                    "error": str(e)
                })

        return results

mtd_service = MTDService()

@app.route('/rotate', methods=['POST'])
def rotate_ports():
    try:
        results = mtd_service.rotate_container_ports()
        return jsonify({"status": "success", "results": results})
    except Exception as e:
        logger.error(f"Rotation failed: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/status', methods=['GET'])
def get_status():
    try:
        services = ['dotnet-ws1', 'dotnet-ws2', 'dotnet-ws3']
        status = []

        for service_name in services:
            try:
                container_name = f"{mtd_service.project_name}-{service_name}-1"
                container = mtd_service.client.containers.get(container_name)
                container.reload()

                port_info = container.ports.get(f"{mtd_service.container_port}/tcp", [])
                current_port = port_info[0]["HostPort"] if port_info else "unknown"

                status.append({
                    "service": service_name,
                    "current_port": current_port,
                    "status": "running" if container.status == "running" else container.status
                })
            except Exception as e:
                status.append({
                    "service": service_name,
                    "error": str(e)
                })

        return jsonify({"status": "success", "services": status})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/next-rotation', methods=['GET'])
def get_next_rotation():
    """Get time until next scheduled rotation"""
    try:
        job = mtd_service.scheduler.get_job('port_rotation')
        if job:
            next_run = job.next_run_time
            return jsonify({
                "status": "success",
                "next_rotation": next_run.isoformat() if next_run else None
            })
        return jsonify({"status": "error", "message": "No scheduled rotation found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)

