from flask import Flask, jsonify, request
import docker
import random
import logging
from datetime import datetime
import requests
from apscheduler.schedulers.background import BackgroundScheduler
import threading
import os

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/mtd.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BFTState:
    def __init__(self):
        self.promised_id = None
        self.accepted_id = None
        self.accepted_value = None
        self.proposal_count = 0
        self.lock = threading.Lock()
        self.prepare_responses = {}
        self.accept_responses = {}
        self.suspicious_nodes = set()
        self.message_history = {}

    def record_message(self, node_id, msg_type, message):
        """Record message for Byzantine detection"""
        if node_id not in self.message_history:
            self.message_history[node_id] = []
        self.message_history[node_id].append((msg_type, message))

    def check_byzantine_behavior(self, node_id):
        """Check if a node shows Byzantine behavior"""
        if node_id not in self.message_history:
            return False
        
        messages = self.message_history[node_id]
        # Check for conflicting messages in the last round
        for i in range(len(messages)):
            for j in range(i + 1, len(messages)):
                if self._are_messages_conflicting(messages[i], messages[j]):
                    logger.warning(f"Node {node_id} showed Byzantine behavior: conflicting messages")
                    return True
        return False

    def _are_messages_conflicting(self, msg1, msg2):
        """Check if two messages conflict"""
        type1, content1 = msg1
        type2, content2 = msg2
        
        if type1 == type2 == 'prepare':
            return (content1.get('proposal_id') == content2.get('proposal_id') and
                   content1.get('status') != content2.get('status'))
        elif type1 == type2 == 'accept':
            return (content1.get('proposal_id') == content2.get('proposal_id') and
                   content1.get('value') != content2.get('value'))
        return False

