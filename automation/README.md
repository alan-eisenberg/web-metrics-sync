# ZAI Automation (Modular Scaffold)

This folder is a modular scaffold for the new automation architecture.

## Run tests

```bash
cd /home/alan/zai-automation/automation
python3 -m pytest -q
```

## Environment

Set secrets via environment variables (recommended):

```bash
export GROQ_API_KEY='your_groq_key'
export OPENVPN_PROFILES_DIR='/mnt/vault/Downloads/vpns'
export OPENVPN_USERNAME='your_openvpn_username'
export OPENVPN_PASSWORD='your_openvpn_password'
```

## Run stage tests (dry mock flow)

```bash
cd /home/alan/zai-automation/automation
python3 -m automation.main --stage vpn
python3 -m automation.main --stage mail
python3 -m automation.main --stage chat
python3 -m automation.main --stage full --keep-open
```

## Notes

- Current modules are safe mocks/stubs for architecture validation.
- `OPENVPN_PROFILES_DIR` defaults to `/mnt/vault/Downloads/vpns` if present.
- Next step is wiring real Selenium + OpenVPN + Groq calls into the module interfaces.
- Data files live under `automation/data/`.
