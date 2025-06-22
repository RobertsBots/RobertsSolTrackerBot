# RobertsSolTrackerBot (Webhook-Modell)

## Anleitung:
1. Setze die Environment Variables in Railway:
   - `BOT_TOKEN`
   - `CHANNEL_ID`

2. Stelle sicher, dass Port 8080 verwendet wird (wird im Railway automatisch erkannt).

3. Die Domain (z. B. `https://robertssoltrackerbot-production.up.railway.app`) wird beim Start als Webhook hinterlegt.

4. Unterstützt `/start`-Befehl im Chat.

## Lokaler Start:
```bash
uvicorn main:app --host 0.0.0.0 --port 8080
```