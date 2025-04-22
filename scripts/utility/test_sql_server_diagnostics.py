import subprocess
import socket
import pyodbc

def check_sql_server_service_status():
    try:
        result = subprocess.run(["sc", "query", "MSSQL$SQLEXPRESS"], capture_output=True, text=True)
        if "RUNNING" in result.stdout:
            return "✅ SQL Server (SQLEXPRESS) is running"
        else:
            return "❌ SQL Server (SQLEXPRESS) is NOT running"
    except Exception as e:
        return f"⚠️ Error checking SQL Server service: {e}"

def check_sql_server_tcp_ip_enabled():
    try:
        result = subprocess.run(
            ["reg", "query", r"HKLM\SOFTWARE\Microsoft\Microsoft SQL Server\MSSQL16.SQLEXPRESS\MSSQLServer\SuperSocketNetLib\Tcp"],
            capture_output=True,
            text=True
        )
        print("🔍 Raw Registry Output:\n", result.stdout)  # Debug print
        if "Enabled" in result.stdout:
            return "✅ TCP/IP appears enabled in registry"
        else:
            return "❌ TCP/IP not detected in registry for SQLEXPRESS"
    except Exception as e:
        return f"⚠️ Error checking TCP/IP status: {e}"

def check_sql_server_port(port=1433):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=3):
            return f"✅ Port {port} is reachable on localhost"
    except socket.error as e:
        return f"❌ Port {port} is NOT reachable: {e}"

def try_odbc_connection():
    try:
        conn = pyodbc.connect(
            r"DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost,1433;DATABASE=CreditSpreadsDB;Trusted_Connection=yes;",
            timeout=5
        )
        conn.autocommit = True
        result = conn.cursor().execute("SELECT GETDATE()").fetchone()
        return f"✅ ODBC connection succeeded. Server time: {result[0]}"
    except Exception as e:
        return f"❌ pyodbc connection failed: {e}"

# Run all checks
checks = [
    check_sql_server_service_status(),
    check_sql_server_tcp_ip_enabled(),
    check_sql_server_port(),
    try_odbc_connection()
]

print("\n🧪 SQL Server Diagnostic Results\n" + "-" * 40)
for check in checks:
    print(check)
