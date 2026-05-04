packer {
  required_plugins {
    docker = {
      version = ">= 1.0.8"
      source  = "github.com/hashicorp/docker"
    }
  }
}

source "docker" "ubuntu" {
  image  = "nikolaik/python-nodejs:python3.11-nodejs20"
  commit = true
  changes = [
    "ENV PATH=/app/.venv/bin:$PATH",
    "WORKDIR /app",
    "ENTRYPOINT [\"python\", \"-m\", \"uvicorn\", \"app.main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]"
  ]
}

build {
  name    = "free-ai-gateway"
  sources = [
    "source.docker.ubuntu"
  ]

  # Create necessary directories
  provisioner "shell" {
    inline = [
      "mkdir -p /app/ui"
    ]
  }

  # Copy files
  provisioner "file" {
    source      = "./ui/package.json"
    destination = "/app/ui/package.json"
  }

  provisioner "file" {
    source      = "./ui/package-lock.json"
    destination = "/app/ui/package-lock.json"
  }

  provisioner "file" {
    source      = "./ui/"
    destination = "/app/ui/"
  }

  provisioner "file" {
    source      = "./app/"
    destination = "/app/app/"
  }

  provisioner "file" {
    source      = "./requirements.txt"
    destination = "/app/requirements.txt"
  }

  # Build UI and install Python dependencies
  provisioner "shell" {
    inline = [
      "cd /app/ui",
      "npm install",
      "npm run build",
      "cd /app",
      "pip install --no-cache-dir -r requirements.txt"
    ]
  }
}
