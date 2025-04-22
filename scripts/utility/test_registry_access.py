import winreg
import sys

def read_registry_key():
    try:
        # Define registry path and hive
        hive = winreg.HKEY_LOCAL_MACHINE
        path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"

        # Open the registry key
        with winreg.OpenKey(hive, path, 0, winreg.KEY_READ) as key:
            print("✅ Successfully opened registry key.\n")

            # Read and print values
            index = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, index)
                    print(f"{name}: {value}")
                    index += 1
                except OSError:
                    break

    except PermissionError:
        print("❌ PermissionError: Insufficient rights to read the registry key.")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ FileNotFoundError: Registry key not found.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🔍 Testing registry access to 'HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion'...\n")
    read_registry_key()
