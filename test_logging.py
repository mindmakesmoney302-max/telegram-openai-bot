import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s: %(message)s')

print("✅ Logging test started")

try:
    import bot  # change this to your bot file if it has a different name
except Exception as e:
    print("⚠️ Error while importing bot:", e)