class MTDService:
    def __init__(self):
        self.client = docker.from_env()
        self.api = self.client.api
        self.port_range = range(8000, 9000)
        self.used_ports = set()
        self.project_name = "ssle-poc-114834"
        self.container_port = "8080"
        
        # BFT-related attributes
        self.node_id = os.environ['NODE_ID']
        self.other_nodes = os.environ['OTHER_NODES'].split(',')
        self.bft_state = BFTState()
        self.is_malicious = os.environ.get('MALICIOUS', '0').lower() == '1'
        
        if self.is_malicious:
            logger.info("🦹 Running as malicious node")
        
        # Initialize scheduler after delay
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(
            self.setup_scheduler,
            'date',
            run_date=datetime.now().replace(second=0, microsecond=0)
        )
        self.scheduler.start()
        logger.info(f"MTD Node {self.node_id} initialized")

    def setup_scheduler(self):
        """Setup the scheduler for periodic rotations"""
        self.scheduler.add_job(
            self.initiate_rotation,
            'interval',
            minutes=30,
            id='port_rotation'
        )
        logger.info("Scheduler started - port rotation will occur every 30 minutes")

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

    def prepare(self, proposal_id):
        """Phase 1a: Handle prepare request"""
        with self.bft_state.lock:
            logger.info(f"Received prepare request with proposal {proposal_id}")
            
            if self.is_malicious and random.random() < 0.5:
                logger.info("🦹 Sending malicious prepare response")
                response = {
                    "node_id": self.node_id,
                    "status": "promise",
                    "proposal_id": proposal_id,
                    "accepted_id": None,
                    "accepted_value": self.get_random_port()  # Lie about the port
                }
            else:
                response = {
                    "node_id": self.node_id,
                    "proposal_id": proposal_id,
                    "status": "reject"
                }
                if not self.bft_state.promised_id or proposal_id > self.bft_state.promised_id:
                    self.bft_state.promised_id = proposal_id
                    response.update({
                        "status": "promise",
                        "accepted_id": self.bft_state.accepted_id,
                        "accepted_value": self.bft_state.accepted_value
                    })
            
            self.bft_state.record_message(self.node_id, 'prepare', response)
            return response

    def accept(self, proposal_id, value):
        """Phase 2a: Handle accept request"""
        with self.bft_state.lock:
            logger.info(f"Received accept request for proposal {proposal_id}")
            
            if self.is_malicious and random.random() < 0.5:
                logger.info("🦹 Sending malicious accept response")
                response = {
                    "node_id": self.node_id,
                    "status": "accepted",
                    "proposal_id": proposal_id,
                    "value": self.get_random_port()  # Accept different port
                }
            else:
                response = {
                    "node_id": self.node_id,
                    "proposal_id": proposal_id,
                    "status": "reject"
                }
                if not self.bft_state.promised_id or proposal_id >= self.bft_state.promised_id:
                    self.bft_state.promised_id = proposal_id
                    self.bft_state.accepted_id = proposal_id
                    self.bft_state.accepted_value = value
                    response.update({
                        "status": "accepted",
                        "value": value
                    })
            
            self.bft_state.record_message(self.node_id, 'accept', response)
            return response

    def initiate_rotation(self):
        """Initiate a port rotation with consensus"""
        logger.info("Starting consensus-based port rotation")
        
        # Generate new port assignments
        services = ['dotnet-ws1', 'dotnet-ws2', 'dotnet-ws3']
        new_assignments = {}
        for service in services:
            new_port = self.get_random_port()
            new_assignments[service] = new_port

        # Get consensus on these assignments
        success, result = self.propose_port_changes(new_assignments)
        if success:
            logger.info(f"Consensus reached for port assignments: {result}")
            return self.execute_rotation(result)
        else:
            logger.error(f"Failed to reach consensus: {result}")
            return []

    def propose_port_changes(self, port_assignments):
        """Run Byzantine fault tolerant consensus for new port assignments"""
        proposal_id = f"{self.bft_state.proposal_count}.{self.node_id}"
        self.bft_state.proposal_count += 1
        logger.info(f"Proposing port changes with ID {proposal_id}")
        
        prepare_responses = {}
        accept_responses = {}
        suspicious_nodes = set()
        
        # We need 2f+1 responses where f is max faulty nodes
        required_responses = (len(self.other_nodes) * 2 + 1) // 3
        
        # Phase 1: Prepare
        for node in self.other_nodes:
            try:
                response = requests.post(f"{node}/prepare", 
                    json={"proposal_id": proposal_id},
                    timeout=5
                ).json()
                
                node_id = response.get('node_id')
                prepare_responses[node_id] = response
                
                # Check for Byzantine behavior
                self.bft_state.record_message(node_id, 'prepare', response)
                if self.bft_state.check_byzantine_behavior(node_id):
                    suspicious_nodes.add(node_id)
                    
            except requests.RequestException as e:
                logger.error(f"Failed to send prepare to {node}: {e}")

        # Filter out suspicious nodes
        valid_prepares = {k: v for k, v in prepare_responses.items() 
                         if k not in suspicious_nodes and v['status'] == 'promise'}
        
        if len(valid_prepares) < required_responses:
            return False, "Failed to get enough valid prepare responses"

        # Get highest accepted value
        highest_accepted = None
        for response in valid_prepares.values():
            if response.get('accepted_id'):
                if not highest_accepted or response['accepted_id'] > highest_accepted['accepted_id']:
                    highest_accepted = response

        # Phase 2: Accept
        value_to_propose = highest_accepted['accepted_value'] if highest_accepted else port_assignments
        
        for node in self.other_nodes:
            try:
                response = requests.post(f"{node}/accept", 
                    json={
                        "proposal_id": proposal_id,
                        "value": value_to_propose
                    },
                    timeout=5
                ).json()
                
                node_id = response.get('node_id')
                accept_responses[node_id] = response
                
                # Check for Byzantine behavior
                self.bft_state.record_message(node_id, 'accept', response)
                if self.bft_state.check_byzantine_behavior(node_id):
                    suspicious_nodes.add(node_id)
                    
            except requests.RequestException as e:
                logger.error(f"Failed to send accept to {node}: {e}")

        # Filter out suspicious nodes
        valid_accepts = {k: v for k, v in accept_responses.items() 
                        if k not in suspicious_nodes and v['status'] == 'accepted'}
        
        if len(valid_accepts) < required_responses:
            return False, "Failed to get enough valid accept responses"

        if suspicious_nodes:
            logger.warning(f"Detected potentially Byzantine nodes: {suspicious_nodes}")

        logger.info(f"BFT consensus reached for proposal {proposal_id}")
        return True, value_to_propose

    def execute_rotation(self, port_assignments):
        """Execute the agreed-upon port changes"""
        results = []
        for service_name, new_port in port_assignments.items():
            try:
                container_name = f"{self.project_name}-{service_name}-1"
                container = self.client.containers.get(container_name)

                logger.info(f"Rotating {service_name} to port {new_port}")

                # Stop and remove old container
                container.stop()
                config = container.attrs
                old_port = config["HostConfig"]["PortBindings"].get(
                    f"{self.container_port}/tcp", [{}]
                )[0].get("HostPort", "unknown")
                container.remove()

                # Get network info
                network_names = list(config["NetworkSettings"]["Networks"].keys())
                main_network = network_names[0] if network_names else None

                # Create new container
                host_config = self.api.create_host_config(
                    port_bindings={f"{self.container_port}/tcp": new_port},
                    restart_policy={"Name": "always"}
                )

                volumes = []
                for vol in config.get('Mounts', []):
                    volumes.append(vol['Destination'])

                container_id = self.api.create_container(
                    image=container.image.tags[0],
                    name=container_name,
                    hostname=service_name,
                    environment=config.get('Config', {}).get('Env', []),
                    volumes=volumes,
                    host_config=host_config
                )["Id"]

                if main_network:
                    self.api.connect_container_to_network(
                        container_id, 
                        main_network, 
                        aliases=[service_name]
                    )

                self.api.start(container_id)
                
                new_container = self.client.containers.get(container_id)
                new_container.reload()

                results.append({
                    "service": service_name,
                    "status": "success",
                    "old_port": old_port,
                    "new_port": new_port
                })

            except Exception as e:
                logger.error(f"Failed to rotate {service_name}: {e}")
                results.append({
                    "service": service_name,
                    "status": "failed",
                    "error": str(e)
                })

        return results

mtd_service = MTDService()

@app.route('/prepare', methods=['POST'])
def prepare():
    data = request.get_json()
    result = mtd_service.prepare(data['proposal_id'])
    return jsonify(result)

@app.route('/accept', methods=['POST'])
def accept():
    data = request.get_json()
    result = mtd_service.accept(data['proposal_id'], data['value'])
    return jsonify(result)

@app.route('/rotate', methods=['POST'])
def rotate_ports():
    try:
        results = mtd_service.initiate_rotation()
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

@app.route('/suspicious', methods=['GET'])
def get_suspicious_nodes():
    """Get list of nodes showing Byzantine behavior"""
    return jsonify({
        "status": "success",
        "suspicious_nodes": list(mtd_service.bft_state.suspicious_nodes),
        "is_malicious": mtd_service.is_malicious,
        "node_id": mtd_service.node_id
    })

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
