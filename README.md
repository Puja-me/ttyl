# 🗨️ TTYL - Talk To You Later

**A secure, feature-rich real-time chat application built with Python**

*Developed under the PacketVSocket SMP of Cipher SIG, IET NITK*

---

## 📋 Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Commands](#commands)
- [Security](#security)
- [Database Schema](#database-schema)
- [Contributing](#contributing)
- [License](#license)

---

## 🌟 Overview

TTYL is a lightweight, secure client-server chat application that enables real-time messaging between multiple users over a network. Built with Python's socket programming and enhanced with encryption capabilities, it provides both public chat rooms and private messaging functionality with comprehensive admin controls.

## ✨ Features

### 🔐 Security & Encryption
- **End-to-end encryption** for private messages using Fernet (AES 128)
- **Public message encryption** with shared keys
- **SSL/TLS database connections** for secure logging

### 💬 Communication
- **Public chat room** for all connected users
- **Private messaging** between individual users
- **Real-time message delivery** with TCP reliability
- **Username change** functionality during chat sessions

### 👥 User Management
- **Automatic username conflict resolution** with suffix generation
- **Online user list** retrieval
- **User reporting system** for moderation
- **Graceful connection handling** and cleanup

### 🛡️ Administrative Controls
- **Multi-admin support** with promotion/demotion
- **User kicking** with temporary removal
- **User banning** with permanent restrictions
- **Admin-only command restrictions**
- **Comprehensive audit logging**

### 📊 Logging & Monitoring
- **MySQL database integration** for persistent logging
- **Event tracking** (connections, admin actions, reports)
- **Local file backup** logging system
- **Timestamp tracking** for all activities

---

## 🏗️ Architecture

```
┌─────────────────┐    TCP/IP Socket    ┌─────────────────┐
│                 │◄──────────────────►│                 │
│  Client (N)     │    Encrypted Msgs   │  Server         │
│  - client.py    │                     │  - server.py    │
│  - Commands     │                     │  - Threading    │
│  - Encryption   │                     │  - User Mgmt    │
└─────────────────┘                     └─────────────────┘
                                                 │
                                                 │
                                        ┌─────────────────┐
                                        │  MySQL Database │
                                        │  - Chat Logs    │
                                        │  - Audit Trail  │
                                        └─────────────────┘
```

---

## 📋 Prerequisites

- **Python 3.7+**
- **MySQL Server** (or Aiven MySQL service)
- **Required Python packages:**
  ```bash
  pip install cryptography mysql-connector-python
  ```

---

## 🚀 Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd ttyl-chat
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up the database:**
   ```sql
   CREATE DATABASE ttyl;
   USE ttyl;
   
   CREATE TABLE chat_logs (
       id INT AUTO_INCREMENT PRIMARY KEY,
       timestamp DATETIME NOT NULL,
       event_type VARCHAR(50) NOT NULL,
       username VARCHAR(100) NOT NULL,
       target_user VARCHAR(100),
       ip_address VARCHAR(45),
       details TEXT,
       is_admin_action BOOLEAN DEFAULT FALSE
   );
   ```

4. **Configure database connection** (see Configuration section)

---

## ⚙️ Configuration

### Database Configuration
Edit the database connection parameters in `server.py`:

```python
def connect_db(self):
    return mysql.connector.connect(
        host="your-mysql-host",
        port=3306,  # or your custom port
        user="your-username",
        password="your-password",
        database="ttyl",
        ssl_ca="/path/to/ca.pem",  # if using SSL
        ssl_verify_cert=True
    )
```

### Network Configuration
Modify connection settings in both `client.py` and `server.py`:

```python
HOST = '127.0.0.1'  # Change to your server IP for LAN/WAN access
PORT = 7423         # Custom port (ensure it's open in firewall)
```

### Security Keys
**⚠️ Important:** Change the default encryption keys before production use:

```python
# In client.py - Generate new keys using:
# from cryptography.fernet import Fernet
# key = Fernet.generate_key()

public_key = b'your-new-public-key-here'
key = b'your-new-private-key-here'
```

---

## 🎮 Usage

### Starting the Server
```bash
python server.py
```
The server will start listening on the configured HOST and PORT.

### Connecting Clients
```bash
python client.py
```
Enter a username when prompted. If the username exists, a unique suffix will be automatically added.

### Basic Chat Flow
1. **Connect** to the server
2. **Enter username** (automatic conflict resolution)
3. **Start chatting** in the public room
4. **Use commands** for additional features (see Commands section)

---

## 🔧 Commands

### 👤 User Commands
| Command | Syntax | Description |
|---------|--------|-------------|
| `/users` | `/users` | List all online users |
| `/private` | `/private username message` | Send encrypted private message |
| `/change_name` | `/change_name new_username` | Change your username |
| `/report` | `/report username` | Report a user to admins |
| `/exit` | `/exit` | Leave the chat safely |

### 🛡️ Admin Commands
| Command | Syntax | Description |
|---------|--------|-------------|
| `/kick` | `/kick username` | Temporarily remove user |
| `/ban` | `/ban username` | Permanently ban user |
| `/unban` | `/unban username` | Remove ban from user |
| `/admin` | `/admin username` | Promote user to admin |
| `/demote` | `/demote` | Demote yourself from admin |

### 📝 Command Examples
```bash
# Public message
Hello everyone!

# Private message
/private john Hey, how are you?

# Administrative action
/kick spammer

# User management
/admin trusted_user
```

---

## 🔒 Security

### Encryption Details
- **Private Messages:** AES-128 encryption via Fernet
- **Public Messages:** Shared key encryption for basic obfuscation
- **Database:** SSL/TLS encrypted connections

### Security Best Practices
1. **Change default encryption keys** before deployment
2. **Use strong passwords** for database connections
3. **Enable SSL certificates** for production databases
4. **Regularly rotate encryption keys**
5. **Monitor admin actions** through database logs

### Known Security Considerations
- Shared public key visible in source code (obfuscation only)
- No user authentication system (username-based only)
- Admin privileges not persistent across restarts

---

## 🗄️ Database Schema

### chat_logs Table
```sql
CREATE TABLE chat_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    username VARCHAR(100) NOT NULL,
    target_user VARCHAR(100),
    ip_address VARCHAR(45),
    details TEXT,
    is_admin_action BOOLEAN DEFAULT FALSE
);
```

### Logged Events
- `CONNECT` - User connections
- `ADMIN_ACTION` - Administrative commands
- `DISCONNECT` - User disconnections
- `REPORT` - User reports

---

## 📁 Project Structure

```
ttyl-chat/
├── client.py          # Client application
├── server.py          # Server application
├── config.py          # Configuration file
├── README.md          # This file
├── requirements.txt   # Python dependencies
└── chat_server.log    # Local log file (generated)
```

---

## 🔧 Troubleshooting

### Common Issues

**Connection Refused:**
- Check if server is running
- Verify HOST and PORT settings
- Check firewall settings

**Database Connection Error:**
- Verify database credentials
- Check SSL certificate path
- Ensure database exists

**Encryption Errors:**
- Verify matching keys between client/server
- Check for corrupted key formats

**Username Conflicts:**
- Automatic suffix resolution should handle this
- Check for special characters in usernames

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add comments for complex logic
- Test with multiple clients
- Update documentation for new features

---

## 📈 Future Enhancements

- [ ] User authentication system
- [ ] File transfer capabilities
- [ ] Chat history persistence
- [ ] Web-based client interface
- [ ] Voice message support
- [ ] Group chat rooms
- [ ] Message reactions and emojis
- [ ] Rate limiting and spam protection

---

## 📜 License

This project is developed under the **PacketVSocket SMP** of **Cipher SIG, IET NITK**.

---

## 👨‍💻 Authors

**PacketVSocket SMP Team**  
*Cipher SIG, IET NITK*

---

## 📞 Support

For issues, questions, or contributions, please:
- Open an issue on GitHub
- Contact the development team
- Check the troubleshooting section above

---

**Happy Chatting! 🎉**

*TTYL - Where conversations come alive!*
