import socket
import json
from pathlib import Path

def find_free_port(start_port=8080, max_port=8200):
    """Find available port"""
    for port in range(start_port, max_port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                # Try to bind first, skip if it fails
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    raise Exception("No available ports found")

def get_port_config():
    """Get or create port configuration"""
    config_file = Path("port_config.json")

    # Always try to find available port to handle port conflicts
    backend_port = find_free_port()
    config = {
        "backend_port": backend_port,
        "frontend_url": f"http://localhost:5173"
    }

    # Save configuration (if possible)
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception:
        pass # Portable version might not be writable, ignore

    return config

def update_frontend_config(backend_port):
    """Update frontend configuration file"""
    config_content = f"""// Dynamic configuration - will be updated by the backend
window.API_BASE_URL = 'http://localhost:{backend_port}';
window.DYNAMIC_PORT_SUPPORT = true;
window.BACKEND_PORT = {backend_port};
"""

    config_file = Path("frontend/config.js")
    config_file.write_text(config_content)

if __name__ == "__main__":
    config = get_port_config()
    print(f"Backend port: {config['backend_port']}")
    print(f"Frontend URL: {config['frontend_url']}")
    update_frontend_config(config['backend_port'])
    print(f"Updated frontend config for port {config['backend_port']}")