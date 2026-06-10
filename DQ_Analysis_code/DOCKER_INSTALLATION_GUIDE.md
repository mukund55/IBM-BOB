# Docker Installation Guide for Windows

## Download Docker Desktop for Windows

### Official Download Link:
**https://www.docker.com/products/docker-desktop/**

### Direct Download Link:
**https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe**

---

## System Requirements

### Windows 11 or Windows 10 (64-bit)
- Windows 10 version 21H2 or higher (Home, Pro, Enterprise, or Education)
- Windows 11 (any version)

### Hardware Requirements:
- 64-bit processor with Second Level Address Translation (SLAT)
- 4GB system RAM minimum (8GB recommended)
- BIOS-level hardware virtualization support must be enabled

### Required Windows Features:
- WSL 2 (Windows Subsystem for Linux 2)
- Hyper-V and Containers Windows features

---

## Installation Steps

### Step 1: Download Docker Desktop
1. Go to: **https://www.docker.com/products/docker-desktop/**
2. Click **"Download for Windows"**
3. Save the installer file: `Docker Desktop Installer.exe`

### Step 2: Run the Installer
1. Double-click `Docker Desktop Installer.exe`
2. Follow the installation wizard
3. **Important**: Make sure "Use WSL 2 instead of Hyper-V" is checked (recommended)
4. Click "OK" to proceed with installation

### Step 3: Restart Your Computer
After installation completes, restart your computer.

### Step 4: Start Docker Desktop
1. Launch Docker Desktop from Start Menu
2. Accept the Docker Subscription Service Agreement
3. Wait for Docker to start (you'll see the Docker icon in system tray)

### Step 5: Verify Installation
Open PowerShell and run:
```powershell
docker --version
docker-compose --version
```

You should see version information for both commands.

### Step 6: Test Docker
Run a test container:
```powershell
docker run hello-world
```

If you see "Hello from Docker!" message, installation is successful!

---

## Troubleshooting

### WSL 2 Installation Required
If Docker asks you to install WSL 2:

1. Open PowerShell as Administrator
2. Run:
```powershell
wsl --install
```
3. Restart your computer
4. Start Docker Desktop again

### Enable Virtualization in BIOS
If you get virtualization errors:

1. Restart computer and enter BIOS (usually F2, F10, or Del key during startup)
2. Find "Virtualization Technology" or "Intel VT-x" or "AMD-V"
3. Enable it
4. Save and exit BIOS
5. Start Docker Desktop

### Docker Desktop Won't Start
1. Open PowerShell as Administrator
2. Run:
```powershell
wsl --update
wsl --set-default-version 2
```
3. Restart Docker Desktop

---

## Alternative: Docker Desktop Download Links by Version

### Latest Stable Release:
- **Windows (x64)**: https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe
- **Windows (ARM64)**: https://desktop.docker.com/win/main/arm64/Docker%20Desktop%20Installer.exe

### Official Docker Hub:
- https://hub.docker.com/editions/community/docker-ce-desktop-windows

---

## After Installation - Next Steps

Once Docker is installed and running:

1. Navigate to your project directory:
```powershell
cd C:\Users\000QVU744\BoB\DQ_Analysis_code
```

2. Follow the PostgreSQL setup commands from `run_postgres_commands.md`

3. Start with:
```powershell
docker run -d --name postgres_dq_test -e POSTGRES_USER=dquser -e POSTGRES_PASSWORD=dqpass123 -e POSTGRES_DB=dq_database -p 5432:5432 postgres:15-alpine
```

---

## Useful Docker Desktop Features

### Docker Dashboard
- View running containers
- Start/Stop containers
- View logs
- Access container shell

### Settings
- Resources: Adjust CPU, Memory, Disk allocation
- Docker Engine: Advanced configuration
- Kubernetes: Enable if needed

---

## Quick Reference Commands

```powershell
# Check Docker status
docker info

# List running containers
docker ps

# List all containers
docker ps -a

# Stop a container
docker stop <container_name>

# Remove a container
docker rm <container_name>

# View container logs
docker logs <container_name>

# Execute command in container
docker exec -it <container_name> <command>
```

---

## Support Links

- **Docker Documentation**: https://docs.docker.com/desktop/install/windows-install/
- **Docker Community Forums**: https://forums.docker.com/
- **WSL 2 Documentation**: https://docs.microsoft.com/en-us/windows/wsl/install

---

## License Information

Docker Desktop is free for:
- Small businesses (fewer than 250 employees AND less than $10 million in annual revenue)
- Personal use
- Education
- Non-commercial open source projects

For larger organizations, a paid subscription may be required.