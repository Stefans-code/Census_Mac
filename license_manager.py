import jwt
import os
import hashlib
import platform
import subprocess
from datetime import datetime, timezone

class LicenseManager:
    """Gestione licenza offline di Census (stesse regole di Vocius/Datarium):
    JWT HS256 firmato, binding all'HWID della macchina, scadenza e
    revoca online opzionale via Supabase."""

    # Deve corrispondere a license_maker.py (modalità Census)
    LICENSE_SECRET = "census_offline_secure_key_2026_x99"
    ALGORITHM = "HS256"
    APP_NAME = "Census"
    LICENSE_EXT = ".census"

    def __init__(self):
        self.license_path = self._get_license_directory()

    def _get_license_directory(self):
        """Individua una cartella scrivibile persistente per la licenza."""
        system = platform.system()
        try:
            if system == "Windows":
                base = os.environ.get("LOCALAPPDATA", os.path.join(os.path.expanduser("~"), "AppData", "Local"))
                path = os.path.join(base, self.APP_NAME)
            elif system == "Darwin":  # macOS
                path = os.path.join(os.path.expanduser("~"), "Library", "Application Support", self.APP_NAME)
            else:  # Linux e altri
                path = os.path.join(os.path.expanduser("~"), ".census")

            os.makedirs(path, exist_ok=True)
            return os.path.join(path, "license" + self.LICENSE_EXT)
        except Exception:
            return "license" + self.LICENSE_EXT

    @staticmethod
    def get_hwid():
        """Genera un HWID unico e stabile per il PC (Windows, macOS o Linux)."""
        system = platform.system()
        try:
            if system == "Windows":
                # Primario: MachineGuid del registro
                import winreg
                registry = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
                key = winreg.OpenKey(registry, r"SOFTWARE\Microsoft\Cryptography")
                machine_guid, _ = winreg.QueryValueEx(key, "MachineGuid")
                winreg.CloseKey(key)

                # Secondario: seriale della scheda madre
                mb_serial = ""
                try:
                    cmd = "powershell -command \"(Get-CimInstance Win32_BaseBoard).SerialNumber\""
                    mb_serial = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=5).decode().strip()
                except Exception:
                    mb_serial = "STABLE-MB-ID"

                raw_id = f"{machine_guid}-{mb_serial}-CENSUS-SECURE"

            elif system == "Darwin":  # macOS
                try:
                    cmd = "ioreg -rd1 -c IOPlatformExpertDevice"
                    output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode()
                    serial = "MACOS-FALLBACK"
                    for line in output.splitlines():
                        if "IOPlatformSerialNumber" in line:
                            serial = line.split("=")[-1].replace('"', '').strip()
                            break
                except Exception:
                    serial = "MACOS-FALLBACK"
                raw_id = f"{serial}-APPLE-CENSUS-SECURE"

            else:  # Linux: machine-id stabile
                machine_id = ""
                for p in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
                    try:
                        with open(p) as f:
                            machine_id = f.read().strip()
                        if machine_id:
                            break
                    except Exception:
                        continue
                if not machine_id:
                    machine_id = f"{platform.node()}-{platform.processor()}"
                raw_id = f"{machine_id}-LINUX-CENSUS-SECURE"

            return hashlib.sha256(raw_id.encode()).hexdigest()[:16].upper()
        except Exception:
            import uuid
            fallback_id = f"{uuid.getnode()}-{platform.node()}-SECURE-FALLBACK"
            return hashlib.sha256(fallback_id.encode()).hexdigest()[:16].upper()

    def check_online_validation(self, hwid):
        """Controllo revoca centralizzato (Supabase), OPZIONALE perché le licenze
        Census sono offline e non sempre registrate nel DB.

        Ritorna:
          False -> SOLO se il DB contiene esplicitamente questo HWID come 'revoked'
          True  -> HWID trovato e attivo nel DB
          None  -> HWID sconosciuto / offline / DB non raggiungibile (decide la licenza locale)

        Differenza voluta rispetto a Datarium: un HWID *sconosciuto* NON viene
        trattato come revocato, altrimenti ogni licenza offline verrebbe bloccata."""
        import urllib.request
        import json

        apikey = ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhvb3dramVwdmJva3htaHNxbW5tIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY3NTI2NjUsImV4cCI6MjA5MjMyODY2NX0.2S_baIWot9ZkW7bsi16hy84O9Edf_XlBcQBmhXs3H1Y")
        base = "https://xoowkjepvbokxmhsqmnm.supabase.co"

        # Interroga la tabella per leggere lo stato ESPLICITO dell'HWID
        try:
            req = urllib.request.Request(
                f"{base}/rest/v1/licenses?hwid=eq.{hwid}&select=status",
                headers={"apikey": apikey, "Authorization": f"Bearer {apikey}"})
            with urllib.request.urlopen(req, timeout=3) as response:
                data = json.loads(response.read().decode())
                if isinstance(data, list) and data:
                    if any(item.get("status") == "revoked" for item in data):
                        return False
                    if any(item.get("status") == "active" for item in data):
                        return True
                # lista vuota = HWID non registrato (licenza offline) -> indecidibile online
        except Exception:
            pass
        return None

    def verify_license(self, token=None):
        """Verifica se la licenza è valida per questo hardware.
        Ritorna (bool, messaggio)."""
        current_hwid = self.get_hwid()

        # Revoca online ha priorità: se il DB dice 'revocata', elimina il file locale
        online_valid = self.check_online_validation(current_hwid)
        if online_valid is False:
            if os.path.exists(self.license_path):
                try: os.remove(self.license_path)
                except Exception: pass
            return False, "Licenza revocata o terminata"

        if not token:
            if os.path.exists(self.license_path):
                try:
                    with open(self.license_path, "r") as f:
                        token = f.read().strip()
                except Exception:
                    return False, "Errore lettura licenza"
            else:
                return False, "Licenza mancante"

        try:
            payload = jwt.decode(token, self.LICENSE_SECRET, algorithms=[self.ALGORITHM])

            if payload.get("hwid") != current_hwid:
                return False, f"Hardware ID non corrispondente (Locale: {current_hwid})"

            exp = datetime.fromtimestamp(payload['exp'], tz=timezone.utc)
            if exp < datetime.now(timezone.utc):
                return False, "Licenza scaduta"

            return True, f"Attiva (Scadenza: {exp.strftime('%d/%m/%Y')})"
        except jwt.ExpiredSignatureError:
            return False, "Licenza scaduta"
        except jwt.InvalidTokenError:
            return False, "Token non valido o corrotto"
        except Exception as e:
            return False, f"Verifica fallita: {str(e)}"

    def save_license(self, token):
        """Salva il token della licenza in un percorso scrivibile persistente."""
        try:
            with open(self.license_path, "w") as f:
                f.write(token)
            return True
        except Exception as e:
            print(f"Errore salvataggio licenza: {e}")
            return False
